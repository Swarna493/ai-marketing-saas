import csv
import math
import os
import re
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_PATH = os.path.join(
    BASE_DIR,
    "dataset",
    "marketing_dataset.csv"
)

FIELDS = [
    "product",
    "category",
    "description",
    "target_audience",
    "platform",
    "tone",
    "keywords",
    "brand_style"
]


def _tokenize(text):
    return re.findall(
        r"[a-z0-9]+",
        str(text).lower()
    )


# =========================================================
# CSV DATASET
# =========================================================

rows = []
doc_tokens = []

try:
    with open(
        CSV_PATH,
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            rows.append(row)

            text = " ".join(
                (row.get(field) or "")
                for field in FIELDS
            )

            doc_tokens.append(
                _tokenize(text)
            )

except FileNotFoundError:

    print(
        f"WARNING: Dataset not found: {CSV_PATH}"
    )


# =========================================================
# TF-IDF
# =========================================================

N = len(rows)

df_counts = Counter()

for tokens in doc_tokens:
    df_counts.update(set(tokens))


idf = {
    token: math.log(
        (1 + N) / (1 + count)
    ) + 1

    for token, count in df_counts.items()
}


def _vectorize(tokens):

    tf = Counter(tokens)

    vector = {
        token: count * idf[token]
        for token, count in tf.items()
        if token in idf
    }

    norm = math.sqrt(
        sum(
            weight * weight
            for weight in vector.values()
        )
    ) or 1.0

    return vector, norm


doc_vecs = [
    _vectorize(tokens)
    for tokens in doc_tokens
]


# =========================================================
# CSV RETRIEVAL
# =========================================================

def retrieve_context(query, top_k=3):

    if not rows:
        return []

    query_vector, query_norm = _vectorize(
        _tokenize(query)
    )

    scored = []

    for index, (doc_vector, doc_norm) in enumerate(
        doc_vecs
    ):

        dot_product = sum(
            weight * doc_vector.get(
                token,
                0.0
            )
            for token, weight
            in query_vector.items()
        )

        similarity = (
            dot_product /
            (query_norm * doc_norm)
        )

        scored.append(
            (
                similarity,
                index
            )
        )

    scored.sort(reverse=True)

    results = []

    for similarity, index in scored[:top_k]:

        row = rows[index]

        results.append({

            "product": row.get(
                "product",
                ""
            ),

            "description": row.get(
                "description",
                ""
            ),

            "target_audience": row.get(
                "target_audience",
                ""
            ),

            "platform": row.get(
                "platform",
                ""
            ),

            "tone": row.get(
                "tone",
                ""
            ),

            "keywords": row.get(
                "keywords",
                ""
            ),

            "brand_style": row.get(
                "brand_style",
                ""
            ),

            "similarity": float(similarity)
        })

    return results


# =========================================================
# PDF RAG
# =========================================================

pdf_chunks = []


def set_pdf_chunks(chunks):

    global pdf_chunks

    pdf_chunks = chunks or []


def clear_pdf_chunks():

    global pdf_chunks

    pdf_chunks = []


def get_pdf_chunk_count():

    return len(pdf_chunks)


def retrieve_pdf_context(query, top_k=3):

    if not pdf_chunks:
        return []

    query_tokens = set(
        _tokenize(query)
    )

    if not query_tokens:
        return []

    scored = []

    for index, chunk in enumerate(
        pdf_chunks
    ):

        chunk_tokens = set(
            _tokenize(chunk)
        )

        if not chunk_tokens:
            continue

        common_words = (
            query_tokens.intersection(
                chunk_tokens
            )
        )

        denominator = math.sqrt(
            len(query_tokens) *
            len(chunk_tokens)
        )

        if denominator == 0:
            score = 0.0
        else:
            score = (
                len(common_words) /
                denominator
            )

        scored.append(
            (
                score,
                index
            )
        )

    scored.sort(reverse=True)

    results = []

    for score, index in scored[:top_k]:

        results.append({
            "text": pdf_chunks[index],
            "similarity": float(score)
        })

    return results


def get_pdf_context_text(query, top_k=3):

    results = retrieve_pdf_context(
        query,
        top_k
    )

    if not results:
        return ""

    return "\n\n".join(
        result["text"]
        for result in results
    )


# =========================================================
# COMBINED CSV + PDF RAG
# =========================================================

def get_combined_context(
    query,
    csv_top_k=2,
    pdf_top_k=3
):

    csv_results = retrieve_context(
        query,
        csv_top_k
    )

    pdf_results = retrieve_pdf_context(
        query,
        pdf_top_k
    )

    context_parts = []

    if csv_results:

        context_parts.append(
            "MARKETING DATASET CONTEXT:"
        )

        for item in csv_results:

            context_parts.append(
                f"""
Product: {item["product"]}
Description: {item["description"]}
Target Audience: {item["target_audience"]}
Platform: {item["platform"]}
Tone: {item["tone"]}
Keywords: {item["keywords"]}
Brand Style: {item["brand_style"]}
"""
            )

    if pdf_results:

        context_parts.append(
            "UPLOADED PDF CONTEXT:"
        )

        for index, item in enumerate(
            pdf_results,
            start=1
        ):

            context_parts.append(
                f"""
PDF Context {index}:
{item["text"]}
"""
            )

    return "\n".join(context_parts)