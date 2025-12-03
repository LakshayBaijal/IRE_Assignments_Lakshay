# Assignment 2 - Crawling, PageRank & Deduplication
## Lakshay Baijal - 2024202006

### Execution

https://github.com/user-attachments/assets/3f325cba-c07e-488a-bea7-2ac11bd9cf1a

### Report {Results}
```br
https://github.com/LakshayBaijal/IRE_Assignments_Lakshay/blob/main/Assignment_2_Final_Updated/2024202006_Assignment_2.pdf
```

### Execution Commands
- Remove Container

```br
sudo docker stop crawling_srv
sudo docker rm crawling_srv
```

- Docker Image

```br
sudo docker load -i crawling_assignment_unlimited-amd64.tar
```

- Run Server

```br
mkdir -p server_data

sudo docker run -d \
  --name crawling_srv \
  -p 3000:3000 \
  -v "$(pwd)/server_data:/data" \
  crawling_assignment:unlimited
```

### Crawler To get Metrics

- Run Crawler
- 30s test

```br
python3 run_crawler.py --base-url http://localhost:3000 --window 30 --seed page_s1ns46p4 --rps 2
```

- 5 min test

```br
python3 run_crawler.py --base-url http://localhost:3000 --window 300 --seed page_s1ns46p4 --rps 2
```

```br
ls -lh final_metric.json node_events.json
```

```br
docker cp crawling_srv:/data/evaluation.bin ./evaluation.bin 2>/dev/null || true
```

### Deduplication

- Diagnose and Mapping

```br
python3 dedup_lsh.py --input dedup_data.csv
```

### Page Rank

- Check if Docker is running

```br
python3 pagerank_crawl.py --base-url http://localhost:3000 --seed page_s1ns46p4 --window 60 --rps 2 --max-nodes 200 --top 10
```

- Graph

```br
python3 graph_visualize.py --graph pagerank_graph.json --pr pagerank_scores.json
```

