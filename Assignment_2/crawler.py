import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import time

# ---------------------------
# Command-line arguments
# ---------------------------
parser = argparse.ArgumentParser(description="Simple Web Crawler for IRE Assignment 2")
parser.add_argument("--base-url", required=True, help="Base URL of the local crawling server")
parser.add_argument("--seed", required=True, help="Seed page ID (e.g., page_abcd1234)")
parser.add_argument("--limit", type=int, default=100, help="Maximum number of pages to crawl")
args = parser.parse_args()

base_url = args.base_url.rstrip('/')
seed = args.seed
limit = args.limit

visited = set()
to_visit = [seed]
results = []

print(f"Starting crawl from seed: {seed}")
print(f"Base URL: {base_url}\n")

while to_visit and len(visited) < limit:
    page_id = to_visit.pop(0)
    if page_id in visited:
        continue

    url = f"{base_url}/{page_id}"
    print(f"Fetching {url}...")

    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print(f"❌ Failed to fetch {page_id}: Status code {response.status_code}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.text if soup.title else "No Title"
        links = [a["href"] for a in soup.find_all("a", href=True) if "page_" in a["href"]]

        # Add new links to queue
        for link in links:
            link_id = link.split('/')[-1]
            if link_id not in visited and link_id not in to_visit:
                to_visit.append(link_id)

        # Record result
        results.append({
            "PageID": page_id,
            "Title": title,
            "NumOutgoingLinks": len(links),
            "OutgoingLinks": ', '.join(links),
            "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })

        visited.add(page_id)

    except Exception as e:
        print(f"⚠️ Error fetching {page_id}: {e}")

# Save to CSV
df = pd.DataFrame(results)
df.to_csv("crawl_results.csv", index=False)
print("\n✅ Crawling complete! Saved results to crawl_results.csv")
