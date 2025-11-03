# scripts/generate_queries.py
import json
import random
from tqdm import tqdm

# === CONFIG ===
INPUT_FILE = "../Dataset/Wiki_Dataset/data/processed/wiki_preprocessed.jsonl"
OUTPUT_FILE = "queries.txt"
NUM_QUERIES = 50

# === Load data ===
print(f"Loading tokens from {INPUT_FILE} ...")
tokens = set()

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    for line in tqdm(f, desc="Reading docs"):
        j = json.loads(line)
        toks = j["text"].split()
        for t in toks:
            if len(t) > 3:
                tokens.add(t)
tokens = list(tokens)
print(f"Collected {len(tokens)} unique tokens.")

# === Generate random queries ===
queries = []
for _ in range(NUM_QUERIES):
    a, b = random.sample(tokens, 2)
    op = random.choice(["AND", "OR"])
    queries.append(f'"{a}" {op} "{b}"')
    if random.random() < 0.3:
        c = random.choice(tokens)
        queries.append(f'NOT "{c}"')

# === Save queries ===
with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for q in queries:
        out.write(q + "\n")

print(f"✅ Generated {len(queries)} queries -> {OUTPUT_FILE}")
