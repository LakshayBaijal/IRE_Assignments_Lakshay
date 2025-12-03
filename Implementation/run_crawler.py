import argparse, json
from crawler import HTMLCrawler
from extra_metrics import compute_extra_metrics
import json
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--base-url', default='http://localhost:3000', help='base URL')
    p.add_argument('--window', type=int, default=300, help='evaluation window seconds')
    p.add_argument('--seed', default='page_s1ns46p4', help='seed page id from portal')
    p.add_argument('--rps', type=float, default=3.0, help='max requests per second')
    args = p.parse_args()

    c = HTMLCrawler(base_url=args.base_url, eval_window=args.window, max_rps=args.rps)
    final_metric, node_events = c.visit_loop(args.seed)

    with open('final_metric.json', 'w') as f:
        json.dump({'final_metric': final_metric, 'num_nodes': len(node_events)}, f, indent=2)
    with open('node_events.json', 'w') as f:
        json.dump(node_events, f, indent=2)

    print("final_metric:", final_metric)
    extra = compute_extra_metrics(c.nodes, window=args.window)

    print("Coverage:", extra["coverage"])
    print("Visit Count:", extra["visit_count"])
    print("Matched Entries:", extra["matched_entries"])
    print("Total Nodes:", extra["total_nodes"])
    print("MSE:", extra["mse"])

    with open("extra_metrics.json","w") as f:
        json.dump(extra, f, indent=2)
if __name__ == '__main__':
    main()
