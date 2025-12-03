#!/usr/bin/env python3
"""
dedup_final_improved.py

Improved deduplication pipeline implementing Grok feedback:
 - includes street_number + address_2 in address field
 - optional phonetic matching via jellyfish (if installed)
 - DOB fuzzy (exact -> 1.0, within 365 days -> 0.8)
 - SSN fuzzy handling (normalized digits + fuzzy check)
 - blocking + DSU clustering, cap huge blocks (log skipped)
 - intra-cluster & inter-cluster diagnostics for self-eval

Usage:
  pip install rapidfuzz jellyfish   # optional (faster / phonetic)
  python3 dedup_final_improved.py --input dedup_data.csv --threshold 0.78
"""

import csv
import json
import re
import time
import argparse
import random
from collections import defaultdict
from datetime import datetime

# try imports
try:
    from rapidfuzz import fuzz
    HAVE_RAPIDFUZZ = True
except Exception:
    HAVE_RAPIDFUZZ = False

try:
    import jellyfish
    HAVE_JELLYFISH = True
except Exception:
    HAVE_JELLYFISH = False

# fallback token_set_ratio & ratio implementations
def token_set_ratio_fallback(a, b):
    # simple token-set overlap proportion fallback
    ta = set(a.split())
    tb = set(b.split())
    if not ta and not tb:
        return 1.0
    inter = ta.intersection(tb)
    if not inter:
        return 0.0
    overlap_prop = (2 * len(inter)) / (len(ta) + len(tb))
    return overlap_prop

def ratio_fallback(a,b):
    # simple ratio fallback
    from difflib import SequenceMatcher
    if not a and not b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()

# wrapper functions
if HAVE_RAPIDFUZZ:
    def token_set_ratio(a,b):
        try:
            return (fuzz.token_set_ratio(a or "", b or "") or 0) / 100.0
        except Exception:
            return token_set_ratio_fallback(a,b)
    def simple_ratio(a,b):
        try:
            return (fuzz.ratio(a or "", b or "") or 0) / 100.0
        except Exception:
            return ratio_fallback(a,b)
else:
    token_set_ratio = token_set_ratio_fallback
    simple_ratio = ratio_fallback

# phonetic helper
def phonetic_sim(a, b):
    """Return phonetic similarity [0..1]. Prefer jellyfish.jaro_winkler on soundex codes if available."""
    if not a and not b:
        return 1.0
    if HAVE_JELLYFISH:
        try:
            # compute soundex of surnames or full name tokens
            sa = jellyfish.soundex(a.split()[-1]) if a.strip() else ""
            sb = jellyfish.soundex(b.split()[-1]) if b.strip() else ""
            if sa and sb and sa == sb:
                return 1.0
            # fallback to jaro_winkler on whole names
            jw = jellyfish.jaro_winkler_similarity(a or "", b or "") / 100.0 if hasattr(jellyfish, "jaro_winkler_similarity") else 0.0
            return max(jw, token_set_ratio(a,b))
        except Exception:
            return token_set_ratio(a,b)
    else:
        # fallback: use token_set_ratio as proxy
        return token_set_ratio(a,b)

# ------------------------
# DSU (Union-Find)
# ------------------------
class DSU:
    def __init__(self):
        self.parent = {}
    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra

# ------------------------
# Normalisation helpers
# ------------------------
def norm_text(s):
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s

def norm_ssn(s):
    if s is None:
        return ""
    return re.sub(r'\D', '', str(s))

def parse_date_try(s):
    if not s:
        return None
    s = s.strip()
    fmts = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%m/%d/%Y"]
    for f in fmts:
        try:
            return datetime.strptime(s, f)
        except Exception:
            pass
    # try year-only or other noisy patterns
    try:
        # e.g., '1987'
        if len(s) == 4 and s.isdigit():
            return datetime.strptime(s, "%Y")
    except:
        pass
    return None

