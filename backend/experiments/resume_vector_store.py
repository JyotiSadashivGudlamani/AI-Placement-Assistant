
from pathlib import Path
import chromadb

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# --------------------------------
# 1. Define project paths
# --------------------------------

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent

PDF_PATH = BASE_DIR / "sample_resume.pdf"
CHROMA_PATH = BACKEND_DIR / "chroma_db"

if not PDF_PATH.exists():
    raise FileNotFoundError(f"Resume PDF not found: {PDF_PATH}")

# --------------------------------
# 2. Extract PDF text
# --------------------------------

reader = PdfReader(str(PDF_PATH))

resume_text = ""

for page in reader.pages:
    text = page.extract_text()
    if text:
        resume_text += text + "\n"

if not resume_text.strip():
    raise ValueError("No readable text found in the PDF.")

print("PDF text extracted successfully!")

# --------------------------------
# 3. Split text into chunks
# --------------------------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)

chunks = splitter.split_text(resume_text)

print("Total chunks:", len(chunks))

# --------------------------------
# 4. Load embedding model
# --------------------------------

print("Loading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

# --------------------------------
# 5. Generate embeddings
# --------------------------------

embeddings = model.encode(chunks).tolist()

print("Embeddings generated!")
print("Number of embeddings:", len(embeddings))
print("Embedding dimensions:", len(embeddings[0]))

# --------------------------------
# 6. Connect to ChromaDB
# --------------------------------

client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)

collection = client.get_or_create_collection(
    name="uploaded_resume_collection",
    metadata={"hnsw:space": "cosine"}
)

# Remove old chunks from this PDF before re-inserting
collection.delete(
    where={"source": PDF_PATH.name}
)

# --------------------------------
# 7. Store chunks and embeddings
# --------------------------------

ids = [
    f"resume_chunk_{i}"
    for i in range(len(chunks))
]

metadatas = [
    {
        "source": PDF_PATH.name,
        "chunk_number": i + 1
    }
    for i in range(len(chunks))
]

collection.add(
    ids=ids,
    documents=chunks,
    embeddings=embeddings,
    metadatas=metadatas
)

print("\nResume stored successfully in ChromaDB!")
print("Stored records:", collection.count())

# --------------------------------
# 8. Test semantic search
# --------------------------------

question = "What is Jyoti's educational qualification?"

query_embedding = model.encode([question]).tolist()

results = collection.query(
    query_embeddings=query_embedding,
    n_results=3
)

print("\nSemantic Search Results:")

for document, metadata in zip(
    results["documents"][0],
    results["metadatas"][0]
):
    print("\nRetrieved chunk:")
    print(document)
    print("Metadata:", metadata)
