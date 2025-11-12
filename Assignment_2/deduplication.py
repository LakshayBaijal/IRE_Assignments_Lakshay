import pandas as pd
from fuzzywuzzy import fuzz

# -----------------------
# Load dataset
# -----------------------
df = pd.read_csv("dedup_data.csv")
print(f"✅ Loaded dataset with {len(df)} rows")

# Combine key fields into one string for comparison
df["combined"] = (
    df["given_name"].astype(str) + " " +
    df["surname"].astype(str) + " " +
    df["address_1"].astype(str) + " " +
    df["suburb"].astype(str) + " " +
    df["postcode"].astype(str)
)

# -----------------------
# Deduplication parameters
# -----------------------
threshold = 90  # Adjust similarity threshold
visited = set()
groups = []

# -----------------------
# Group similar records
# -----------------------
for i in range(len(df)):
    if i in visited:
        continue
    base = df.loc[i, "combined"]
    group = [i]
    visited.add(i)
    
    for j in range(i + 1, len(df)):
        if j in visited:
            continue
        similarity = fuzz.token_set_ratio(str(base), str(df.loc[j, "combined"]))
        if similarity >= threshold:
            group.append(j)
            visited.add(j)
    
    groups.append(group)

# -----------------------
# Save grouped output
# -----------------------
grouped_rows = []
for idx, group in enumerate(groups, start=1):
    records = df.loc[group, ["given_name", "surname", "address_1", "suburb", "postcode"]]
    grouped_rows.append({
        "GroupID": idx,
        "Count": len(group),
        "Records": " | ".join(
            records.apply(lambda x: f"{x['given_name']} {x['surname']} ({x['address_1']}, {x['suburb']}, {x['postcode']})", axis=1)
        )
    })

result_df = pd.DataFrame(grouped_rows)
result_df.to_csv("dedup_results.csv", index=False)
print("\n✅ Deduplication complete! Saved to dedup_results.csv")
print(f"📦 Total unique groups: {len(result_df)}")
# -----------------------
# Generate mapping file (record → group)
# -----------------------
mapping_rows = []
for idx, group in enumerate(groups, start=1):
    for record_idx in group:
        mapping_rows.append({
            "Original_ID": df.loc[record_idx, "id"],
            "Given_Name": df.loc[record_idx, "given_name"],
            "Surname": df.loc[record_idx, "surname"],
            "GroupID": idx
        })

mapping_df = pd.DataFrame(mapping_rows)
mapping_df.to_csv("dedup_mapping.csv", index=False)
print("🗺️  Mapping file saved as dedup_mapping.csv")