# ------------------------
# Similarity scoring (enhanced)
# ------------------------
def record_similarity(r1, r2, dob_tol_days=365, ssn_lev_threshold=0.9):
    """
    Weighted similarity combining:
      - name (token_set + phonetic)
      - address (street_number + address_1 + address_2 + suburb)
      - DOB fuzzy (exact ->1.0, within tol ->0.8)
      - SSN (exact ->1.0; fuzzy ->1.0 if similar above threshold)
    Returns float in 0..1
    """
    # weights (tunable)
    w_name = 0.4
    w_addr = 0.4
    w_dob  = 0.1
    w_ssn  = 0.1

    # name
    name1 = ((r1.get('given_name','') or "") + " " + (r1.get('surname','') or "")).strip()
    name2 = ((r2.get('given_name','') or "") + " " + (r2.get('surname','') or "")).strip()
    # token set + phonetic combo
    ts_name = token_set_ratio(name1, name2)
    ph_name = phonetic_sim(name1, name2)
    name_score = max(ts_name, ph_name)

    # address combine: include street_number and address_2
    a1_parts = [r1.get('street_number','') or "", r1.get('address_1','') or "", r1.get('address_2','') or "", r1.get('suburb','') or ""]
    a2_parts = [r2.get('street_number','') or "", r2.get('address_1','') or "", r2.get('address_2','') or "", r2.get('suburb','') or ""]
    addr1 = " ".join([p for p in a1_parts if p]).strip()
    addr2 = " ".join([p for p in a2_parts if p]).strip()
    addr1 = norm_text(addr1)
    addr2 = norm_text(addr2)
    addr_score = token_set_ratio(addr1, addr2)

    # DOB fuzzy
    dob1 = parse_date_try(r1.get('date_of_birth','') or "")
    dob2 = parse_date_try(r2.get('date_of_birth','') or "")
    dob_score = 0.0
    if dob1 and dob2:
        if dob1 == dob2:
            dob_score = 1.0
        else:
            diff = abs((dob1 - dob2).days)
            if diff <= dob_tol_days:
                dob_score = 0.8
            else:
                dob_score = 0.0

    # SSN handling
    ss1 = norm_ssn(r1.get('soc_sec_id','') or "")
    ss2 = norm_ssn(r2.get('soc_sec_id','') or "")
    ss_score = 0.0
    if ss1 and ss2:
        if ss1 == ss2:
            ss_score = 1.0
        else:
            # fuzzy: compare normalized digit strings using ratio
            if HAVE_RAPIDFUZZ:
                lev = (fuzz.ratio(ss1, ss2) or 0) / 100.0
            else:
                # fallback: length-aware simple ratio
                lev = simple_ratio(ss1, ss2)
            if lev >= ssn_lev_threshold:
                ss_score = 1.0
            else:
                ss_score = 0.0

    final = w_name * name_score + w_addr * addr_score + w_dob * dob_score + w_ssn * ss_score
    return final

# ------------------------
# Blocking
# ------------------------
def build_blocks(records):
    blocks = defaultdict(list)
    for rec in records:
        s = (rec.get('surname','') or "")[:40]
        p = rec.get('postcode','')
        key1 = f"{s}|{p}"
        blocks[key1].append(rec['idx'])
        key2 = f"{s[:3]}|{p}"
        blocks[key2].append(rec['idx'])
    return blocks

# ------------------------
# Evaluation helpers (intra/inter)
# ------------------------
def avg_pairwise_similarity(group_ids, records, sample_limit_pairs=500):
    # compute average pairwise similarity inside group (use sample if large)
    idxs = [idx for idx,rec in enumerate(records) if rec['id'] in set(group_ids)]
    pairs = []
    n = len(idxs)
    if n < 2:
        return None
    # generate pairs
    for i in range(n):
        for j in range(i+1, n):
            pairs.append((idxs[i], idxs[j]))
    if not pairs:
        return None
    if len(pairs) > sample_limit_pairs:
        pairs = random.sample(pairs, sample_limit_pairs)
    total = 0.0
    count = 0
    for a,b in pairs:
        s = record_similarity(records[a], records[b])
        total += s; count += 1
    return (total / count) if count else None

