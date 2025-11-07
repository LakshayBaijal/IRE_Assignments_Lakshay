import pandas as pd
from rapidfuzz import fuzz
from itertools import combinations
import csv

def is_similar(record1, record2, threshold=85):
    """
    Compare two records using fuzzy string matching.
    Returns True if they are similar enough to be considered duplicates.
    """
    score = 0
    fields = ['given_name', 'surname', 'address_1', 'suburb', 'state', 'date_of_birth']

    for field in fields:
        val1 = str(record1.get(field, '')).strip().lower()
        val2 = str(record2.get(field, '')).strip().lower()
        if val1 and val2:
            score += fuzz.token_sort_ratio(val1, val2)
    
    avg_score = score / len(fields)
    return avg_score >= threshold


def group_duplicates(df, threshold=85):
    """
    Group records that are similar to each other.
    """
    groups = []
    visited = set()

    for i, row1 in df.iterrows():
        if i in visited:
            continue
        group = [row1['id']]
        visited.add(i)

        for j, row2 in df.iterrows():
            if j in visited:
                continue
            if is_similar(row1, row2, threshold):
                group.append(row2['id'])
                visited.add(j)
        groups.append(group)

    return groups


def main():
    # Load dataset
    df = pd.read_csv("dedup_data.csv")
    print(f"📊 Loaded {len(df)} records.")

    # Group similar records
    print("🔍 Grouping possible duplicates...")
    groups = group_duplicates(df)

    # Save grouped output
    with open("dedup_grouped.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["group_id", "record_ids"])
        for i, group in enumerate(groups, 1):
            writer.writerow([i, ";".join(map(str, group))])

    print(f"✅ Deduplication complete! {len(groups)} groups written to dedup_grouped.csv")


if __name__ == "__main__":
    main()
