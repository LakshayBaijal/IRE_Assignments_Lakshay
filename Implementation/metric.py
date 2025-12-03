from typing import List, Dict
def metric_for_sequence(events: List[str]) -> float:
    n = len(events)
    if n == 0:
        return 0.0
    total = 0
    cur = events[0]
    run_len = 1
    for e in events[1:]:
        if e == cur:
            run_len += 1
        else:
            total += run_len * run_len
            cur = e
            run_len = 1
    total += run_len * run_len
    return total / n

def global_metric(node_events: Dict[str, List[str]]) -> float:
    vals = []
    for seq in node_events.values():
        if len(seq) > 0:
            vals.append(metric_for_sequence(seq))
    if not vals:
        return 0.0
    return sum(vals) / len(vals)