def avg_intercluster_similarity(group_list, records, sample_pairs=1000):
    # sample random pairs across different clusters
    if len(group_list) < 2:
        return None
    pairs = []
    # build flat list of cluster ids (choose from multi groups)
    flat = []
    for g in group_list:
        if len(g) >= 1:
            flat.extend(g)
    if len(flat) < 2:
        return None
    # sample cross-group pairs
    for _ in range(sample_pairs):
        a = random.choice(flat)
        b = random.choice(flat)
        if a == b:
            continue
        # ensure they come from different groups
        # cheap test: skip if a and b in same group (linear search ok for sample)
        same = False
        for g in group_list:
            if a in g and b in g:
                same = True; break
        if same:
            continue
        pairs.append((a,b))
    if not pairs:
        return None
    # compute sim
    total = 0.0; count = 0
    id_to_rec = {rec['id']: rec for rec in records}
    for a,b in pairs:
        ra = id_to_rec.get(a); rb = id_to_rec.get(b)
        if not ra or not rb:
            continue
        total += record_similarity(ra, rb)
        count += 1
    return (total / count) if count else None

# ------------------------
# Main pipeline
# ------------------------
def dedup_pipeline(input_csv, threshold=0.78, sample_limit=None,
                   ssn_lev_threshold=0.9, dob_tol_days=365, max_block_members=2000,
                   out_groups='groups.json', out_map='dedup_mapping.csv'):
    start = time.time()
    # read CSV
    rows = []
    with open(input_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    if sample_limit:
        rows = rows[:sample_limit]
    N = len(rows)

    # normalize and prepare records
    records = []
    for i, r in enumerate(rows):
        rec = {
            "idx": i,
            "id": r.get("id") or r.get("Id") or r.get("ID") or str(i),
            "given_name": norm_text(r.get("given_name","")),
            "surname": norm_text(r.get("surname","")),
            "street_number": norm_text(r.get("street_number","")) if 'street_number' in r else norm_text(""),
            "address_1": norm_text(r.get("address_1","")),
            "address_2": norm_text(r.get("address_2","")) if 'address_2' in r else "",
            "suburb": norm_text(r.get("suburb","")),
            "postcode": str(r.get("postcode","")).strip(),
            "date_of_birth": (r.get("date_of_birth") or "").strip(),
            "soc_sec_id": norm_ssn(r.get("soc_sec_id",""))
        }
        records.append(rec)

    # build blocks
    blocks = build_blocks(records)

    dsu = DSU()
    pairs_checked = 0
    pairs_merged = 0
    skipped_from_blocks = 0

    for key, members in blocks.items():
        m = len(members)
        if m <= 1:
            continue
        # cap huge blocks
        if m > max_block_members:
            skipped = m - max_block_members
            skipped_from_blocks += skipped
            members = members[:max_block_members]
            print(f"[WARN] Block {key} too large ({m}); truncated by {skipped} members")
        # compare pairs within block
        for i in range(len(members)):
            for j in range(i+1, len(members)):
                ai = members[i]
                bj = members[j]
                pairs_checked += 1
                r1 = records[ai]; r2 = records[bj]

                # SSN exact or fuzzy quick path
                ss1 = r1['soc_sec_id']; ss2 = r2['soc_sec_id']
                if ss1 and ss2:
                    if ss1 == ss2:
                        dsu.union(ai, bj); pairs_merged += 1
                        continue
                    else:
                        # fuzzy SSN check (lev)
                        if HAVE_RAPIDFUZZ:
                            lev = (fuzz.ratio(ss1, ss2) or 0) / 100.0
                        else:
                            lev = simple_ratio(ss1, ss2)
                        if lev >= ssn_lev_threshold:
                            dsu.union(ai, bj); pairs_merged += 1
                            continue

                # compute similarity
                score = record_similarity(r1, r2, dob_tol_days=dob_tol_days, ssn_lev_threshold=ssn_lev_threshold)
                if score >= threshold:
                    dsu.union(ai, bj); pairs_merged += 1

    # build groups mapping
    groups = defaultdict(list)
    for rec in records:
        root = dsu.find(rec['idx'])
        groups[root].append(rec['id'])
    group_list = [g for g in groups.values() if g]
    group_list.sort(key=lambda x: -len(x))

    # write outputs
    with open(out_groups, 'w', encoding='utf-8') as f:
        json.dump(group_list, f, indent=2)
    with open(out_map, 'w', newline='', encoding='utf-8') as f:
        import csv as _csv
        writer = _csv.writer(f)
        writer.writerow(['original_id','group_id'])
        for gid, group in enumerate(group_list, start=1):
            for rid in group:
                writer.writerow([rid, gid])

    elapsed = time.time() - start

    # compute diagnostics: singletons, multi, sizes
    sizes = sorted([len(g) for g in group_list], reverse=True)
    num_groups = len(group_list)
    num_singletons = sum(1 for s in sizes if s==1)
    num_multis = num_groups - num_singletons
    records_in_multis = sum(s for s in sizes if s>1)

    # intra-cluster avg similarity (sample top K groups or all)
    intra_vals = []
    for g in group_list[:200]:  # limit to 200 groups for speed
        if len(g) < 2:
            continue
        v = avg_pairwise_similarity(g, records)
        if v is not None:
            intra_vals.append(v)
    avg_intra = sum(intra_vals)/len(intra_vals) if intra_vals else None

    # inter-cluster (sample)
    inter_avg = avg_intercluster_similarity(group_list, records, sample_pairs=1000)

    # final diagnostics print
    print("Loaded:", N, "records")
    print("Blocks:", len(blocks))
    print("Skipped (cap) total members:", skipped_from_blocks)
    print("Groups found:", num_groups, " (singletons:", num_singletons, " multi:", num_multis, ")")
    print("Records in multi-record groups:", records_in_multis)
    print("Pairs checked:", pairs_checked, "Pairs merged:", pairs_merged)
    if sizes:
        print("Top group sizes sample:", sizes[:10])
    print("Elapsed: %.2fs" % elapsed)
    if avg_intra is not None:
        print("Avg intra-cluster similarity (sampled groups): %.3f" % avg_intra)
    if inter_avg is not None:
        print("Avg inter-cluster similarity (sampled pairs): %.3f" % inter_avg)

    return {
        "groups": group_list,
        "num_groups": num_groups,
        "num_singletons": num_singletons,
        "num_multis": num_multis,
        "records_in_multis": records_in_multis,
        "pairs_checked": pairs_checked,
        "pairs_merged": pairs_merged,
        "avg_intra_sim": avg_intra,
        "avg_inter_sim": inter_avg,
        "elapsed": elapsed
    }

# ------------------------
# CLI
# ------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Improved Dedup pipeline (Grok feedback)")
    ap.add_argument('--input', default='dedup_data.csv', help='input CSV path')
    ap.add_argument('--threshold', type=float, default=0.78, help='0..1 similarity threshold')
    ap.add_argument('--sample', type=int, default=0, help='limit rows for testing')
    ap.add_argument('--ssn-lev-th', type=float, default=0.9, help='SSN fuzzy threshold')
    ap.add_argument('--dob-tol-days', type=int, default=365, help='DOB fuzz tolerance in days')
    ap.add_argument('--max-block', type=int, default=2000, help='cap block members (avoid O(n^2) too large)')
    ap.add_argument('--out-groups', default='groups.json', help='output groups json')
    ap.add_argument('--out-map', default='dedup_mapping.csv', help='output mapping csv')
    args = ap.parse_args()

    sample = args.sample if args.sample > 0 else None
    result = dedup_pipeline(args.input, threshold=args.threshold, sample_limit=sample,
                            ssn_lev_threshold=args.ssn_lev_th, dob_tol_days=args.dob_tol_days,
                            max_block_members=args.max_block, out_groups=args.out_groups,
                            out_map=args.out_map)
    # save diagnostics summary (for inclusion in report)
    with open('dedup_diagnostics.json','w') as df:
        json.dump({
            "num_groups": result['num_groups'],
            "num_singletons": result['num_singletons'],
            "num_multis": result['num_multis'],
            "records_in_multis": result['records_in_multis'],
            "pairs_checked": result['pairs_checked'],
            "pairs_merged": result['pairs_merged'],
            "avg_intra_sim": result['avg_intra_sim'],
            "avg_inter_sim": result['avg_inter_sim'],
            "elapsed": result['elapsed']
        }, df, indent=2)
    print("Wrote dedup_diagnostics.json")
