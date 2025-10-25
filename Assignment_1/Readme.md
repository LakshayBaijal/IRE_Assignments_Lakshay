

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


# Output Screenshots
<img width="1139" height="980" alt="Screenshot from 2025-10-21 03-43-50" src="https://github.com/user-attachments/assets/4229f8b6-3070-4fb9-84f9-2eb8971d58bf" />

<img width="534" height="395" alt="Screenshot from 2025-10-21 04-21-10" src="https://github.com/user-attachments/assets/1bbda886-872b-4956-adf7-95c7c96c31cf" />

<img width="797" height="577" alt="Screenshot from 2025-10-24 02-56-39" src="https://github.com/user-attachments/assets/d76b329a-8e13-44a0-bf02-35fe9c8ed4e6" />

<img width="1805" height="932" alt="Screenshot from 2025-10-23 05-03-56" src="https://github.com/user-attachments/assets/6dfbf434-a773-4949-ad48-2da4ed65b2fd" />

<img width="1805" height="932" alt="Screenshot from 2025-10-23 04-44-44" src="https://github.com/user-attachments/assets/bc9a1a46-1bee-4411-ab13-b4f653bcf289" />

<img width="534" height="395" alt="Screenshot from 2025-10-21 04-21-10" src="https://github.com/user-attachments/assets/c7ba3ac8-68cd-4994-98f5-28a30b8d305a" />




