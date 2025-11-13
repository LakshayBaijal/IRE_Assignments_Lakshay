#!/usr/bin/env python3
"""
evaluate_submit_refresh.py

Improved evaluation submitter that:
 - loads pagerank.csv and crawl.db
 - refreshes top-K pages to retrieve fresh node_ids before each /evaluate submit
 - updates crawl.db with refreshed node_ids
 - builds payload entries with page_id, latest_node_id, score
 - sends submissions every submit_interval seconds for 60s total
 - logs responses to evaluation_log.json

Usage:
  python3 evaluate_submit_refresh.py --base-url http://localhost:3000 --db crawl.db --refresh-k 12 --submit-interval 14 --max-entries 50

Notes:
 - Make sure pagerank.csv exists (run python3 pagerank.py first).
 - Adjust --refresh-k to trade off fewer visits vs fresher node ids.
"""
import argparse
import json
import sqlite3
import time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

# -------------------------
# Helpers
# -------------------------
def load_pagerank(csv_path="pagerank.csv"):
    try:
        df = pd.read_csv(csv_path)
        return dict(zip(df["page_id"].astype(str), df["pagerank"].astype(float)))
    except Exception as e:
        print(f"⚠️ Could not load pagerank.csv: {e}")
        return {}

def load_pages_from_db(db_path="crawl.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT page_id, node_id, updated_at, out_links FROM pages")
    rows = cursor.fetchall()
    conn.close()
    pages = {}
    for page_id, node_id, updated_at, out_links in rows:
        pages[str(page_id)] = {
            "page_id": str(page_id),
            "node_id": (node_id if node_id is not None else "unknown"),
            "updated_at": int(updated_at) if updated_at else int(time.time()),
            "out_links": json.loads(out_links) if out_links else []
        }
    return pages

def update_node_in_db(db_path, page_id, node_id):
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE pages SET node_id = ? WHERE page_id = ?", (node_id, page_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print("DB update error:", e)

def fetch_node_for_page(base_url, page_id, session, timeout=4):
    """Fetch the page and try to extract a node id. Returns node_id or None."""
    # Server variant here uses '/page_<id>' paths (your working server)
    # try several likely URL patterns
    candidates = [f"/{page_id}", f"/page/{page_id}", f"/{page_id}/", f"/page/{page_id}/"]
    last_text = ""
    for p in candidates:
        url = urljoin(base_url, p)
        try:
            r = session.get(url, timeout=timeout)
        except Exception:
            continue
        if r.status_code != 200:
            continue
        last_text = r.text
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        # Look for patterns like "Node ID: abc123" or <span class="node-id"><b>abc</b></span>
        m_node = re.search(r"Node ID[:\s]*([A-Za-z0-9_\-]{6,})", text, re.I)
        if m_node:
            return m_node.group(1)
        node_tag = soup.select_one("span.node-id b")
        if node_tag and node_tag.text.strip():
            return node_tag.text.strip()
        # fallback token search: long alnum token not starting with page_
        tokens = re.findall(r"[A-Za-z0-9_\-]{6,}", text)
        for t in tokens:
            if not t.startswith("page_"):
                return t
    return None

# -------------------------
# Core
# -------------------------
def build_entries(pages, pagerank_scores, max_entries=None):
    entries = []
    for pid, meta in pages.items():
        nid = meta.get("node_id", "unknown")
        # only include pages with some node id
        if not nid or nid == "unknown" or str(nid).strip() == "":
            continue
        score = float(pagerank_scores.get(pid, 0.0))
        entries.append({"page_id": pid, "latest_node_id": nid, "score": score})
    # sort by score descending (optional)
    entries = sorted(entries, key=lambda e: e["score"], reverse=True)
    if max_entries:
        entries = entries[:max_entries]
    return entries

def refresh_top_k(base_url, top_pages, session, db_path="crawl.db"):
    visits = 0
    updated = {}
    for pid in top_pages:
        visits += 1
        nid = fetch_node_for_page(base_url, pid, session)
        if nid:
            updated[pid] = nid
            update_node_in_db(db_path, pid, nid)
    return visits, updated

def run(base_url, db_path="crawl.db", refresh_k=10, submit_interval=14, max_entries=None):
    session = requests.Session()
    pagerank_scores = load_pagerank("pagerank.csv")
    pages = load_pages_from_db(db_path)
    if not pages:
        print("❗ No pages in DB, run crawler.py first.")
        return

    # Build edges/pagerank sanity (optional)
    print(f"Total pages from DB: {len(pages)}")
    # choose top-k pages by pagerank for refreshing; fallback to top pages by presence
    sorted_pr = sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True)
    top_pages = [p for p, _ in sorted_pr[:refresh_k]] if sorted_pr else list(pages.keys())[:refresh_k]
    print(f"Top-{len(top_pages)} pages chosen for refresh: {top_pages}")

    first_visit_time = time.time()
    evaluation_log = []
    total_visits = 0

    # schedule submit times: first ~1s, then every submit_interval until 60s window is reached
    submit_times = []
    t = 1.0
    while t <= 60.0:
        submit_times.append(t)
        t += submit_interval

    for offset in submit_times:
        target = first_visit_time + offset
        now = time.time()
        to_sleep = target - now
        if to_sleep > 0:
            time.sleep(to_sleep)

        # refresh top K pages to obtain fresh node_ids
        visits, updated = refresh_top_k(base_url, top_pages, session, db_path=db_path)
        total_visits += visits
        # reload pages after refresh
        pages = load_pages_from_db(db_path)

        entries = build_entries(pages, pagerank_scores, max_entries=max_entries)
        payload = {"entries": entries}
        # DEBUG: print a small preview of payload
        print(f"[t={round(time.time()-first_visit_time,3)}s] Submitting {len(entries)} entries, visits +{visits}")

        try:
            resp = session.post(urljoin(base_url, "/evaluate"), json=payload, timeout=8)
            status = resp.status_code
            resp_json = resp.json() if resp.text else {}
        except Exception as e:
            status = None
            resp_json = {"error": str(e)}

        log_item = {
            "seconds_into_window": round(time.time() - first_visit_time, 3),
            "entries_sent": len(entries),
            "visit_count_increment": visits,
            "total_visit_count": total_visits,
            "status_code": status,
            "response": resp_json
        }
        print(" -> status:", status, " resp keys:", list(resp_json.keys()) if isinstance(resp_json, dict) else resp_json)
        evaluation_log.append(log_item)

        # stop if window exceeded
        if time.time() - first_visit_time >= 60.0:
            break

    with open("evaluation_log.json", "w") as f:
        json.dump({"first_visit_time": first_visit_time, "log": evaluation_log}, f, indent=2)
    print("✅ Finished. Log saved to evaluation_log.json")

# -------------------------
# CLI
# -------------------------
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", required=True)
    p.add_argument("--db", default="crawl.db")
    p.add_argument("--refresh-k", type=int, default=10)
    p.add_argument("--submit-interval", type=float, default=14.0)
    p.add_argument("--max-entries", type=int, default=None)
    args = p.parse_args()
    run(args.base_url, db_path=args.db, refresh_k=args.refresh_k, submit_interval=args.submit_interval, max_entries=args.max_entries)
