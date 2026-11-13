
from sentence_transformers import SentenceTransformer, util

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Sample sentences
sentences = [
    "I am learning Python and artificial intelligence.",
    "I want to become a software developer.",
    "Machine learning helps computers learn from data.",
    "I am studying React and web development."
]

# Convert sentences into embeddings
embeddings = model.encode(sentences, convert_to_tensor=True)

# Calculate cosine similarity
similarity_matrix = util.cos_sim(embeddings, embeddings)

print("\nCOSINE SIMILARITY RESULTS\n")

for i in range(len(sentences)):
    for j in range(i + 1, len(sentences)):
        score = similarity_matrix[i][j].item()

        print(f"Sentence {i + 1} vs Sentence {j + 1}")
        print(f"Similarity: {score:.4f}")
        print("-" * 40)

# Search using a query
query = "I want to learn AI and machine learning"

query_embedding = model.encode(query, convert_to_tensor=True)

scores = util.cos_sim(query_embedding, embeddings)[0]

print("\nSEMANTIC SEARCH RESULTS\n")

for index in scores.argsort(descending=True):
    print(f"Score: {scores[index].item():.4f}")
    print(f"Sentence: {sentences[index]}")
    print("-" * 40)
