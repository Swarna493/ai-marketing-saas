import csv
import re
import os


# Load marketing dataset
DATASET_PATH = os.path.join(
    os.path.dirname(__file__),
    "dataset",
    "marketing_dataset.csv"
)

data = []

try:
    with open(DATASET_PATH, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        data = list(reader)
except Exception as e:
    print("Dataset loading error:", e)


def retrieve_context(query, top_k=3):
    """
    Lightweight RAG retrieval.
    Finds the most relevant dataset rows using keyword matching.
    Does not require pandas, NumPy, PyTorch, or sentence-transformers.
    """

    query_words = set(
        re.findall(r"\w+", str(query).lower())
    )

    scores = []

    for index, row in enumerate(data):

        text = " ".join([
            str(row.get("product", "")),
            str(row.get("category", "")),
            str(row.get("description", "")),
            str(row.get("target_audience", "")),
            str(row.get("platform", "")),
            str(row.get("tone", "")),
            str(row.get("keywords", "")),
            str(row.get("brand_style", ""))
        ]).lower()

        text_words = set(
            re.findall(r"\w+", text)
        )

        # Count matching words
        matching_words = query_words.intersection(text_words)
        score = len(matching_words)

        scores.append((score, index))

    # Highest matching score first
    scores.sort(
        key=lambda item: item[0],
        reverse=True
    )

    results = []

    for score, index in scores[:top_k]:

        row = data[index]

        results.append({
            "product": row.get("product", ""),
            "description": row.get("description", ""),
            "target_audience": row.get("target_audience", ""),
            "platform": row.get("platform", ""),
            "tone": row.get("tone", ""),
            "keywords": row.get("keywords", ""),
            "brand_style": row.get("brand_style", ""),
            "similarity": float(score)
        })

    return results