# extra_metrics.py
import math
from statistics import median, mean

def _to_seconds(ts):
    """
    Convert timestamp to seconds if it looks like milliseconds.
    If ts is None or 0 -> return None.
    """
    if ts is None:
        return None
    try:
        ts = float(ts)
    except Exception:
        return None
    # if timestamp is very large (ms), convert to seconds
    # epoch seconds ~1e9..1.8e9, ms ~1e12
    if ts > 1e11:
        return ts / 1000.0
    return ts

def compute_extra_metrics(nodes, window=300.0, cap_error_to_window=True):
    """
    nodes: dict of NodeState objects (has visit_timestamps, update_timestamps)
    window: normalization window in seconds
    cap_error_to_window: if True, clip error to [0, window]
    Returns dict with coverage, visit_count, matched_entries, total_nodes, mse, and diagnostics.
    """
    total_nodes = len(nodes)
    visited_nodes = 0
    matched_entries = 0
    total_visits = 0
    mse_values = []

    # collect some diagnostics about raw differences
    diffs = []

    for pid, ns in nodes.items():
        visits = [ _to_seconds(x) for x in list(ns.visit_timestamps) if _to_seconds(x) is not None ]
        updates = [ _to_seconds(x) for x in list(ns.update_timestamps) if _to_seconds(x) is not None ]

        if visits:
            visited_nodes += 1
            total_visits += len(visits)

        if updates:
            matched_entries += 1

        if visits and updates:
            last_update = updates[-1]
            for v in visits:
                error = v - last_update
                # treat visits before update as zero error
                if error < 0:
                    error = 0.0

                # cap error to window if requested
                if cap_error_to_window and error > window:
                    error = window

                norm = error / float(window) if window > 0 else 0.0
                mse_values.append(norm * norm)
                diffs.append(error)

    coverage = visited_nodes / total_nodes if total_nodes > 0 else 0.0
    mse = (sum(mse_values) / len(mse_values)) if mse_values else 0.0

    # diagnostics on diffs (in seconds)
    diag = {}
    if diffs:
        diffs_sorted = sorted(diffs)
        diag['diff_min'] = diffs_sorted[0]
        diag['diff_max'] = diffs_sorted[-1]
        diag['diff_median'] = median(diffs_sorted)
        diag['diff_mean'] = mean(diffs_sorted)
        # some percentiles
        def pct(arr, p):
            if not arr: return None
            k = int(len(arr) * p)
            k = min(max(k,0), len(arr)-1)
            return arr[k]
        diag['p10'] = pct(diffs_sorted, 0.10)
        diag['p25'] = pct(diffs_sorted, 0.25)
        diag['p75'] = pct(diffs_sorted, 0.75)
        diag['p90'] = pct(diffs_sorted, 0.90)
    else:
        diag['diff_min'] = diag['diff_max'] = diag['diff_median'] = diag['diff_mean'] = None

    return {
        "coverage": coverage,
        "visit_count": total_visits,
        "matched_entries": matched_entries,
        "total_nodes": total_nodes,
        "mse": mse,
        "diagnostics": diag
    }
