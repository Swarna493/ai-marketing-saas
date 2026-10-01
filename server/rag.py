import csv
import math
import os
import re
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "dataset", "marketing_dataset.csv")

FIELDS = ["product", "category", "description", "target_audience",
          "platform", "tone", "keywords", "brand_style"]


def _tokenize(text):
    return re.findall(r"[a-z0-9]+", str(text).lower())


rows = []
doc_tokens = []
try:
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
            text = " ".join((row.get(k) or "") for k in FIELDS)
            doc_tokens.append(_tokenize(text))
except FileNotFoundError:
    print(f"WARNING: dataset not found at {CSV_PATH}. RAG will return no results.")

N = len(rows)
df_counts = Counter()
for toks in doc_tokens:
    df_counts.update(set(toks))
idf = {t: math.log((1 + N) / (1 + c)) + 1 for t, c in df_counts.items()}


def _vectorize(tokens):
    tf = Counter(tokens)
    vec = {t: c * idf[t] for t, c in tf.items() if t in idf}
    norm = math.sqrt(sum(w * w for w in vec.values())) or 1.0
    return vec, norm


doc_vecs = [_vectorize(t) for t in doc_tokens]


def retrieve_context(query, top_k=3):
    if not rows:
        return []
    q_vec, q_norm = _vectorize(_tokenize(query))
    scored = []
    for i, (d_vec, d_norm) in enumerate(doc_vecs):
        dot = sum(w * d_vec.get(t, 0.0) for t, w in q_vec.items())
        scored.append((dot / (q_norm * d_norm), i))
    scored.sort(reverse=True)

    results = []
    for score, i in scored[:top_k]:
        row = rows[i]
        results.append({
            "product": row.get("product", ""),
            "description": row.get("description", ""),
            "target_audience": row.get("target_audience", ""),
            "platform": row.get("platform", ""),
            "tone": row.get("tone", ""),
            "keywords": row.get("keywords", ""),
            "brand_style": row.get("brand_style", ""),
            "similarity": float(score),
        })
    return results
