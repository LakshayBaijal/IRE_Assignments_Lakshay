<img width="1000" height="600" alt="image" src="https://github.com/user-attachments/assets/b115cc82-92d2-4041-9447-b66521366f57" /># IRE Assignment 1 - Text Indexing and Retrieval

## Introduction
It focuses on building and analyzing a self implemented inverted index and
comparing its query latency and performance with pre built indexing systems. The
task involves preprocessing, index construction, query execution, and latency
measurement on two datasets Wikipedia and News.

## Download Dataset
```br
https://drive.google.com/drive/folders/1G1bWYRaep7kCVg9a1cM7i-TI1rc0lZF6
```


## Directory Structure
```br
.
├── Assignment 1.pdf
├── Dataset
│   ├── webhose-news
│   │   └── data
│   │       ├── processed
│   │       │   ├── news_for_index.jsonl
│   │       │   └── news_preprocessed.jsonl
│   │       └── raw
│   │           └── news_combined.jsonl
│   └── Wiki_Dataset
│       └── data
│           ├── processed
│           │   ├── wiki_for_index.jsonl
│           │   └── wiki_preprocessed.jsonl
│           └── raw
│               └── wiki_sample.jsonl
└── ire_assignment
    ├── common
    │   └── version.py
    ├── es_scripts
    │   ├── es_build_index.py
    │   ├── es_measure_latency.py
    │   ├── es_plot_latency.py
    │   ├── es_search.py
    │   └── plot_performance_graph.py
    ├── index_base.py
    ├── indices
    │   ├── json
    │   ├── news_index
    │   │   ├── docs.json
    │   │   ├── meta.json
    │   │   └── postings.json
    │   ├── registry.json
    │   └── wiki_index
    │       ├── docs.json
    │       ├── meta.json
    │       └── postings.json
    ├── news_dataset.jsonl
    ├── news_index.db
    ├── news_latency.json
    ├── plots
    │   ├── latency_comparison.png
    │   ├── news_after.png
    │   ├── news_before.png
    │   ├── news_latency_plot.png
    │   ├── wiki_after.png
    │   ├── wiki_before.png
    │   └── wiki_latency_plot.png
    ├── requirements.txt
    ├── results
    │   ├── news_latency_plot.png
    │   ├── news_latency_results.csv
    │   ├── wiki_latency_plot.png
    │   └── wiki_latency_results.csv
    ├── run_selfindex.py
    ├── scripts
    │   ├── clean_wiki_for_index.py
    │   ├── export_to_redis.py
    │   ├── export_to_sqlite.py
    │   ├── filter_news_for_index.py
    │   ├── generate_queries.py
    │   ├── list_and_clear_indices.py
    │   ├── measure_latency.py
    │   ├── measure_latency_sqlite.py
    │   ├── news_queries.txt
    │   ├── performance_compare_es_vs_self.py
    │   ├── plot_latency.py
    │   ├── plot_latency_sqlite.py
    │   ├── preprocess_and_plot.py
    │   ├── preprocess_news.py
    │   ├── preprocess_wiki.py
    │   ├── queries.txt
    │   ├── rebuild_index.py
    │   ├── search_json_v.py
    │   ├── search_sqlite.py
    │   ├── search_sqlite_v.py
    │   ├── sqlite_to_jsonl.py
    │   ├── sqlite_to_jsonl_v2.py
    │   ├── verify_sqlite.py
    │   └── wiki_queries.txt
    ├── self_index.py
    ├── wiki_dataset.jsonl
    ├── wiki_index.db
    ├── wiki_latency.json
    └── wiki_postings.jsonl

20 directories, 66 files
```

## Build & Verify SQLite Index
- Build & Verify SQLite Index
```br
python3 scripts/build_index.py data/wiki.txt wiki_index.db
```
- Verify database contents
```br
python3 scripts/verify_sqlite.py wiki_index.db
```

## Search Using SQLite Index (SelfIndex-v1.x)
- Boolean retrieval (x=1)
```br
python3 scripts/search_sqlite_v.py wiki_index.db --version v1.12000 --query "artificial intelligence" --topk 10
```

- TF Ranking (x=2)

```br
python3 scripts/search_sqlite_v.py wiki_index.db --version v1.22000 --query "artificial intelligence" --topk 10
```

- TF-IDF Ranking (x=3)

```br
python3 scripts/search_sqlite_v.py wiki_index.db --version v1.32000 --query "artificial intelligence" --topk 10
```

- TF-IDF + Compression + Skipping (x=3, z=1, i=1)

```br
python3 scripts/search_sqlite_v.py wiki_index.db --version v1.32110 --query "artificial intelligence" --topk 10
```

- TF-IDF + Compression + Skipping + DAAT (x=3, z=1, i=1, q=2)
```br
python3 scripts/search_sqlite_v.py wiki_index.db --version v1.32112 --query "artificial intelligence" --topk 10
```

## Convert SQLite to JSON Format
- Generate JSONL from database

```br
python3 scripts/sqlite_to_jsonl.py wiki_index.db wiki_postings.jsonl
```

## Search Using JSON Version (SelfIndex-v1.y)
- Boolean Search (y=1, JSON datastore)
```br
python3 scripts/search_json_v.py wiki_postings.jsonl --version v1.12000 --query "artificial intelligence" --topk 10
```
- TF-IDF Search (y=1, JSON datastore)

```br
python3 scripts/search_json_v.py wiki_postings.jsonl --version v1.32000 --query "artificial intelligence" --topk 10
```

## Measure Query Latency
- Wiki Dataset

