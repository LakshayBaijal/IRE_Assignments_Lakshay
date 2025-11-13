#!/usr/bin/env python3
"""
evaluate_submit.py

Usage:
    python3 evaluate_submit.py --base-url http://localhost:3000 \
        --db crawl.db --refresh-k 10 --submit-interval 14

What it does:
1. Loads pages (page_id, node_id, out_links) from crawl.db
2. Builds a directed edge list and computes PageRank (power iteration)
3. Optionally refreshes the top-K pages (by PageRank) to get fresh node_ids (this costs visits)
4. Submits /evaluate payloads repeatedly inside a 60-second window:
   - first submission as soon as possible (within ~1s)
   - subsequent submissions at intervals <= submit_interval (default: 14s)
   - stops after 60 seconds from first visit
5. Saves responses to evaluation_log.json and prints summary
"""
import sqlite3
import json
import time
import argparse
import requests
import numpy as np
from urllib.parse import urljoin

# -------------------------
# PageRank helper
# -------------------------
def compute_pagerank_from_edges(edges, d=0.85, max_iter=200, tol=1e-6):
    nodes = sorted(set([src for src, _ in edges] + [dst for _, dst in edges]))
    if not nodes:
        return {}
    N = len(nodes)
    node_index = {n: i for i, n in enumerate(nodes)}

    M = np.zeros((N, N), dtype=float)
    for src, dst in edges:
        if src in node_index and dst in node_index:
            i, j = node_index[dst], node_index[src]
            M[i, j] = 1.0

    # Normalize columns (column-stochastic)
    for j in range(N):
        col_sum = np.sum(M[:, j])
        if col_sum > 0:
            M[:, j] /= col_sum
        else:
            M[:, j] = 1.0 / N  # dangling node fix

    v = np.ones(N) / N
    for iteration in range(max_iter):
        v_new = d * (M @ v) + (1 - d) / N
        if np.linalg.norm(v_new - v, 1) < tol:
            break
        v = v_new

    pagerank = {node: float(score) for node, score in zip(nodes, v)}
    return pagerank

# -------------------------
# DB helpers
# -------------------------
def load_pages_from_db(db_path="crawl.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT page_id, node_id, updated_at, out_links FROM pages")
    rows = cursor.fetchall()
    conn.close()
    pages = {}
    for page_id, node_id, updated_at, out_links in rows:
        try:
            out_list = json.loads(out_links) if out_links else []
        except Exception:
            out_list = []
        pages[page_id] = {
            "page_id": page_id,
            "node_id": node_id,
            "updated_at": int(updated_at) if updated_at else int(time.time()),
            "out_links": out_list
        }
    return pages

def edges_from_pages(pages):
    edges = []
    for src, meta in pages.items():
        for dst in meta.get("out_links", []):
            edges.append((src, dst))
    return edges

# -------------------------
# Refresh top-K pages (optional)
# -------------------------
def refresh_top_k(base_url, top_pages, session, db_conn_path="crawl.db", timeout=3):
    """Fetch the pages in top_pages and update crawl.db with their node_ids.
       Returns number of successful refreshes and updated pages dict fragment.
    """
    updated = {}
    visits = 0
    for pid in top_pages:
        visits += 1
        try:
            r = session.get(urljoin(base_url, f"/{pid}"), timeout=timeout)
            if r.status_code != 200:
                continue
            text = r.text
            # Attempt to parse node_id from page body
            # This is consistent with crawler.fetch_page which used: soup.select_one("span.node-id b")
            # We will do a loose parse to extract 'node-id' text pattern
            # fallback: simple substring search
            node_id = None
            # look for 'node-id' or 'Node ID' patterns
            start = text.find("node-id")
            if start == -1:
                # try 'Node ID' or 'Node Id' etc.
                start = text.lower().find("node id")
            if start != -1:
                # crude extraction: take next 200 chars and find quotes / tags
                snippet = text[start:start+200]
                # look for patterns like <b>abc</b> or >abc<
                import re
                m = re.search(r'([A-Za-z0-9_\-]{6,})', snippet)
                if m:
                    node_id = m.group(1)
            # fallback to full-text numeric/alpha token search
            if not node_id:
                import re
                m_all = re.findall(r'[A-Za-z0-9_\-]{6,}', text)
                if m_all:
                    node_id = m_all[0]

            if node_id:
                updated[pid] = node_id
                # update sqlite DB
                try:
                    conn = sqlite3.connect(db_conn_path)
                    conn.execute("UPDATE pages SET node_id = ? WHERE page_id = ?", (node_id, pid))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
        except Exception:
            continue
    return visits, updated

# -------------------------
# Build evaluation payload
# -------------------------
def build_evaluation_entries(pages, pagerank_scores, limit=None):
    """Return list of dicts: {page_id, latest_node_id, score}
       If limit is provided, only include up to limit entries (useful if server restricts).
    """
    entries = []
    for pid, meta in pages.items():
        score = float(pagerank_scores.get(pid, 0.0))
        entries.append({
            "page_id": pid,
            "latest_node_id": meta.get("node_id", "unknown"),
            "score": score
        })
    # sort by score desc (not necessary, but stable)
    entries = sorted(entries, key=lambda x: x["score"], reverse=True)
    if limit:
        entries = entries[:limit]
    return entries

