# self_index.py
from __future__ import annotations
import json
import re
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Tuple, Dict, List, Set

# If you have an IndexBase provided by your assignment, keep using it.
# This code expects index_base.py to be in the same folder.
try:
    from index_base import IndexBase
except Exception:
    # Minimal fallback if index_base.py isn't present. Keeps compatibility.
    class IndexBase:
        def __init__(self, *args, **kwargs):
            pass

ROOT = Path(__file__).parent
INDICES_DIR = ROOT / "indices"
REGISTRY_PATH = INDICES_DIR / "registry.json"
INDICES_DIR.mkdir(parents=True, exist_ok=True)
if not REGISTRY_PATH.exists():
    REGISTRY_PATH.write_text(json.dumps({"indices": {}}, indent=2))

_token_re = re.compile(r"[A-Za-z0-9]+")

def tokenize(text: str) -> List[str]:
    if not text:
        return []
    return [m.group(0).lower() for m in _token_re.finditer(text)]

@dataclass
class Posting:
    doc_id: str
    positions: List[int]

class SelfIndex(IndexBase):
    def __init__(self):
        super().__init__("SelfIndex", "BOOLEAN", "CUSTOM", "TERMatat", "NONE", "Null")
        self.inverted: Dict[str, List[Posting]] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.index_id: str | None = None

    def _index_dir_for(self, index_id: str) -> Path:
        return INDICES_DIR / index_id

    def _save_registry(self, index_id: str, meta: dict):
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            reg = json.load(f)
        reg.setdefault("indices", {})[index_id] = meta
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(reg, f, indent=2)

    def _load_registry(self) -> dict:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def create_index(self, index_id: str, files: Iterable[Tuple[str, str]]) -> None:
        idx_dir = self._index_dir_for(index_id)
        idx_dir.mkdir(parents=True, exist_ok=True)

        inverted: Dict[str, Dict[str, List[int]]] = defaultdict(lambda: defaultdict(list))
        doc_lengths: Dict[str, int] = {}

        for doc_id, text in files:
            if doc_id is None:
                continue
            terms = tokenize(text or "")
            doc_lengths[doc_id] = len(terms)
            for pos, t in enumerate(terms):
                inverted[t][doc_id].append(pos)

        postings_json = {term: [{"doc_id": d, "positions": poslist}
                               for d, poslist in doc2pos.items()]
                         for term, doc2pos in inverted.items()}

        with open(idx_dir / "postings.json", "w", encoding="utf-8") as f:
            json.dump(postings_json, f)

        with open(idx_dir / "docs.json", "w", encoding="utf-8") as f:
            json.dump({"doc_lengths": doc_lengths}, f)

        meta = {"core": "SelfIndex", "info": "BOOLEAN",
                "dstore": "CUSTOM", "compr": "NONE",
                "qproc": "TERMatat", "optim": "Null"}
        with open(idx_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        self._save_registry(index_id, meta)
        print(f"[OK] Created index '{index_id}' at {idx_dir}")

    def load_index(self, index_id_or_path: str) -> None:
        idx_dir = Path(index_id_or_path)
        if not idx_dir.exists():
            idx_dir = self._index_dir_for(index_id_or_path)
            if not idx_dir.exists():
                raise FileNotFoundError(f"Index not found: {index_id_or_path}")

        with open(idx_dir / "postings.json", "r", encoding="utf-8") as f:
            inv_json = json.load(f)
        with open(idx_dir / "docs.json", "r", encoding="utf-8") as f:
            docs_json = json.load(f)

        self.inverted = {t: [Posting(p["doc_id"], p["positions"]) for p in plist]
                         for t, plist in inv_json.items()}
        self.doc_lengths = docs_json.get("doc_lengths", {})
        self.index_id = idx_dir.name
        print(f"[OK] Loaded index '{self.index_id}'")

    def update_index(self, index_id: str,
                     remove_files: Iterable[Tuple[str, str]],
                     add_files: Iterable[Tuple[str, str]]) -> None:
        self.load_index(index_id)
        to_remove = {doc_id for doc_id, _ in (remove_files or [])}
        for term in list(self.inverted.keys()):
            postings = [p for p in self.inverted[term] if p.doc_id not in to_remove]
            if postings:
                self.inverted[term] = postings
            else:
                del self.inverted[term]
        for r in to_remove:
            self.doc_lengths.pop(r, None)
        for doc_id, text in (add_files or []):
            terms = tokenize(text or "")
            self.doc_lengths[doc_id] = len(terms)
            for pos, t in enumerate(terms):
                lst = self.inverted.setdefault(t, [])
                for p in lst:
                    if p.doc_id == doc_id:
                        p.positions.append(pos)
                        break
                else:
                    lst.append(Posting(doc_id, [pos]))
        idx_dir = self._index_dir_for(index_id)
        postings_json = {term: [{"doc_id": p.doc_id, "positions": p.positions}
                                for p in plist]
                         for term, plist in self.inverted.items()}
        with open(idx_dir / "postings.json", "w", encoding="utf-8") as f:
            json.dump(postings_json, f)
        with open(idx_dir / "docs.json", "w", encoding="utf-8") as f:
            json.dump({"doc_lengths": self.doc_lengths}, f)

    def _postings_map_for_term(self, term: str) -> Dict[str, List[int]]:
        lst = self.inverted.get(term, [])
        return {p.doc_id: p.positions for p in lst}

    def _docs_for_term(self, term: str) -> Set[str]:
        return set(self._postings_map_for_term(term).keys())

    def _eval_phrase(self, phrase: str) -> Set[str]:
        words = [w for w in tokenize(phrase) if w]
        if not words:
            return set()
        candidate = self._docs_for_term(words[0]).copy()
        for w in words[1:]:
            candidate &= self._docs_for_term(w)
            if not candidate:
                return set()
        results = set()
        for d in candidate:
            pos_lists = [self._postings_map_for_term(w)[d] for w in words]
            pos_sets = [set(pl) for pl in pos_lists]
            for p0 in pos_lists[0]:
                if all((p0 + i) in pos_sets[i] for i in range(len(words))):
                    results.add(d)
                    break
        return results

    def query(self, q: str) -> str:
        try:
            tokens = self._lex_query(q)
            rpn = self._to_rpn(tokens)
            docs = self._eval_rpn(rpn)
            results = [{"doc_id": d} for d in sorted(docs)]
            return json.dumps({"index_id": self.index_id, "count": len(results), "results": results}, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _lex_query(self, q: str) -> List[str]:
        tokens = []
        i = 0
        while i < len(q):
            if q[i].isspace():
                i += 1; continue
            if q[i] in "()":
                tokens.append(q[i]); i += 1; continue
            if q[i] == '"':
                j = i+1
                while j < len(q) and q[j] != '"':
                    j += 1
                if j >= len(q):
                    raise ValueError("Unclosed quote in query")
                tokens.append(q[i:j+1]); i = j+1; continue
            m = re.match(r"[A-Za-z0-9]+", q[i:])
            if m:
                w = m.group(0)
                uw = w.upper()
                if uw in ("AND", "OR", "NOT"):
                    tokens.append(uw)
                else:
                    tokens.append(f'"{w}"')
                i += len(w); continue
            raise ValueError(f"Unexpected character in query near: {q[i:i+10]!r}")
        return tokens

    def _to_rpn(self, tokens: List[str]) -> List[str]:
        prec = {"NOT": 3, "AND": 2, "OR": 1}
        out, stack = [], []
        for tok in tokens:
            if tok in ("AND", "OR", "NOT"):
                while stack and stack[-1] in prec and prec[stack[-1]] >= prec[tok]:
                    out.append(stack.pop())
                stack.append(tok)
            elif tok == "(":
                stack.append(tok)
            elif tok == ")":
                while stack and stack[-1] != "(":
                    out.append(stack.pop())
                if not stack:
                    raise ValueError("Mismatched parentheses")
                stack.pop()
            else:
                out.append(tok)
        while stack:
            op = stack.pop()
            if op in ("(", ")"):
                raise ValueError("Mismatched parentheses")
            out.append(op)
        return out

    def _eval_rpn(self, rpn: List[str]) -> Set[str]:
        st: List[Set[str]] = []
        universe = set(self.doc_lengths.keys())
        for tok in rpn:
            if tok == "NOT":
                if not st:
                    raise ValueError("NOT operator missing operand")
                a = st.pop()
                st.append(universe - a)
            elif tok == "AND":
                b = st.pop(); a = st.pop(); st.append(a & b)
            elif tok == "OR":
                b = st.pop(); a = st.pop(); st.append(a | b)
            else:
                term = tok
                if term.startswith('"') and term.endswith('"'):
                    content = term[1:-1]
                    docs = self._eval_phrase(content)
                else:
                    docs = self._docs_for_term(term)
                st.append(docs)
        if len(st) != 1:
            raise ValueError("Malformed query")
        return st[0]

    def delete_index(self, index_id: str) -> None:
        idx_dir = self._index_dir_for(index_id)
        if idx_dir.exists():
            for f in idx_dir.iterdir():
                f.unlink()
            idx_dir.rmdir()
        reg = self._load_registry()
        reg.get("indices", {}).pop(index_id, None)
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(reg, f, indent=2)
        print(f"[Deleted] {index_id}")

    def list_indices(self) -> List[str]:
        reg = self._load_registry()
        return list(reg.get("indices", {}).keys())

    def list_indexed_files(self, index_id: str) -> List[str]:
        idx_dir = self._index_dir_for(index_id)
        docs_path = idx_dir / "docs.json"
        if not docs_path.exists():
            return []
        with open(docs_path, "r", encoding="utf-8") as f:
            dj = json.load(f)
        return list(dj.get("doc_lengths", {}).keys())
