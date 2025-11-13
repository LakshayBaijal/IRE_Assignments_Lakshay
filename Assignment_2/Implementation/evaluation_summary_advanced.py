import json
import pandas as pd
import matplotlib.pyplot as plt

# Load evaluation log
with open("evaluation_log.json", "r") as f:
    data = json.load(f)

entries = data.get("log", [])
df = pd.DataFrame(entries)

if "response" in df.columns:
    responses = pd.json_normalize(df["response"])
    df = pd.concat([df.drop(columns=["response"]), responses], axis=1)

# Save summary
summary = {
    "total_submissions": len(df),
    "total_entries_sent": df["entries_sent"].sum(),
    "total_visits": df["total_visit_count"].iloc[-1],
    "avg_entries_per_submission": df["entries_sent"].mean(),
    "avg_status_code": df["status_code"].mean(),
    "avg_mse": df["mse"].mean() if "mse" in df.columns else None,
    "avg_coverage": df["coverage"].mean() if "coverage" in df.columns else None,
}
pd.DataFrame([summary]).to_csv("summary.csv", index=False)
print("✅ Saved summary.csv")

# Plot 1: Visits
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

# Plot 2: Entries
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

# Plot 3: MSE (if non-zero)
if "mse" in df.columns and df["mse"].sum() > 0:
    plt.figure(figsize=(8, 5))
    plt.plot(df["seconds_into_window"], df["mse"], marker="^", color="red", label="MSE")
    plt.title("Mean Squared Error vs Time")
    plt.xlabel("Seconds into Window")
    plt.ylabel("MSE")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("mse_vs_time.png")
    plt.close()
    print("✅ Saved mse_vs_time.png")
else:
    print("⚠️ Skipped MSE plot (no non-zero values).")

# Plot 4: Coverage (if non-zero)
if "coverage" in df.columns and df["coverage"].sum() > 0:
    plt.figure(figsize=(8, 5))
    plt.plot(df["seconds_into_window"], df["coverage"] * 100, marker="d", color="green", label="Coverage (%)")
    plt.title("Coverage vs Time")
    plt.xlabel("Seconds into Window")
    plt.ylabel("Coverage (%)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("coverage_vs_time.png")
    plt.close()
    print("✅ Saved coverage_vs_time.png")
else:
    print("⚠️ Skipped coverage plot (no non-zero values).")

# Plot 5: Combined
fig, ax1 = plt.subplots(figsize=(8, 5))
ax1.plot(df["seconds_into_window"], df["total_visit_count"], marker="o", color="blue", label="Total Visits")
ax1.set_xlabel("Seconds into Window")
ax1.set_ylabel("Total Visit Count", color="blue")
ax2 = ax1.twinx()
ax2.plot(df["seconds_into_window"], df["entries_sent"], marker="s", color="orange", label="Entries Sent")
ax2.set_ylabel("Entries Sent", color="orange")
plt.title("Combined Visits and Entries Over Time")
plt.grid(True)
plt.tight_layout()
plt.savefig("combined_visits_entries.png")
plt.close()

print("\n📊 Evaluation Summary:")
print(pd.DataFrame([summary]).to_string(index=False))
