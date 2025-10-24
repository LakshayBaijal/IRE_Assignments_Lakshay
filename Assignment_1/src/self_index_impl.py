#!/usr/bin/env python3
"""
Implements TF-IDF scoring for the SelfIndex.
"""

import math
from collections import defaultdict
from src.tokenizer import tokenize


def compute_tfidf_scores(index, doc_store, query):
    """
    Compute TF-IDF scores for the given query.
    """
    terms = tokenize(query)
    scores = defaultdict(float)
    N = len(doc_store)

    for term in terms:
        if term not in index:
            continue
        postings = index[term]
        df = len(postings)
        idf = math.log((N + 1) / (df + 1)) + 1
        for doc_id, tf in postings.items():
            scores[doc_id] += tf * idf

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[:10]


def query(self, q: str):
    """Search the index for the given query and return ranked results."""
    q = q.strip()
    if not q:
        return []

    if not hasattr(self, "inverted_index"):
        print("⚠️ Index not loaded.")
        return []

    q_terms = [t.lower() for t in q.split()]
    matched = {}
    for term in q_terms:
        if term in self.inverted_index:
            for doc_id in self.inverted_index[term]:
                matched[doc_id] = matched.get(doc_id, 0) + 1

    # Rank by match frequency
    ranked = sorted(matched.items(), key=lambda x: x[1], reverse=True)
    results = []

    for doc_id, score in ranked:
        text = self.documents.get(doc_id, "")
        snippet = text[:250].replace("\n", " ")
        results.append({
            "doc_id": doc_id,
            "score": float(score),
            "snippet": snippet
        })

    # Optional: console feedback
    print(f"🔍 Query: '{q}' → {len(results)} results")

    # ✅ Always return the list for display_results() to use
    return results

