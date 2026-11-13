
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Sample resume data
resume_text = """
Jyoti is a Computer Science Engineering student.

Technical Skills:
Java, Python, C++, HTML, CSS, JavaScript,
React.js, Node.js, Express.js, MongoDB and MySQL.

Projects:
AI Placement Assistant using Python, FastAPI,
Sentence Transformers and ChromaDB.

Internship:
Learning RAG, LLMs, embeddings, FastAPI,
Docker and AI agents.
"""

# 2. Split text into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=150,
    chunk_overlap=30,
    separators=["\n\n", "\n", ", ", " ", ""]
)

chunks = splitter.split_text(resume_text)

print("Total chunks:", len(chunks))

# 3. Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

embeddings = model.encode(chunks).tolist()

# 4. Create persistent ChromaDB database
client = chromadb.PersistentClient(
    path="./chroma_db"
)

# 5. Create collection
collection = client.get_or_create_collection(
    name="resume_collection",
    metadata={"hnsw:space": "cosine"}
)

# 6. Store chunks and embeddings
ids = [f"resume_chunk_{i}" for i in range(len(chunks))]

metadatas = [
    {
        "source": "resume",
        "chunk_number": i + 1
    }
    for i in range(len(chunks))
]

collection.upsert(
    ids=ids,
    documents=chunks,
    embeddings=embeddings,
    metadatas=metadatas
)

print("\nSuccessfully stored data in ChromaDB!")
print("Total stored records:", collection.count())


# 7. Search and retrieve relevant chunks

queries = [
    "What programming languages does Jyoti know?",
    "Which projects has Jyoti developed?",
    "What is Jyoti learning during her internship?"
]

for query in queries:

    print("\nUSER QUESTION:", query)

    # Convert user question into embedding
    query_embedding = model.encode([query]).tolist()

    # Search ChromaDB
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=4
    )

    print("\nRETRIEVED CONTEXT:")

    for i, document in enumerate(results["documents"][0]):

        distance = results["distances"][0][i]
        similarity = 1 - distance
        metadata = results["metadatas"][0][i]

        print(f"\nRank: {i + 1}")
        print(f"Similarity: {similarity:.4f}")
        print(f"Metadata: {metadata}")
        print(f"Content: {document}")

    print("=" * 60)