```br
python3 scripts/measure_latency_sqlite.py wiki_index.db scripts/wiki_queries.txt results/wiki_latency_results.csv
```

- News Dataset
```br
python3 scripts/measure_latency_sqlite.py news_index.db scripts/news_queries.txt results/news_latency_results.csv
```

## Plot Latency Results
- For wiki
```br
python3 scripts/plot_latency.py results/wiki_latency_results.csv
```
- For News
```br
python3 scripts/plot_latency.py results/news_latency_results.csv
```

## Run Elasticsearch Index (Docker)
```br
sudo docker start elasticsearch-container
curl http://localhost:9200
```

- Build ES index
```br
python3 es_scripts/es_build_index.py wiki_es_index wiki_dataset.jsonl
```
- Search
```br
python3 es_scripts/es_search.py wiki_es_index "artificial intelligence"
```

## Output
### Preprocessing
- News dataset
  
  <img width="926" height="206" alt="image" src="https://github.com/user-attachments/assets/e5917d90-19aa-4a10-a259-d199f7849139" />

- Wiki dataset
  
  <img width="903" height="202" alt="image" src="https://github.com/user-attachments/assets/0fc401be-0fc7-4be4-a674-f091039e70ce" />

### Index Construction
<img width="1516" height="139" alt="image" src="https://github.com/user-attachments/assets/ff85c1f8-310b-4312-b752-936047b9a3c3" />

### Verification of SQLite index showing document and posting counts.
<img width="1508" height="580" alt="image" src="https://github.com/user-attachments/assets/873ae22f-add5-4c47-ab7a-e8dbea335725" />

### Exporting preprocessed documents into SQLite for indexing.
<img width="1511" height="296" alt="image" src="https://github.com/user-attachments/assets/f3ba428d-642c-4206-b040-91415d9fbfa2" />

### Query Execution
- Wiki Dataset
  
  <img width="866" height="466" alt="image" src="https://github.com/user-attachments/assets/3552e87e-bcea-4dfa-9944-206f53a191f8" />
  <img width="875" height="348" alt="image" src="https://github.com/user-attachments/assets/271e328c-9456-4a8f-a109-1156d0deb5ae" />
  <img width="842" height="348" alt="image" src="https://github.com/user-attachments/assets/ca744935-589a-4914-86a6-e89192b6e96a" />
  <img width="840" height="348" alt="image" src="https://github.com/user-attachments/assets/c230ee45-ab86-43da-a138-1f14b7e00b88" />
  <img width="844" height="348" alt="image" src="https://github.com/user-attachments/assets/8aa325b6-c72e-4a5c-b92b-fe285a604e7d" />

- News Dataset

  <img width="869" height="228" alt="image" src="https://github.com/user-attachments/assets/1346d9f4-670c-439b-9231-814e93b9ea0c" />
  <img width="892" height="301" alt="image" src="https://github.com/user-attachments/assets/c9c660ae-e00d-4410-9da6-598cd8027e9f" />
  <img width="890" height="347" alt="image" src="https://github.com/user-attachments/assets/f2711df3-2aa7-49dd-92bc-90191566c198" />
  <img width="880" height="347" alt="image" src="https://github.com/user-attachments/assets/87e191f9-9c3f-49c4-ad02-c07a6eca2c86" />

### Latency Measurement
- Measuring query latency

<img width="874" height="227" alt="image" src="https://github.com/user-attachments/assets/e5ce07d2-9eaf-4b4d-9af4-5323b86c3a01" />

- Latency results for the Wiki dataset

<img width="896" height="315" alt="image" src="https://github.com/user-attachments/assets/dcbc9909-72ac-49d7-8047-cab5e6f0b7c9" />

- Latency results for the News dataset

<img width="920" height="315" alt="image" src="https://github.com/user-attachments/assets/05d98f62-81d5-4b4e-9269-47199f7408d5" />


### Latency Visualization
- Wiki Dataset before optimization

  <img width="1000" height="600" alt="image" src="https://github.com/user-attachments/assets/ffe675f8-543e-41da-a256-9cd978af2587" />

- Wiki dataset latency after optimization

  <img width="1000" height="600" alt="image" src="https://github.com/user-attachments/assets/af2df832-e9e8-4ed1-b8ef-70a35ae4dbb8" />

- News dataset latency before optimization

  <img width="1000" height="600" alt="image" src="https://github.com/user-attachments/assets/fb09d04b-bb63-4bc6-8ae5-5250ec66a5d0" />

- News dataset latency after optimization.

  <img width="1000" height="600" alt="image" src="https://github.com/user-attachments/assets/d08e637e-6dc7-4362-a80c-056b9b2ab4e7" />

- Bar plot of Wiki query latencies.

  <img width="1378" height="827" alt="image" src="https://github.com/user-attachments/assets/f65e98e2-24dd-4bd7-af5a-e41620003352" />

- Bar plot of News query latencies.

  <img width="1378" height="827" alt="image" src="https://github.com/user-attachments/assets/4703a8c8-b55f-4eb7-8a55-6fcf594f0ff0" />


## Performance Comparison
- performance difference between Wiki and News datasets

  <img width="534" height="395" alt="image" src="https://github.com/user-attachments/assets/79c76cb0-d273-4d99-afbd-3eae035c37da" />

- latency comparison graph between wiki and news dataset

  <img width="817" height="548" alt="image" src="https://github.com/user-attachments/assets/1714b896-b53a-47d0-a9d7-5cf45a30cbe7" />
  <img width="1000" height="600" alt="image" src="https://github.com/user-attachments/assets/f632678d-7272-4888-90bb-caa345f74264" />






