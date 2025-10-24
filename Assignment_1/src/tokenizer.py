#!/usr/bin/env python3
"""
Tokenizer for IRE Indexing Assignment.
Cleans, normalizes, and tokenizes text.
"""

import re
import nltk
from nltk.corpus import stopwords

try:
    STOPWORDS = set(stopwords.words("english"))
except LookupError:
    nltk.download("stopwords")
    STOPWORDS = set(stopwords.words("english"))

TOKEN_RE = re.compile(r"[A-Za-z]+")

def tokenize(text: str):
    """
    Convert input text into a list of normalized tokens.
    """
    text = text.lower()
    tokens = TOKEN_RE.findall(text)
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]
