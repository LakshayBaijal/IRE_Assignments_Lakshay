#!/usr/bin/env python3
"""
search_sqlite.py

Simple retrieval interface for the IRE assignment sqlite index.
- Auto-detects docs/postings schema fields (tries title/path/etc).
- Builds TF-IDF weights for query and docs (from postings tf = number of positions).
- Ranks by cosine similarity (vector space model).
"""

import sqlite3
import math
import json
import sys
import argparse
import re
from collections import defaultdict, Counter

RE_TOKEN = re.compile(r"[a-z0-9]+")  # simple tokenizer: lowercase alnum tokens

def tokenize(text):
    return RE_TOKEN.findall(text.lower())

def get_table_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info('{table_name}')")
    rows = cursor.fetchall()
    return [r[1] for r in rows]  # r[1] is column name

def choose_doc_display_field(cursor):
    # prefer these fields if present
    prefs = ["title", "doc_title", "path", "name", "url", "filename", "file"]
    cols = get_table_columns(cursor, "docs")
    for p in prefs:
        if p in cols:
            return p
    # fallback: if docs has more than 1 column, pick the second (after doc_id) if exists
    if len(cols) >= 2:
        # assume first is doc_id, second might be path/whatever
        return cols[1]
    return None

def detect_postings_columns(cursor):
    # Try to discover which column index corresponds to doc_id and posting json
    cursor.execute("SELECT * FROM postings LIMIT 1")
    desc = cursor.description
    if not desc:
        # table empty? fallback to defaults
        return {"doc_id_idx": 1, "posting_idx": 2}
    col_names = [d[0] for d in desc]
    # find likely indices
    def find_name(candidates, default=None):
        for cand in candidates:
            if cand in col_names:
                return col_names.index(cand)
        return default
    doc_id_idx = find_name(["doc_id", "docid", "doc"], default=1)
    posting_idx = find_name(["posting", "postings", "posting_json", "value", "positions"], default=len(col_names)-1)
    return {"doc_id_idx": doc_id_idx, "posting_idx": posting_idx}

def compute_tf_idf(tf, df, N):
    # tf: raw term frequency (positive int)
    # df: document frequency (positive int)
    # N: total number of documents (positive int)
    if tf <= 0 or df <= 0:
        return 0.0
    return (1.0 + math.log10(tf)) * math.log10(max(1.0, N / df))

def search(db_path, query, top_k=10):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # total docs
    cursor.execute("SELECT COUNT(*) FROM docs")
    N = cursor.fetchone()[0]
    if N == 0:
        print("Index contains 0 documents.")
        conn.close()
        return

    # choose display field
    display_field = choose_doc_display_field(cursor)

    # detect postings column indexes
    pcols = detect_postings_columns(cursor)
    doc_id_idx = pcols["doc_id_idx"]
    posting_idx = pcols["posting_idx"]

    # process query -> token counts
    q_terms = tokenize(query)
    if not q_terms:
        print("No valid tokens in query.")
        conn.close()
        return
    q_tf_counter = Counter(q_terms)

    # We'll build:
    # - query vector: q_weights[term]
    # - doc_vectors: doc_weights[doc_id][term]
    doc_weights = defaultdict(dict)
    doc_norm_sqr = defaultdict(float)  # sum of squares for doc vectors
    q_weights = {}
    q_norm_sqr = 0.0

    # For each unique term, fetch postings and compute weights
    for term, q_tf in q_tf_counter.items():
        cursor.execute("SELECT * FROM postings WHERE term=?", (term,))
        rows = cursor.fetchall()
        df = len(rows)
        if df == 0:
            # term not in index; skip
            continue

        # query weight for this term (tf in query)
        q_w = compute_tf_idf(q_tf, df, N)
        q_weights[term] = q_w
        q_norm_sqr += q_w * q_w

        # populate doc weights for term
        for row in rows:
            # row is tuple with columns matching postings table
            try:
                doc_id = row[doc_id_idx]
                posting_json = row[posting_idx]
            except Exception:
                # fallback to conventional ordering (term, doc_id, posting_json)
                if len(row) >= 3:
                    doc_id = row[1]
                    posting_json = row[2]
                else:
                    continue
            # posting_json may already be a dict or string
            if isinstance(posting_json, (dict, list)):
                posting = posting_json
            else:
                try:
                    posting = json.loads(posting_json)
                except Exception:
                    # if posting isn't json, try to interpret as simple count
                    posting = {}

            # extract term frequency (prefer "positions" list length)
            tf = 0
            if isinstance(posting, dict):
                if "positions" in posting and isinstance(posting["positions"], list):
                    tf = len(posting["positions"])
                elif "tf" in posting and isinstance(posting["tf"], int):
                    tf = posting["tf"]
                else:
                    # sometimes posting_json might be a plain number in string
                    tf = posting.get("tf", 0) if hasattr(posting, "get") else 0
            elif isinstance(posting, list):
                tf = len(posting)
            else:
                # try to parse digits
                try:
                    tf = int(str(posting))
                except Exception:
                    tf = 0

            if tf <= 0:
                # if we couldn't determine tf from posting, assume tf=1 (document contains term)
                tf = 1

            w = compute_tf_idf(tf, df, N)
            doc_weights[doc_id][term] = w
            doc_norm_sqr[doc_id] += w * w

    if not q_weights:
        print("No query terms were found in the index.")
        conn.close()
        return

    q_norm = math.sqrt(q_norm_sqr) if q_norm_sqr > 0 else 0.0

    # compute cosine similarities
    scores = {}
    for doc_id, term_weights in doc_weights.items():
        dot = 0.0
        for term, dw in term_weights.items():
            qw = q_weights.get(term, 0.0)
            dot += qw * dw
        denom = math.sqrt(doc_norm_sqr.get(doc_id, 0.0)) * q_norm
        score = (dot / denom) if denom > 0 else 0.0
        scores[doc_id] = score

    # fallback: if scores empty (shouldn't happen), we could also rank by sum(tf-idf)
    if not scores:
        print("No candidate documents after scoring.")
        conn.close()
        return

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    # print results
    print(f"\n🔍 Query Results for: {query}")
    print("-" * 80)
    for rank, (doc_id, score) in enumerate(ranked, start=1):
        display = ""
        if display_field:
            try:
                cursor.execute(f"SELECT {display_field} FROM docs WHERE doc_id=?", (doc_id,))
                row = cursor.fetchone()
                display = row[0] if row and len(row) > 0 else None
            except Exception:
                display = None
        if display:
            print(f"{rank}. Doc ID: {doc_id} | Score: {score:.6f} | {display_field}: {display}")
        else:
            print(f"{rank}. Doc ID: {doc_id} | Score: {score:.6f}")
    print("-" * 80)
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Search an sqlite inverted index (IRE assignment).")
    parser.add_argument("db", help="path to sqlite index DB (e.g., wiki_index.db)")
    parser.add_argument("--k", type=int, default=10, help="number of top results to show")
    args = parser.parse_args()

    db_path = args.db
    top_k = args.k

    try:
        while True:
            query = input("\nEnter your query (or type 'exit' to quit): ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit"):
                break
            search(db_path, query, top_k=top_k)
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
