#!/usr/bin/env python3
"""
evaluation_summary_plot.py
---------------------------------
Reads evaluation_log.json from crawler assignment,
computes summary statistics, and generates plots.

Outputs:
  - summary.csv
  - evaluation_visits_plot.png
  - entries_sent_plot.png
"""

import json
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------------
# 1. Load the evaluation log JSON
# -------------------------------
with open("evaluation_log.json", "r") as f:
    data = json.load(f)

# Extract all submission entries
entries = data.get("log", [])
df = pd.DataFrame(entries)

if df.empty:
    print("❌ No data found in evaluation_log.json")
    exit(1)

print(f"✅ Loaded {len(df)} submissions from evaluation_log.json")

# -------------------------------
# 2. Compute summary statistics
# -------------------------------
summary = {
    "total_submissions": len(df),
    "total_entries_sent": df["entries_sent"].sum(),
    "total_visits": df["total_visit_count"].iloc[-1],
    "avg_entries_per_submission": df["entries_sent"].mean(),
    "avg_status_code": df["status_code"].mean(),
}

# Extract response metrics if they exist (nested dictionary)
if "response" in df.columns:
    responses = pd.json_normalize(df["response"])
    for col in responses.columns:
        summary[f"avg_{col}"] = responses[col].mean()

summary_df = pd.DataFrame([summary])

# Save summary to CSV
summary_df.to_csv("summary.csv", index=False)
print("✅ Saved summary.csv")

# -------------------------------
# 3. Plot total visits over time
# -------------------------------
plt.figure(figsize=(8, 5))
plt.plot(df["seconds_into_window"], df["total_visit_count"], marker="o", color="steelblue", label="Total Visits")
plt.title("Total Visits Over Time During Evaluation")
plt.xlabel("Seconds into Window")
plt.ylabel("Total Visit Count")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("evaluation_visits_plot.png")
plt.close()
print("✅ Saved evaluation_visits_plot.png")

# -------------------------------
# 4. Plot entries sent over time
# -------------------------------
plt.figure(figsize=(8, 5))
plt.plot(df["seconds_into_window"], df["entries_sent"], marker="s", color="orange", label="Entries Sent")
plt.title("Entries Sent Over Time During Evaluation")
plt.xlabel("Seconds into Window")
plt.ylabel("Entries Sent")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("entries_sent_plot.png")
plt.close()
print("✅ Saved entries_sent_plot.png")

# -------------------------------
# 5. Print summary to console
# -------------------------------
print("\n📊 Evaluation Summary:")
print(summary_df.to_string(index=False))
