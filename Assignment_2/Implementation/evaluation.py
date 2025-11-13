#!/usr/bin/env python3
import json
import time
import sqlite3
import requests
import pandas as pd
import argparse

def load_pagerank_scores(csv_path="pagerank.csv"):
    """Load PageRank scores into a dictionary {page_id: score}."""
    try:
        df = pd.read_csv(csv_path)
        scores = dict(zip(df["page_id"], df["pagerank"]))
        print(f"✅ Loaded {len(scores)} PageRank scores.")
        return scores
    except Exception as e:
        print(f"⚠️ Could not load pagerank.csv: {e}")
        return {}

def load_latest_nodes(db_path="crawl.db"):
    """Load latest node_ids for each page."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT page_id, node_id FROM pages")
    rows = cursor.fetchall()
    conn.close()
    print(f"✅ Loaded {len(rows)} pages from crawl.db")
    return dict(rows)

def run_evaluation_loop(base_url, db_path="crawl.db", refresh_k=10, submit_interval=14):
    pagerank_scores = load_pagerank_scores()
    node_map = load_latest_nodes(db_path)

    # Prepare entries with scores
    entries = []
    for pid, node in node_map.items():
        entries.append({
            "page_id": pid,
            "latest_node_id": node,
            "score": pagerank_scores.get(pid, 0.0)
        })

    log = []
    start_time = time.time()
    print(f"🚀 Starting evaluation loop for {len(entries)} pages...\n")

    while time.time() - start_time < 60:  # Run for 60s
        payload = {"entries": entries}
        ts = round(time.time() - start_time, 3)

        try:
            resp = requests.post(f"{base_url}/evaluate", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                print(f"[t={ts}s] ✅ Sent {len(entries)} entries | "
                      f"mse={data.get('mse', 0):.5f}, coverage={data.get('coverage', 0):.2f}, "
                      f"matched={data.get('matched_entries', 0)}")
                log.append({
                    "seconds_into_window": ts,
                    "entries_sent": len(entries),
                    "status_code": 200,
                    "response": data
                })
            else:
                print(f"[t={ts}s] ❌ Error {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"⚠️ Request error: {e}")

        time.sleep(submit_interval)

    print("\n✅ Evaluation loop finished. Log saved to evaluation_log.json")
    with open("evaluation_log.json", "w") as f:
        json.dump({"log": log}, f, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--db", default="crawl.db")
    parser.add_argument("--refresh-k", type=int, default=10)
    parser.add_argument("--submit-interval", type=int, default=14)
    args = parser.parse_args()

    run_evaluation_loop(args.base_url, args.db, args.refresh_k, args.submit_interval)
