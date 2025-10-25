

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

## Self Indexing Search Engine
<img width="1179" height="877" alt="Screenshot from 2025-10-26 01-08-58" src="https://github.com/user-attachments/assets/a82b3941-d158-4873-ba66-e9e7c14482ae" />

## Elastic Search Indexing
<img width="896" height="283" alt="Screenshot from 2025-10-25 02-17-51" src="https://github.com/user-attachments/assets/21b78a52-e9ec-467a-864b-c90eb6f38ce6" />

## Comparision between News and Wiki Self Indexing
<img width="534" height="395" alt="Screenshot from 2025-10-21 04-21-10" src="https://github.com/user-attachments/assets/97a079c0-6c49-4e87-b0af-54ba954b095a" />

## Comparision between News and Wiki Self Indexing Graph Plot
<img width="817" height="548" alt="Screenshot from 2025-10-26 01-04-35" src="https://github.com/user-attachments/assets/e8c5e086-8018-4302-a561-21f53f684749" />

## Comparision between Self Indexing and Elastic Search
<img width="1196" height="209" alt="Screenshot from 2025-10-26 01-06-25" src="https://github.com/user-attachments/assets/c15706be-5bd3-400d-a0c7-33eda245a50c" />

<img width="1213" height="830" alt="Screenshot from 2025-10-26 01-07-54" src="https://github.com/user-attachments/assets/dfb35552-da8e-4059-b6c6-c3a071a15b63" />

## Comparision between Self Indexing and Elastic Search Graph Plot
<img width="800" height="400" alt="performance_comparison" src="https://github.com/user-attachments/assets/327ba07b-a63f-4ede-a97c-d97f075824ea" />




