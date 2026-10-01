import pandas as pd
import re

df = pd.read_csv("dataset/marketing_dataset.csv")


def retrieve_context(query, top_k=3):
    query_words = set(re.findall(r"\w+", query.lower()))

    scores = []

    for index, row in df.iterrows():
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

        text_words = set(re.findall(r"\w+", text))

        score = len(query_words.intersection(text_words))
        scores.append((score, index))

    scores.sort(reverse=True)

    results = []

    for score, index in scores[:top_k]:
        row = df.iloc[index]

        results.append({
            "product": row["product"],
            "description": row["description"],
            "target_audience": row["target_audience"],
            "platform": row["platform"],
            "tone": row["tone"],
            "keywords": row["keywords"],
            "brand_style": row["brand_style"],
            "similarity": float(score)
        })

    return results