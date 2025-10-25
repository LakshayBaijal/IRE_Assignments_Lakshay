

# Description
This project is part of the Information Retrieval Engineering (IRE) course.
It focuses on building a search engine that supports two types of indexing and querying mechanisms:

- ElasticSearch-based Search
- Self Index Search (Custom Implementation)

# Implementation
https://github.com/user-attachments/assets/54fb81d4-a82f-4ae8-b196-eeb6dd5020d3


# Features

- ElasticSearch Mode: Uses the ElasticSearch engine for indexing and querying.

- Self Index Mode: Implements a custom inverted index and search ranking system from scratch.

- Custom Tokenization and Preprocessing

- TF-IDF Based Ranking

- Efficient Index Storage

- Evaluation on Multiple Queries







# Project Structure
<img width="321" height="777" alt="Screenshot from 2025-10-25 03-54-46" src="https://github.com/user-attachments/assets/95699177-afda-401e-a157-49ad0b661b82" />

# Download Dataset and Indices
- Indices
  ```br
  https://drive.google.com/drive/folders/1z_tRs-PDJxildYpoKREzq2QhA4EGIuRc
  ```
- Dataset
  ```br
  https://drive.google.com/drive/folders/1zrTQUMP7srrhQCMSkwU27QB5xVxmM3DY
  ```
  
# Requirments

```br
python3 -m venv venv
source venv/bin/activate   # On Linux
```
# For ElasticSearch Mode

```br
sudo docker stop elasticsearch
sudo docker rm elasticsearch
sudo docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  docker.elastic.co/elasticsearch/elasticsearch:8.13.4
```
```br
sudo service elasticsearch start
sudo docker ps
```


# Scripts Execute
- For Search Engine {Self Index Mode}
```br
python -m scripts.search_engine
```
- For Comparision Between Elastic Search and Self Index Mode
```br
python scripts/test_es_index.py
python -m scripts.performance_compare_es_vs_self
```
- For Plotting Graph using Metrics.csv
```br
python -m scripts.plot_performance_graph
```
