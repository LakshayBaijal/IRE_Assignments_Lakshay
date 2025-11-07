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
python crawler.py --base-url http://localhost:3000 --seed page_eain05vc --limit 100
```
```br
sqlite3 crawl.db "SELECT COUNT(*) FROM pages;"
sqlite3 crawl.db "SELECT page_id, length(out_links) FROM pages LIMIT 10;"
```

- compute pagerank + save graph

```br
python pagerank_analysis.py
```

- deduplication
```br
python deduplication.py
```

- stop the server 
```br
docker ps 
```
