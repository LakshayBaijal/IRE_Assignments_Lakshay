#!/usr/bin/env python3
"""
dedup_final_lsh.py

MinHash + LSH based deduplication pipeline (designed for dedup_data.csv ~5k rows).

Outputs:
  - groups.json            : list of groups (each group is list of original ids)
  - dedup_mapping.csv      : original_id -> group_id
  - dedup_diagnostics.json : clustering diagnostics (counts, avg sim, timings)

Usage:
  python3 dedup_final_lsh.py --input dedup_data.csv \
      --threshold 0.72 --k 2 --num-perm 128 --use-fuzzy

Notes:
 - Requires: datasketch, pandas, networkx, fuzzywuzzy (python-Levenshtein recommended)
   Install inside venv: pip install datasketch pandas networkx fuzzywuzzy python-Levenshtein
"""

import argparse
import json
import csv
import time
import random
import math
from collections import defaultdict

# external libs
try:
    import pandas as pd
except Exception as e:
    raise RuntimeError("pandas required. Install with `pip install pandas`") from e

try:
    from datasketch import MinHash, MinHashLSH
except Exception as e:
    raise RuntimeError("datasketch required. Install with `pip install datasketch`") from e

try:
    import networkx as nx
except Exception as e:
    raise RuntimeError("networkx required. Install with `pip install networkx`") from e

# fuzzy optional (used as secondary check)
USE_FUZZY_BY_DEFAULT = True
try:
    from fuzzywuzzy.fuzz import token_set_ratio
    HAVE_FUZZY = True
except Exception:
    HAVE_FUZZY = False
    USE_FUZZY_BY_DEFAULT = False

