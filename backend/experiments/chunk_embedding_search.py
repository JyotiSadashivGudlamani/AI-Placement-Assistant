
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer, util

# 1. Sample resume
resume = """
Jyoti is a Computer Science Engineering student.

Technical Skills:
Java, Python, C++, HTML, CSS, JavaScript, React.js,
Node.js, Express.js, MongoDB and MySQL.

Projects:
AI Placement Assistant using Python, FastAPI,
Sentence Transformers and ChromaDB.

Internship:
Learning RAG, LLMs, embeddings, FastAPI,
Docker and AI agents.
"""

# 2. Split resume into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,
    chunk_overlap=20
)

chunks = splitter.split_text(resume)

print("Total chunks:", len(chunks))

# 3. Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 4. Generate embeddings
chunk_embeddings = model.encode(
    chunks,
    convert_to_tensor=True
)

print("Embedding shape:", chunk_embeddings.shape)

# 5. User query
query = "Which programming languages does Jyoti know?"

# 6. Generate query embedding
query_embedding = model.encode(
    query,
    convert_to_tensor=True
)

# 7. Calculate similarity scores
scores = util.cos_sim(
    query_embedding,
    chunk_embeddings
)[0]

# 8. Retrieve top 3 chunks
top_results = scores.argsort(descending=True)[:3]

print("\nTOP 3 SEARCH RESULTS\n")

for rank, index in enumerate(top_results, start=1):
    print("Rank:", rank)
    print("Similarity:", round(scores[index].item(), 4))
    print("Relevant chunk:")
    print(chunks[index])
    print("-" * 50)
