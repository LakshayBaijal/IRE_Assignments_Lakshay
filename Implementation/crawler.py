import time, re, requests
from collections import deque, defaultdict
from typing import Dict, List
from bs4 import BeautifulSoup
from metric import global_metric
from datetime import datetime

class NodeState:
    def __init__(self, page_id):
        self.page_id = page_id
        self.events: List[str] = []   # sequence of 'u' and 'v'
        self.last_node_id = None
        self.update_timestamps = deque(maxlen=1000)
        self.visit_timestamps = deque(maxlen=1000)

    def record_update(self, ts):
        # ts: float seconds
        self.update_timestamps.append(ts)

    def record_visit(self, ts):
        self.visit_timestamps.append(ts)

    def add_event(self, e):
        self.events.append(e)

class HTMLCrawler:
    def __init__(self, base_url="http://localhost:3000", eval_window=300.0, eval_interval=15.0, max_rps=5.0):
        self.base_url = base_url.rstrip('/')
        self.eval_window = eval_window
        self.eval_interval = eval_interval
        self.max_rps = max_rps
        self.nodes: Dict[str, NodeState] = {}
        self.adj = defaultdict(set)
        self.visited_pages = set()

    def _full_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def fetch_html(self, page_path: str) -> str:
        url = self._full_url(page_path)
        # fetch HTML (we DON'T request JSON)
        r = requests.get(url, timeout=6.0)
        r.raise_for_status()
        return r.text

    def parse_page(self, html: str) -> Dict:
        soup = BeautifulSoup(html, "html.parser")
        # page id (header .page-id)
        page_id_el = soup.find(class_="page-id")
        page_id = None
        if page_id_el:
            text = page_id_el.get_text(strip=True)
            # text like "Page ID: page_s1ns46p4"
            if ":" in text:
                page_id = text.split(":",1)[1].strip()
            else:
                page_id = text.strip()

        # node id (span.node-id or .node-id b)
        node_span = soup.find("span", class_="node-id")
        node_id = None
        if node_span:
            # check for <b> child
            b = node_span.find("b")
            if b:
                node_id = b.get_text(strip=True)
            else:
                # text like "Node ID: u8ljimebxup0"
                txt = node_span.get_text(" ", strip=True)
                if ":" in txt:
                    node_id = txt.split(":",1)[1].strip()
                else:
                    # fallback: take last token
                    node_id = txt.split()[-1].strip()

        # outgoing links: <a href="/page_xxx" ...>
        links = []
        for a in soup.select("a[href]"):
            href = a.get("href").strip()
            if href.startswith("/page_") or re.search(r"/page_[a-z0-9]+", href):
                # normalize to page_xxx (strip leading slash)
                links.append(href.lstrip("/"))
        # unique preserve order
        seen = set()
        links_unique = []
        for L in links:
            if L not in seen:
                seen.add(L)
                links_unique.append(L)

        # history: look for details summary "Previous IDs" then child divs containing "• id (timestamp)"
        history = []
        details = soup.find("details")
        if details:
            # find all divs inside details containing the bullet entries
            for div in details.find_all("div"):
                txt = div.get_text(" ", strip=True)
                # pattern: "• id (YYYY-MM-DD HH:MM:SS UTC)"
                m = re.search(r"•\s*([^\s(]+)\s*\(([^)]+)\)", txt)
                if m:
                    hid = m.group(1).strip()
                    tsraw = m.group(2).strip()
                    # try parse timestamp formats
                    ts = None
                    for fmt in ("%Y-%m-%d %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S UTC"):
                        try:
                            # some servers report "2025-12-02 19:16:47 UTC"
                            dt = datetime.strptime(tsraw, "%Y-%m-%d %H:%M:%S %Z")
                            ts = dt.timestamp()
                            break
                        except Exception:
                            pass
                    if ts is None:
                        # fallback: try split and remove timezone
                        try:
                            core = tsraw.replace("UTC","").strip()
                            dt = datetime.strptime(core, "%Y-%m-%d %H:%M:%S")
                            ts = dt.timestamp()
                        except Exception:
                            ts = None
                    history.append({"node_id": hid, "timestamp": ts, "raw": tsraw})
        return {"page_id": page_id, "node_id": node_id, "links": links_unique, "history": history}

    def discover_and_record(self, page_path: str, now: float):
        html = self.fetch_html(page_path)
        parsed = self.parse_page(html)
        pid = parsed.get("page_id") or page_path
        node_id = parsed.get("node_id")
        history = parsed.get("history", [])
        links = parsed.get("links", [])

        ns = self.nodes.setdefault(pid, NodeState(pid))
        # incorporate history updates (timestamps may be None if parsing failed)
        for h in history:
            ts = h.get("timestamp")
            if ts:
                ns.record_update(ts)
        # determine update event: if last_node_id is known and node_id != last_node_id -> 'u'
        if ns.last_node_id is not None and node_id is not None and node_id != ns.last_node_id:
            ns.add_event('u')
            ns.record_update(now)
        # always record visit
        ns.record_visit(now)
        ns.add_event('v')
        ns.last_node_id = node_id

        # adjacency
        for l in links:
            self.adj[pid].add(l)
            # ensure node object exists
            self.nodes.setdefault(l, NodeState(l))
        self.visited_pages.add(pid)
        return parsed

    def visit_loop(self, seed_page: str):
        start = time.time()
        end = start + self.eval_window
        now = time.time()
        # initial discovery
        self.discover_and_record(seed_page, now)
        frontier = deque([seed_page])

        while time.time() < end:
            now = time.time()
            # choose next: naive frontier first, else any discovered page
            if frontier:
                p = frontier.popleft()
            else:
                # pick a discovered but unvisited page
                unvisited = [x for x in self.nodes.keys() if x not in self.visited_pages]
                if unvisited:
                    p = unvisited[0]
                else:
                    # fallback: pick any known page (round-robin)
                    p = list(self.nodes.keys())[0]

            try:
                parsed = self.discover_and_record(p, time.time())
            except Exception as e:
                # ignore fetch/parse errors and continue
                # small sleep to avoid busy loop
                time.sleep(0.2)
                continue

            # expand frontier with links that we haven't visited
            for l in parsed.get("links", []):
                if l not in self.visited_pages and l not in frontier:
                    frontier.append(l)

            # throttle
            time.sleep(1.0 / max(1.0, self.max_rps))

        # done: compute metric and return events
        node_events = {pid: ns.events for pid, ns in self.nodes.items()}
        final_metric = global_metric(node_events)
        return final_metric, node_events