# -------------------------
# Normalization & shingling
# -------------------------
def normalize(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().lower()
    # keep alnum and spaces
    out = []
    for ch in s:
        if ch.isalnum() or ch.isspace():
            out.append(ch)
        else:
            out.append(' ')
    return " ".join("".join(out).split())

def build_shingles(text: str, k: int = 2):
    t = normalize(text)
    if len(t) == 0:
        return []
    # optionally pad? keep simple
    s = t.replace(" ", "_")
    shingles = [s[i:i+k] for i in range(max(1, len(s) - k + 1))]
    return shingles

# -------------------------
# Combine record fields
# -------------------------
def combine_fields(row, include_fields=None):
    if include_fields is None:
        include_fields = [
            "given_name", "surname", "street_number", "address_1",
            "address_2", "suburb", "postcode", "state",
            "date_of_birth", "soc_sec_id"
        ]
    parts = []
    for f in include_fields:
        parts.append(str(row.get(f, "") if f in row else ""))
    return normalize(" ".join(parts))

# -------------------------
# MinHash helpers
# -------------------------
def build_minhash_from_shingles(shingles, num_perm=128):
    mh = MinHash(num_perm=num_perm)
    # handle empty
    if not shingles:
        mh.update("".encode('utf8'))
        return mh
    for sh in shingles:
        mh.update(sh.encode('utf8'))
    return mh

# -------------------------
# Similarity check helpers
# -------------------------
def fuzzy_sim(a: str, b: str):
    if not HAVE_FUZZY:
        # fallback to simple token overlap
        sa = set(a.split())
        sb = set(b.split())
        if not sa and not sb: return 1.0
        inter = sa.intersection(sb)
        return (2.0 * len(inter) / (len(sa) + len(sb))) if (len(sa) + len(sb))>0 else 0.0
    else:
        return token_set_ratio(a, b) / 100.0

# -------------------------
# Main dedup pipeline
# -------------------------
def dedup_lsh(
    input_csv,
    threshold=0.72,
    k=2,
    num_perm=128,
    use_fuzzy=True,
    include_fields=None,
    max_candidates_per_row=1000,
    sample_intra_groups=200,
    sample_pairs_per_group=100
):
    t0 = time.time()

    df = pd.read_csv(input_csv, dtype=str).fillna("")
    n = len(df)
    print(f"Loaded: {n} records from {input_csv}")

    # build text representations
    combined_texts = []
    for i, row in df.iterrows():
        combined_texts.append(combine_fields(row, include_fields))

    # Build MinHash signatures & insert into LSH
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    minhashes = {}
    for idx, txt in enumerate(combined_texts):
        shingles = build_shingles(txt, k=k)
        mh = build_minhash_from_shingles(shingles, num_perm=num_perm)
        minhashes[idx] = mh
        # use string key in LSH
        lsh.insert(str(idx), mh)

    # Build similarity graph
    G = nx.Graph()
    G.add_nodes_from(range(n))

    # For each record query candidates and verify with fuzzy token-set or exact threshold
    checked_pairs = 0
    merged_pairs = 0
    for idx in range(n):
        try:
            cand_keys = lsh.query(minhashes[idx])
        except Exception:
            cand_keys = []
        # convert to int and dedupe
        cand_idxs = []
        for kstr in cand_keys:
            try:
                j = int(kstr)
                if j != idx:
                    cand_idxs.append(j)
            except:
                pass
        # limit candidates to avoid explosion
        if len(cand_idxs) > max_candidates_per_row:
            cand_idxs = cand_idxs[:max_candidates_per_row]

        for j in cand_idxs:
            # to avoid duplicate checks, only check j > idx
            if j <= idx:
                continue
            checked_pairs += 1
            a = combined_texts[idx]
            b = combined_texts[j]
            # primary criterion: fuzzy similarity if enabled, else accept candidate
            sim = fuzzy_sim(a, b) if use_fuzzy else 1.0
            if sim >= threshold:
                G.add_edge(idx, j)
                merged_pairs += 1
            else:
                # if fuzzy didn't pass, optionally check Jaccard estimate from MinHash (approx)
                # use MinHash.jaccard to estimate if available
                try:
                    est = minhashes[idx].jaccard(minhashes[j])
                except Exception:
                    est = 0.0
                # be permissive: if estimated Jaccard is high enough, connect
                if est >= threshold:
                    G.add_edge(idx, j)
                    merged_pairs += 1

    # connected components -> groups
    comps = list(nx.connected_components(G))
    comps_sorted = sorted(comps, key=lambda s: -len(s))
    num_groups = len(comps_sorted)
    num_singletons = sum(1 for c in comps_sorted if len(c) == 1)
    num_multis = num_groups - num_singletons
    records_in_multis = sum(len(c) for c in comps_sorted if len(c) > 1)

    # Build outputs: groups in terms of original IDs
    groups_out = []
    for comp in comps_sorted:
        group_ids = [df.iloc[i]["id"] if "id" in df.columns else str(i) for i in sorted(comp)]
        groups_out.append(group_ids)

    # mapping original id -> group_id (1-indexed)
    mapping = {}
    for gid, comp in enumerate(comps_sorted, start=1):
        for i in comp:
            orig_id = df.iloc[i]["id"] if "id" in df.columns else str(i)
            mapping[orig_id] = gid

    # diagnostics: intra-cluster similarity (sampled), inter-cluster similarity (sampled)
    intra_vals = []
    sampled_groups = [c for c in comps_sorted if len(c) > 1][:sample_intra_groups]
    for comp in sampled_groups:
        comp_list = list(comp)
        # sample pairs limited
        pairs = []
        for a_i in range(len(comp_list)):
            for b_i in range(a_i+1, len(comp_list)):
                pairs.append((comp_list[a_i], comp_list[b_i]))
        if not pairs:
            continue
        if len(pairs) > sample_pairs_per_group:
            pairs = random.sample(pairs, sample_pairs_per_group)
        for (ia, ib) in pairs:
            intra_vals.append(fuzzy_sim(combined_texts[ia], combined_texts[ib]))
    avg_intra = (sum(intra_vals) / len(intra_vals)) if intra_vals else 0.0

    # inter-cluster: sample random pairs across different clusters (singleton vs others)
    inter_vals = []
    # build a flat list of some items from different groups
    if len(comps_sorted) > 1:
        # pick random groups
        groups_for_inter = random.sample(comps_sorted, min(100, len(comps_sorted)))
        # pick one element per group and compute pairwise
        elems = []
        for g in groups_for_inter:
            elems.append(next(iter(g)))
        for i in range(len(elems)):
            for j in range(i+1, len(elems)):
                inter_vals.append(fuzzy_sim(combined_texts[elems[i]], combined_texts[elems[j]]))
    avg_inter = (sum(inter_vals) / len(inter_vals)) if inter_vals else 0.0

    t1 = time.time()
    elapsed = t1 - t0

    diagnostics = {
        "num_records": n,
        "num_groups": num_groups,
        "num_singletons": num_singletons,
        "num_multis": num_multis,
        "records_in_multis": records_in_multis,
        "pairs_checked": checked_pairs,
        "pairs_merged": merged_pairs,
        "avg_intra_similarity": avg_intra,
        "avg_inter_similarity": avg_inter,
        "elapsed_seconds": elapsed,
        "parameters": {
            "threshold": threshold,
            "k": k,
            "num_perm": num_perm,
            "use_fuzzy": use_fuzzy
        }
    }

    # save outputs
    with open("groups.json", "w", encoding="utf-8") as f:
        json.dump(groups_out, f, indent=2)

    with open("dedup_mapping.csv", "w", newline='', encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["original_id", "group_id"])
        for orig_id, gid in mapping.items():
            w.writerow([orig_id, gid])

    with open("dedup_diagnostics.json", "w", encoding="utf-8") as f:
        json.dump(diagnostics, f, indent=2)

    # print summary
    print(f"Groups: {num_groups}  multi: {num_multis}  single: {num_singletons}")
    print(f"Records in multi-record groups: {records_in_multis}")
    print(f"Pairs checked: {checked_pairs}  Pairs merged: {merged_pairs}")
    print(f"Avg intra-sim (sampled): {avg_intra:.3f}  Avg inter-sim (sampled): {avg_inter:.3f}")
    print(f"Elapsed: {elapsed:.2f}s")
    print("Wrote: groups.json, dedup_mapping.csv, dedup_diagnostics.json")

    return diagnostics, groups_out, mapping

# -------------------------
# CLI
# -------------------------
def parse_args():
    ap = argparse.ArgumentParser(description="Deduplication via MinHash-LSH")
    ap.add_argument("--input", required=True, help="input CSV path (dedup_data.csv)")
    ap.add_argument("--threshold", type=float, default=0.72, help="similarity threshold (0..1)")
    ap.add_argument("--k", type=int, default=2, help="shingle size (chars)")
    ap.add_argument("--num-perm", type=int, default=128, help="MinHash permutations")
    ap.add_argument("--use-fuzzy", type=bool, default=USE_FUZZY_BY_DEFAULT, help="use fuzzy token_set re-check (if fuzzywuzzy installed)")
    ap.add_argument("--max-candidates", type=int, default=1000, help="cap candidates per row from LSH query")
    return ap.parse_args()

if __name__ == "__main__":
    args = parse_args()
    diag, groups, mapping = dedup_lsh(
        input_csv=args.input,
        threshold=args.threshold,
        k=args.k,
        num_perm=args.num_perm,
        use_fuzzy=args.use_fuzzy,
        max_candidates_per_row=args.max_candidates
    )
