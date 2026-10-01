import pandas as pd
from sentence_transformers import SentenceTransformer, util

# Load marketing dataset
df = pd.read_csv("dataset/marketing_dataset.csv")

# Combine important fields
df["text"] = (
    df["product"].fillna("").astype(str) + " " +
    df["category"].fillna("").astype(str) + " " +
    df["description"].fillna("").astype(str) + " " +
    df["target_audience"].fillna("").astype(str) + " " +
    df["platform"].fillna("").astype(str) + " " +
    df["tone"].fillna("").astype(str) + " " +
    df["keywords"].fillna("").astype(str) + " " +
    df["brand_style"].fillna("").astype(str)
)

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Create dataset embeddings
texts = df["text"].tolist()
embeddings = model.encode(texts, convert_to_tensor=True)

print("RAG dataset loaded successfully!")
print("Number of records:", len(df))
print("Embedding shape:", embeddings.shape)


# RAG retrieval function
def retrieve_context(query, top_k=3):

    # Convert user query into embedding
    query_embedding = model.encode(
        query,
        convert_to_tensor=True
    )

    # Calculate similarity
    scores = util.cos_sim(query_embedding, embeddings)[0]

    # Get top matching records
    top_results = scores.topk(k=min(top_k, len(df)))

    results = []

    for score, index in zip(top_results.values, top_results.indices):
        row = df.iloc[index.item()]

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


# Test retrieval
query = "eco friendly fashion product for young adults on Instagram"

results = retrieve_context(query)

print("\nRetrieved Marketing Context:")

for result in results:
    print("\nProduct:", result["product"])
    print("Description:", result["description"])
    print("Target Audience:", result["target_audience"])
    print("Platform:", result["platform"])
    print("Tone:", result["tone"])
    print("Keywords:", result["keywords"])
    print("Similarity:", round(result["similarity"], 3))