# debug_timestamps.py
import json
from pprint import pprint
from importlib import import_module

# loads node_events.json and prints some raw timestamp samples
try:
    with open('node_events.json','r') as f:
        node_events = json.load(f)
except Exception as e:
    print("node_events.json not found:", e)
    node_events = None

# If you want to inspect crawler internal NodeState objects, run the crawler then run this script
# It will instead read extra_metrics diagnostics file if available
try:
    with open('extra_metrics.json','r') as f:
        extra = json.load(f)
        print("extra_metrics diagnostics:", extra.get('diagnostics', {}))
except:
    pass

# show a few sample nodes from node_events.json (if present)
if node_events:
    print("Sample nodes and their event lengths:")
    i = 0
    for k, v in node_events.items():
        print(k, "=> events:", len(v), "first_10:", v[:10])
        i += 1
        if i >= 8:
            break
