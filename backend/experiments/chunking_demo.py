
from langchain_text_splitters import RecursiveCharacterTextSplitter

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

splitter = RecursiveCharacterTextSplitter(
    chunk_size=150,
    chunk_overlap=30,
    separators=["\n\n", "\n", ", ", " ", ""]
)

chunks = splitter.split_text(resume_text)

print("Total chunks:", len(chunks))

for i, chunk in enumerate(chunks):
    print(f"\nChunk {i + 1}:")
    print(chunk)
