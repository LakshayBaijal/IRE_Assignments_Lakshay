# IRE Assignment 2 — Crawling & Deduplication

# Lakshay Baijal 2024202006

## Overview

- Activity 2.1: Deduplication using fuzzy matching (rapidfuzz/fuzzywuzzy). Produces `dedup_grouped.csv`, `dedup_mapping.csv`.
- Activity 2.2: Crawler, PageRank, evaluation submission.

```br
https://github.com/LakshayBaijal/IRE_Assignments_Lakshay/blob/main/Assignment_2/M25CS4.406_%20Deduplication%20and%20Crawling%20_%20Moodle.pdf
```
## Important Files

- dedup_data.csv
- dedup_grouped.csv
- dedup_mapping.csv
- crawler.py, crawl_results.csv, crawl.db
- pagerank.py, pagerank.csv
- evaluate_submit_refresh.py, evaluation_log.json
- evaluation_summary_advanced.py, summary.csv, \*.png plots
- README.md (this file)

## How to run (quick)

1. Start server:

```br
   docker load -i crawling_assignment-1.0-amd64.tar
   docker run --rm -p 3000:3000 -v $(pwd)/data:/data ... crawling_assignment:1.0
```

2. Crawl:

```br
  python3 crawler.py --base-url http://localhost:3000 --auto-seed --limit 200
```

3. PageRank:

```br
python3 pagerank.py
```

4. Evaluate (refresh top-K):

```br
python3 evaluate_submit_refresh.py --base-url http://localhost:3000 --db crawl.db --refresh-k 12 --submit-interval 14
```

5. Summarize + plots:

```br
python3 evaluation_summary_advanced.py
```

## Notes & rationale

- `evaluate_submit_refresh.py` refreshes top-K pages prior to each submit to reduce staleness and ensure `latest_node_id` matches server state.
- Tradeoff: increasing `refresh_k` increases visits (cost) but improves coverage and reduces staleness.


## Extras
- verify + load image (first time only)

```br
sha256sum -c crawling_assignment-1.0-amd64.tar.sha256
docker load -i crawling_assignment-1.0-amd64.tar
```

- run the server (every time you start it)

```br
docker run --rm -p 3000:3000 \
  --read-only --tmpfs /tmp:rw,noexec,nosuid \
  --cap-drop ALL --security-opt no-new-privileges \
  --pids-limit 128 --memory 256m \
  crawling_assignment:1.0
```

- crawl the site

```br
python crawler.py --base-url http://localhost:3000 --seed page_et51vpuo --limit 100
```

- compute pagerank

```br
python pagerank.py
```

- deduplication

```br
python dedup.py
```

- graph plot

````br
python export_graph.py

