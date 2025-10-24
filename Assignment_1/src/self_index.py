#!/usr/bin/env python3
"""
SelfIndex: simple inverted-index implementation that can build/load/save/query.

- build_from_jsonl(path): expects JSONL with {"id": ..., "text": ..., "title": ... (opt)}
- save(path): saves a single JSON file containing index + docs metadata
- load(path): loads saved JSON index file
- query(q): returns a list of result dicts: [{"doc_id":..., "score":..., "snippet":...}, ...]
           also prints the top-N results for convenience (so CLI continues to show results)
"""

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
import re
from pathlib import Path
from typing import List, Dict, Any

TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)

def tokenize(text: str) -> List[str]:
    if not text:
        return []
    return [t.lower() for t in TOKEN_RE.findall(text)]

class SelfIndex:
    def __init__(self):
        # term -> list of doc_ids (we keep doc_ids as strings to match your JSON files)
        self.inverted_index: Dict[str, List[str]] = {}
        # doc_id -> full text
        self.documents: Dict[str, str] = {}
        # optional title store
        self.titles: Dict[str, str] = {}

    def build_from_jsonl(self, path: str, text_key_preference=None, max_docs=None):
        """
        Build an index from a JSONL file.
        text_key_preference: list of keys to try in order (default tries common ones)
        max_docs: optional int to limit docs (useful for quick tests)
        """
        if text_key_preference is None:
            text_key_preference = ["text", "body", "content", "article", "title"]

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"No such file: {path}")

        count = 0
        with path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if max_docs is not None and count >= max_docs:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                doc_id = str(obj.get("id", str(i)))
                # pick best text field
                text = ""
                for k in text_key_preference:
                    if obj.get(k):
                        text = obj.get(k)
                        break
                if text is None:
                    text = ""
                text = str(text).strip()
                if not text:
                    # skip empty
                    continue
                self.documents[doc_id] = text
                title = obj.get("title", "")
                if title:
                    self.titles[doc_id] = str(title)

                tokens = tokenize(text)
                seen = set()
                for tok in tokens:
                    if tok in seen:
                        # keep posting only once for this doc (we are using term->doclist)
                        continue
                    seen.add(tok)
                    if tok not in self.inverted_index:
                        self.inverted_index[tok] = []
                    self.inverted_index[tok].append(doc_id)
                count += 1

        return {"indexed": count, "unique_terms": len(self.inverted_index)}

    def save(self, path: str):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        out = {
            "info": "SELF_INDEX",
            "total_docs": len(self.documents),
            "total_terms": len(self.inverted_index),
            "index": self.inverted_index,
            "docs": self.documents,
            "titles": self.titles
        }
        with path.open("w", encoding="utf-8") as f:
            json.dump(out, f)
        return str(path)

    def load(self, path: str):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"No such index file: {path}")
        with path.open("r", encoding="utf-8") as f:
            j = json.load(f)
        self.inverted_index = {k: v.copy() for k, v in j.get("index", {}).items()}
        self.documents = {k: v for k, v in j.get("docs", {}).items()}
        self.titles = {k: v for k, v in j.get("titles", {}).items()}
        return {"loaded_docs": len(self.documents), "loaded_terms": len(self.inverted_index)}

    def _phrase_search(self, phrase: str) -> List[str]:
        """Return doc_ids containing the exact phrase (case-insensitive)."""
        phrase_l = phrase.lower()
        results = []
        for doc_id, text in self.documents.items():
            if phrase_l in text.lower():
                results.append(doc_id)
        return results

    def _term_docs(self, term: str) -> List[str]:
        return self.inverted_index.get(term.lower(), []).copy()

    def query(self, q: str) -> List[Dict[str, Any]]:
        """
        Query the index. Supported forms:
          - phrase search: "some phrase" (double quotes)
          - boolean-ish: simple use of AND/OR/NOT between terms (left-to-right)
          - single-term queries: returns docs containing the term.
        Returns: list of dicts: {"doc_id":..., "score": float, "snippet": "..."}
        Also prints top 10 results for convenience (so interactive scripts can still show them).
        """
        q = q.strip()
        if not q:
            return []

        # phrase
        if q.startswith('"') and q.endswith('"') and len(q) >= 2:
            phrase = q[1:-1].strip()
            doc_ids = self._phrase_search(phrase)
            results = []
            for did in doc_ids:
                txt = self.documents.get(did, "")
                snippet = txt[:300].replace("\n", " ")
                results.append({"doc_id": did, "score": 1.0, "snippet": snippet})
            # print
            print(f"🔍 Query: '{q}' → {len(results)} results (phrase search)")
            for r in results[:10]:
                print(f"  - {r['doc_id']}: {r['snippet'][:120]}...")
            return results

        # tokenize query for boolean-ish handling
        parts = q.split()
        # simple boolean evaluator:
        # support tokens AND, OR, NOT (capitalization ignored). Evaluate left-to-right.
        # start with first term's doc set, then combine.
        def get_set_for_token(tok: str):
            if tok.upper() in ("AND", "OR", "NOT"):
                return tok.upper()
            # normal term
            return set(self._term_docs(tok))

        # build list of operands / ops
        stack = []
        for tok in parts:
            stack.append(get_set_for_token(tok))

        # if only one set (single-term or multiple words not using AND/OR/NOT) -> union of terms
        if all(isinstance(x, set) for x in stack):
            # union documents of all tokens
            union_set = set()
            for s in stack:
                union_set |= s
            ranked = self._rank_by_term_frequency(list(union_set), parts)
        else:
            # evaluate left-to-right
            # initial value:
            i = 0
            # find first set
            while i < len(stack) and not isinstance(stack[i], set):
                i += 1
            if i >= len(stack):
                return []
            current = stack[i]
            i += 1
            while i < len(stack):
                op = stack[i]
                i += 1
                # find next set
                while i < len(stack) and not isinstance(stack[i], set):
                    # handle consecutive operators by skipping invalids
                    i += 1
                if i >= len(stack):
                    break
                nxt = stack[i]
                i += 1
                if op == "AND":
                    current = current & nxt
                elif op == "OR":
                    current = current | nxt
                elif op == "NOT":
                    current = current - nxt
                else:
                    # unexpected operator token (treat as OR)
                    current = current | nxt
            ranked = self._rank_by_term_frequency(list(current), parts)

        # Build results list of dicts
        results = []
        for doc_id, score in ranked:
            text = self.documents.get(doc_id, "")
            snippet = text[:300].replace("\n", " ")
            results.append({"doc_id": doc_id, "score": float(score), "snippet": snippet})

        # Print top 10
        print(f"🔍 Query: '{q}' → {len(results)} results")
        for r in results[:10]:
            print(f"  - {r['doc_id']}: {r['snippet'][:120]}...")

        return results

    def _rank_by_term_frequency(self, doc_ids: List[str], query_terms: List[str]):
        """
        A tiny ranking: score = number of distinct query terms that appear in the document.
        Return list of (doc_id, score) sorted desc by score then by doc_id.
        """
        out = []
        q_terms = [t.lower() for t in query_terms if t.upper() not in ("AND", "OR", "NOT")]
        q_terms = [t for t in q_terms if t]  # remove empties
        for did in doc_ids:
            text = self.documents.get(did, "").lower()
            count = 0
            for qt in set(q_terms):
                if qt in text:
                    count += 1
            out.append((did, count))
        out.sort(key=lambda x: (-x[1], x[0]))
        return out
