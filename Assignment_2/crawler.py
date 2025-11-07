import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sqlite3
import time
import json
import csv
import argparse

# --- Fetch and parse a page ---
def fetch_page(base_url, page_id, session, timeout=5):
    try:
        url = urljoin(base_url, f"/{page_id}")
        print(f"🌐 Fetching {url} ...")
        r = session.get(url, timeout=timeout)

        if r.status_code != 200:
            print(f"❌ Failed to fetch {page_id}: Status code {r.status_code}")
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        # Extract page_id
        pid_tag = soup.find("div", class_="page-id")
        page_id = pid_tag.text.split(":")[-1].strip() if pid_tag else page_id

        # Extract node_id
        node_tag = soup.select_one("span.node-id b")
        node_id = node_tag.text.strip() if node_tag else "unknown"

        # Extract last updated timestamp (handle UTC)
        last_tag = soup.select_one("span.last-updated")
        if last_tag:
            ts_text = last_tag.text.strip().replace("Last Updated:", "").replace("UTC", "").strip()
            last_updated = int(time.mktime(time.strptime(ts_text, "%Y-%m-%d %H:%M:%S")))
        else:
            last_updated = int(time.time())

        # Extract outgoing links
        out_links = []
        for a in soup.find_all("a", href=True):
            if a["href"].startswith("/page_"):
                out_links.append(a["href"].strip("/"))

        return {
            "page_id": page_id,
            "node_id": node_id,
            "updated_at": last_updated,
            "out_links": out_links
        }

    except Exception as e:
        print(f"⚠️ Error fetching {page_id}: {e}")
        return None


# --- Main crawling function ---
def crawl(base_url, seed, limit):
    print(f"Starting crawl from seed: {seed}")
    print(f"Base URL: {base_url}\n")

    session = requests.Session()
    frontier = [seed]
    visited = set()

    conn = sqlite3.connect('crawl.db')
    conn.execute('CREATE TABLE IF NOT EXISTS pages (page_id TEXT PRIMARY KEY, node_id TEXT, updated_at INTEGER, out_links TEXT)')
    conn.commit()

    total = 0
    while frontier and total < limit:
        page_id = frontier.pop(0)
        if page_id in visited:
            continue
        visited.add(page_id)

        page = fetch_page(base_url, page_id, session)
        if page:
            conn.execute('INSERT OR REPLACE INTO pages (page_id, node_id, updated_at, out_links) VALUES (?, ?, ?, ?)',
                         (page['page_id'], page['node_id'], page['updated_at'], json.dumps(page['out_links'])))
            conn.commit()

            frontier.extend(page['out_links'])
            total += 1
            print(f"✅ Crawled {total} pages so far...\n")

    conn.close()

    # Export to CSV for easy viewing
    conn = sqlite3.connect('crawl.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pages")
    rows = cursor.fetchall()
    with open("crawl_results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["page_id", "node_id", "updated_at", "out_links"])
        writer.writerows(rows)
    conn.close()

    print("\n✅ Crawling complete! Saved results to crawl_results.csv")


# --- Command-line entry point ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple web crawler for Assignment 2")
    parser.add_argument("--base-url", required=True, help="Base URL of the web server (e.g., http://localhost:3000)")
    parser.add_argument("--seed", required=True, help="Seed page_id to start crawling (e.g., page_eain05vc)")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of pages to crawl")
    args = parser.parse_args()

    crawl(args.base_url, args.seed, args.limit)