# -------------------------
# Main evaluation loop
# -------------------------
def run_evaluation_loop(base_url, db_path="crawl.db", refresh_k=10, submit_interval=14, max_entries=None):
    session = requests.Session()
    pages = load_pages_from_db(db_path)
    if not pages:
        print("⚠️ No pages in DB. Run crawler.py first to populate crawl.db")
        return
    edges = edges_from_pages(pages)
    pagerank = compute_pagerank_from_edges(edges)

    # Choose top K pages by pagerank to refresh node_ids (to reduce staleness while saving visits)
    sorted_pages = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
    top_pages = [p for p, _ in sorted_pages[:refresh_k]]

    print(f"Total pages loaded from DB: {len(pages)}")
    print(f"Total edges: {len(edges)}")
    print(f"Top-{len(top_pages)} pages chosen for refresh: {top_pages}")

    # Timeline: start timer at first visit (we simulate first visit by counting this script as 'starting visit')
    first_visit_time = time.time()
    window_seconds = 60.0
    evaluation_log = []
    total_visits = 0

    # We'll perform refreshes before each submission to keep node_ids fresh for top pages.
    # Loop until window_seconds elapsed.
    next_submit_offset = 1.0  # do the first submit ~1s after start to ensure 'within 15s'
    submit_times = []
    t = 0
    while t < window_seconds:
        submit_times.append(round(t + next_submit_offset, 3))
        t = submit_times[-1]
        next_submit_offset = submit_interval  # subsequent intervals

    # But enforce the last submit to be <= 60s (the loop above already does)
    # Now perform timed loop
    for offset in submit_times:
        target_time = first_visit_time + offset
        now = time.time()
        sleep_time = target_time - now
        if sleep_time > 0:
            time.sleep(sleep_time)

        # Refresh top pages before each submission (this will add to visit_count)
        visits, updated_nodes = refresh_top_k(base_url, top_pages, session, db_conn_path=db_path)
        total_visits += visits
        if updated_nodes:
            # update our pages dict with refreshed node_ids
            for pid, nid in updated_nodes.items():
                if pid in pages:
                    pages[pid]['node_id'] = nid

        # build entries and submit
        entries = build_evaluation_entries(pages, pagerank, limit=max_entries)
        payload = {"entries": entries}
        eval_url = urljoin(base_url, "/evaluate")
        try:
            resp = session.post(eval_url, json=payload, timeout=6)
            status = resp.status_code
            resp_json = resp.json() if resp.text else {}
        except Exception as e:
            status = None
            resp_json = {"error": str(e)}
        elapsed = time.time() - first_visit_time

        log_item = {
            "seconds_into_window": round(elapsed, 3),
            "entries_sent": len(entries),
            "visit_count_increment": visits,
            "total_visit_count": total_visits,
            "status_code": status,
            "response": resp_json
        }
        print(f"[t={round(elapsed,2)}s] Submitted {len(entries)} entries, visits +{visits}, status={status}")
        if resp_json:
            print(" -> resp keys:", ", ".join(list(resp_json.keys())))
        evaluation_log.append(log_item)

        # Stop if we've passed 60s
        if elapsed >= window_seconds - 0.001:
            break

    # Save logfile
    fname = "evaluation_log.json"
    with open(fname, "w") as f:
        json.dump({
            "first_visit_time": first_visit_time,
            "log": evaluation_log
        }, f, indent=2)
    print(f"\n✅ Evaluation loop finished. Log saved to {fname}")
    print("Summary of submissions:")
    for item in evaluation_log:
        print(f" - t={item['seconds_into_window']}s: entries={item['entries_sent']} visits+={item['visit_count_increment']} status={item['status_code']}")

# -------------------------
# CLI
# -------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Submit /evaluate payloads for the crawling assignment")
    parser.add_argument("--base-url", required=True, help="Base URL (e.g., http://localhost:3000)")
    parser.add_argument("--db", default="crawl.db", help="SQLite DB path (default: crawl.db)")
    parser.add_argument("--refresh-k", type=int, default=10, help="Top-K pages to refresh before each submission")
    parser.add_argument("--submit-interval", type=float, default=14.0, help="Interval (seconds) between subsequent submissions (<=15s). Default 14s.")
    parser.add_argument("--max-entries", type=int, default=None, help="Limit number of entries per submission (None = all pages)")
    args = parser.parse_args()

    if args.submit_interval > 15.0:
        print("⚠️ submit_interval should be <= 15. Setting to 15.")
        args.submit_interval = 15.0

    run_evaluation_loop(args.base_url, db_path=args.db, refresh_k=args.refresh_k, submit_interval=args.submit_interval, max_entries=args.max_entries)
