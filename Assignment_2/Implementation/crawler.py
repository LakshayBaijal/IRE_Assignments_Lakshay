#!/usr/bin/env python3
"""
Robust crawler for Assignment 2

Features:
 - Automatically handles seeds like "page_xxx" or "xxx"
 - Optionally auto-detects a seed from the server homepage (--auto-seed)
 - Builds URLs as /page/<page_id> (works for this webserver)
 - Parses page_id, node_id, last_updated, outgoing links
 - Stores results to crawl.db and exports crawl_results.csv

Usage:
  python3 crawler.py --base-url http://localhost:3000 --seed page_wigymhsh --limit 200
  python3 crawler.py --base-url http://localhost:3000 --auto-seed --limit 200
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sqlite3
import time
import json
import csv
import argparse
import re
import sys

# ---------------------------
# Utilities
# ---------------------------
def normalize_page_id(raw):
    """Return a clean page id like 'page_xxx' (no leading slashes)."""
    if raw is None:
        return None
    s = str(raw).strip()
    # remove leading slashes
    s = s.lstrip("/")
    # If the path is like "page/<page_id>" or "page/page_xxx", take last segment
    if "/" in s:
        s = s.split("/")[-1]
    return s

def detect_seed_from_home(base_url, session, timeout=4):
    """Fetch base_url and attempt to find a page_<id> token in the HTML."""
    try:
        r = session.get(base_url, timeout=timeout)
        if r.status_code != 200:
            return None
        text = r.text
        # Find first occurrence of page_... token
        m = re.search(r"(page_[A-Za-z0-9]+)", text)
        if m:
            return m.group(1)
        # Also try more permissive token
        m2 = re.search(r"Page ID[:\s]*([A-Za-z0-9_/-]+)", text, re.I)
        if m2:
            return normalize_page_id(m2.group(1))
        return None
    except Exception:
        return None

# ---------------------------
# Page fetch & parse
# ---------------------------
def fetch_page(base_url, page_id, session, timeout=6):
    """Fetch a page and extract page_id, node_id, updated_at, out_links."""
    try:
        page_id_norm = normalize_page_id(page_id)
        if not page_id_norm:
            return None

        # Build canonical path: /page/<page_id>
        page_path = f"{page_id_norm}"
        url = urljoin(base_url, page_path)
        print(f"🌐 Fetching {url} ...")
        r = session.get(url, timeout=timeout)

        if r.status_code != 200:
            print(f"❌ Failed to fetch {page_id_norm}: Status code {r.status_code}")
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        # Extract page_id (preferred from the page content, otherwise use normalized)
        pid_candidate = None
        # look for explicit "Page ID" pattern
        text = soup.get_text(" ", strip=True)
        m_pid = re.search(r"(page_[A-Za-z0-9]+)", text)
        if m_pid:
            pid_candidate = m_pid.group(1)
        page_id_final = pid_candidate or page_id_norm

        # Extract node_id: look for "Node ID:" patterns first, then fallback to small tokens
        node_id = None
        m_node = re.search(r"Node ID[:\s]*([A-Za-z0-9_\-]{6,})", text, re.I)
        if m_node:
            node_id = m_node.group(1)
        else:
            # try looking for span.node-id b or similar tags
            node_tag = soup.select_one("span.node-id b")
            if node_tag and node_tag.text.strip():
                node_id = node_tag.text.strip()
            else:
                # as last resort, find any long alphanumeric token (heuristic)
                m_any = re.findall(r"[A-Za-z0-9_\-]{8,}", text)
                if m_any:
                    # prefer tokens that are not 'page_xxx'
                    for tkn in m_any:
                        if not tkn.startswith("page_"):
                            node_id = tkn
                            break

        # Extract last updated timestamp if present: "Last Updated: YYYY-MM-DD HH:MM:SS UTC"
        last_updated = None
        m_last = re.search(r"Last Updated[:\s]*([0-9]{4}-[0-9]{2}-[0-9]{2}\s+[0-9]{2}:[0-9]{2}:[0-9]{2})", text)
        if m_last:
            timestr = m_last.group(1).strip()
            try:
                # parse as UTC
                last_updated = int(time.mktime(time.strptime(timestr, "%Y-%m-%d %H:%M:%S")))
            except Exception:
                last_updated = int(time.time())
        else:
            last_updated = int(time.time())

        # Extract outgoing links: prefer hrefs like '/page/<page_id>' or '/page_<id>'
        out_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            # normalize
            if href.startswith("/"):
                href_clean = href.lstrip("/")
            else:
                href_clean = href
            # if it contains 'page_' anywhere, extract last token
            if "page_" in href_clean:
                link_id = normalize_page_id(href_clean)
                if link_id:
                    out_links.append(link_id)

        # deduplicate out_links while preserving order
        seen = set()
        out_links_unique = []
        for x in out_links:
            if x not in seen:
                seen.add(x)
                out_links_unique.append(x)

        return {
            "page_id": page_id_final,
            "node_id": node_id or "unknown",
            "updated_at": int(last_updated),
            "out_links": out_links_unique
        }

    except Exception as e:
        print(f"⚠️ Error fetching {page_id}: {e}")
        return None

# ---------------------------
# Crawl loop
# ---------------------------
def crawl(base_url, seed=None, limit=200, politeness=0.2, auto_seed=False):
    print(f"Starting crawl from seed: {seed if seed else '(none)'}")
    print(f"Base URL: {base_url}\n")

    session = requests.Session()

    # auto-detect seed if requested or not provided
    if auto_seed or not seed:
        detected = detect_seed_from_home(base_url, session)
        if detected:
            print(f"🔎 Auto-detected seed: {detected}")
            seed = detected
        else:
            print("❗ Could not auto-detect a seed page from the homepage. Provide --seed or try again.")
            return

    # normalize the seed id
    seed = normalize_page_id(seed)
    if not seed:
        print("❗ Invalid seed provided.")
        return

    frontier = [seed]
    visited = set()

    conn = sqlite3.connect('crawl.db')
    conn.execute('CREATE TABLE IF NOT EXISTS pages (page_id TEXT PRIMARY KEY, node_id TEXT, updated_at INTEGER, out_links TEXT)')
    conn.commit()

    total = 0
    try:
        while frontier and total < limit:
            page_id = frontier.pop(0)
            if page_id in visited:
                continue
            visited.add(page_id)

            page = fetch_page(base_url, page_id, session)
            if page:
                # store into sqlite
                try:
                    conn.execute('INSERT OR REPLACE INTO pages (page_id, node_id, updated_at, out_links) VALUES (?, ?, ?, ?)',
                                 (page['page_id'], page['node_id'], page['updated_at'], json.dumps(page['out_links'])))
                    conn.commit()
                except Exception as e:
                    print("DB write error:", e)

                # extend frontier with out_links (preserve small crawl order)
                for out in page['out_links']:
                    if out not in visited and out not in frontier:
                        frontier.append(out)

                total += 1
                print(f"✅ Crawled {total} pages so far...\n")

            # politeness delay
            time.sleep(politeness)

    except KeyboardInterrupt:
        print("\n⏹️ Crawl interrupted by user (KeyboardInterrupt). Exporting what we have...")

    finally:
        conn.close()

    # Export to CSV for easy viewing
    try:
        conn = sqlite3.connect('crawl.db')
        cursor = conn.cursor()
        cursor.execute("SELECT page_id, node_id, updated_at, out_links FROM pages")
        rows = cursor.fetchall()
        with open("crawl_results.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["PageID", "NodeID", "UpdatedAt", "OutgoingLinks"])
            for r in rows:
                writer.writerow(r)
        conn.close()
        print("\n✅ Crawling complete! Saved results to crawl_results.csv")
    except Exception as e:
        print("❗ Failed to export crawl_results.csv:", e)

# ---------------------------
# CLI
# ---------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Robust web crawler for Assignment 2")
    parser.add_argument("--base-url", required=True, help="Base URL of the web server (e.g., http://localhost:3000)")
    parser.add_argument("--seed", required=False, help="Seed page_id to start crawling (e.g., page_eain05vc)")
    parser.add_argument("--auto-seed", action="store_true", help="Try to auto-detect seed from homepage")
    parser.add_argument("--limit", type=int, default=200, help="Maximum number of pages to crawl")
    parser.add_argument("--politeness", type=float, default=0.2, help="Delay between requests (seconds)")
    args = parser.parse_args()

    try:
        crawl(args.base_url, seed=args.seed, limit=args.limit, politeness=args.politeness, auto_seed=args.auto_seed)
    except Exception as e:
        print("Fatal error:", e)
        sys.exit(1)