- stop the server
```br
docker ps
````

# Outputs
### Activity 2.1: Deduplication
- Deduplication Script Implements fuzzy comparison logic using RapidFuzz.
<img width="657" height="101" alt="image" src="https://github.com/user-attachments/assets/b3f83318-f32c-4f18-93cb-0aab14870289" />

- Deduplication Output - Displays grouped duplicate records.
<img width="822" height="477" alt="image" src="https://github.com/user-attachments/assets/76559ddd-a687-43ce-bb76-4772c7c56dce" />

- Grouped Results File - Shows unique group IDs assigned to each cluster of duplicates.
<img width="395" height="616" alt="image" src="https://github.com/user-attachments/assets/ba870ea2-8dec-4179-b5f1-46955b272f68" />

- Mapping File - Shows mapping between similar record IDs.
<img width="389" height="617" alt="image" src="https://github.com/user-attachments/assets/9ec341d3-43be-4585-ab72-e2f7ca5d6494" />

### Observation
The program successfully grouped 2838 distinct person clusters from 5000 entries. Variations like address formatting and misspellings were handled properly.

### Activity 2.2.1: Crawling
- Crawler Implementation - Performs link extraction, timestamp parsing, and database storage.
  <img width="665" height="739" alt="image" src="https://github.com/user-attachments/assets/02e3fe79-019b-4637-9d55-d9f6849889e0" />

- Crawling Results - Shows all pages visited and their outgoing link structure.
<img width="1041" height="294" alt="image" src="https://github.com/user-attachments/assets/7226c6ed-4c20-4841-8689-8151fe1726c8" />

### Activity 2.2.2: Page Rank

### Page Rank
Using the crawled link data, the PageRank algorithm was implemented to estimate the importance of each page based on incoming links.

𝑃𝑅(𝑖)=(1−𝑑)/𝑁+𝑑×Σ𝑗∈𝐼𝑛(𝑖)𝑃𝑅(𝑗)𝐿(𝑗)

Where d = 0.85 (damping factor) , N = total pages, ln(i) = incoming links to page I,
L(j) = number of outgoing links from page j.


- PageRank Script
<img width="472" height="146" alt="image" src="https://github.com/user-attachments/assets/632681d2-4207-424b-ac89-0dbd33d49d4a" />

- PageRank Results
<img width="414" height="427" alt="image" src="https://github.com/user-attachments/assets/ef39e017-038e-4939-86d2-b248184620fd" />

- Computed PageRank Output
<img width="365" height="275" alt="image" src="https://github.com/user-attachments/assets/1d6c3b50-d094-46fc-9cb5-56b42804ff43" />

- PageRank Analysis
<img width="542" height="249" alt="image" src="https://github.com/user-attachments/assets/5cfbc25f-e19c-4396-b39c-31e13f508ed2" />

- Edge List
<img width="337" height="542" alt="image" src="https://github.com/user-attachments/assets/cdbcb63e-5cf7-4f69-9e9f-89b46460e110" />

- Web Graph Visualization
<img width="907" height="642" alt="image" src="https://github.com/user-attachments/assets/f38f55b7-aec8-4720-8bb0-5b348ef3dc13" />


## Part D Updated Evaluation Mechanism (/evaluate endpoint)
### Efficient Refresh Strategy (K-refresher)
To minimize page visits and keep node_id values fresh, I implemented a Top-K Refresh Strategy:

- Compute PageRank from crawl.db

- Select top K highest PageRank pages

- Revisit only those pages to refresh node IDs

- Submit updated node_ids in each evaluation cycle


This approach minimizes visits while maximizing accuracy and freshness.
### Evaluation Script

- Loads PageRank scores
  
- Picks Top-K pages for refreshing

- Performs the required visits

- Submits evaluations every 14 seconds

- Collects all responses into evaluation_log.json


### Final Evaluation Metrics (from evaluation_log.json)

- Evaluation_log.json showing timestamps (seconds_into_window).
<img width="390" height="342" alt="image" src="https://github.com/user-attachments/assets/01985ae2-2ba8-4a54-94dd-da6ede64dafa" />
<img width="1391" height="287" alt="image" src="https://github.com/user-attachments/assets/1236e452-2fea-4a42-a000-dc5611bd1b03" />

- Terminal output showing evaluations sent at correct intervals (≈1s, 15s, 29s, 43s, 57s)
<img width="1389" height="165" alt="image" src="https://github.com/user-attachments/assets/d7c8c76b-4158-4aff-86c5-47996fe54d80" />
<img width="994" height="51" alt="image" src="https://github.com/user-attachments/assets/12267776-05af-47a1-95f7-4fa345a3d507" />

## Final Evaluation Metrics & Graphs
- Mean Squared Error (MSE)
MSE started near 0.0017 and increased slightly over time, indicating small deviations from the true PageRank.

<img width="800" height="500" alt="image" src="https://github.com/user-attachments/assets/d8053b18-0c86-4e6e-9ba4-6d21f5aac745" />

- 



# Observations and Learnings
- Fuzzy matching effectively handled name and address variations.

- The web crawler correctly parsed HTML, extracted links, and stored results.

- PageRank highlighted key hub pages with high incoming connections.

- Graph visualization provided intuitive insight into site structure.

# Conclusion
- Deduplication using fuzzy similarity scoring.

- Web crawling using a custom scraper and database storage.

- PageRank computation using power iteration on crawled data.

- Graph visualization of link topology.
Together, both parts illustrate real world applications of information retrieval and web indexing techniques.

