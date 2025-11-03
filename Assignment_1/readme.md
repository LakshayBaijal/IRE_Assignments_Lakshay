# IRE Assignment 1 - Text Indexing and Retrieval

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
