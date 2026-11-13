
from io import BytesIO
from uuid import uuid4
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

import chromadb
import requests
import traceback


# =====================================================
# 1. CREATE FASTAPI APPLICATION
# =====================================================

app = FastAPI(
    title="AI Placement Assistant",
    description="Resume-based AI question answering using RAG",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# 2. LOAD EMBEDDING MODEL
# =====================================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Embedding model loaded successfully!")


# =====================================================
# 3. CONNECT TO CHROMADB
# =====================================================

database_path = Path(__file__).resolve().parent / "chroma_db"

client = chromadb.PersistentClient(
    path=str(database_path)
)

collection = client.get_collection(
    name="resume_collection"
)

upload_collection = client.get_or_create_collection(
    name="uploaded_resume_collection",
    metadata={"hnsw:space": "cosine"}
)

# Stores the latest uploaded PDF ID during this server session
latest_upload_id = None

print("Connected to ChromaDB!")
print("Original records:", collection.count())
print("Uploaded records:", upload_collection.count())


# =====================================================
# 4. OLLAMA CONFIGURATION
# =====================================================

OLLAMA_URL = "http://localhost:11434/api/chat"

MODEL_NAME = "llama3.2:3b"


# =====================================================
# 5. DEFINE REQUEST STRUCTURE
# =====================================================

class ChatRequest(BaseModel):
    question: str


# =====================================================
# 6. RETRIEVE RELEVANT CONTEXT
# =====================================================

def retrieve_context(question: str):

    global latest_upload_id

    print("\n================================")
    print("RETRIEVAL STARTED")
    print("Question:", question)
    print("Latest Upload ID:", latest_upload_id)
    print("Total Uploaded Records:", upload_collection.count())
    print("================================")

    summary_keywords = [
        "summarize",
        "summarise",
        "summary",
        "overview",
        "whole resume",
        "entire resume",
        "complete resume",
        "full resume"
    ]

    question_lower = question.lower()

    is_summary = any(
        keyword in question_lower
        for keyword in summary_keywords
    )

    # -------------------------------------------------
    # CASE 1: COMPLETE PDF SUMMARY
    # -------------------------------------------------

    if is_summary and latest_upload_id:

        results = upload_collection.get(
            where={"upload_id": latest_upload_id},
            include=["documents", "metadatas"]
        )

        documents = results["documents"] or []
        metadatas = results["metadatas"] or []

        # Sort chunks according to original PDF order
        sorted_chunks = sorted(
            zip(metadatas, documents),
            key=lambda item: item[0]["chunk_number"]
        )

        context = "\n\n".join(
            document
            for metadata, document in sorted_chunks
        )

        print("Summary retrieval selected")
        print("Retrieved chunks:", len(documents))

        if not context.strip():
            return "No readable content found in the uploaded PDF."

        return context

    # -------------------------------------------------
    # CASE 2: NORMAL QUESTION ABOUT UPLOADED PDF
    # -------------------------------------------------

    if latest_upload_id:

        # Get records belonging to the latest upload
        filtered_records = upload_collection.get(
            where={"upload_id": latest_upload_id},
            include=["metadatas"]
        )

        available_count = len(filtered_records["ids"])

        print("Available latest-upload chunks:", available_count)

        if available_count == 0:
            return "No uploaded resume data found."

        # Convert question into embedding
        question_embedding = embedding_model.encode(
            [question]
        ).tolist()

        # Search relevant chunks
        results = upload_collection.query(
            query_embeddings=question_embedding,
            n_results=min(4, available_count),
            where={"upload_id": latest_upload_id}
        )

        documents = results["documents"][0] or []

    # -------------------------------------------------
    # CASE 3: ORIGINAL SAMPLE RESUME
    # -------------------------------------------------

    else:

        available_count = collection.count()

        if available_count == 0:
            return "No resume data found."

        question_embedding = embedding_model.encode(
            [question]
        ).tolist()

        results = collection.query(
            query_embeddings=question_embedding,
            n_results=min(4, available_count)
        )

        documents = results["documents"][0] or []

    # Remove duplicate chunks
    unique_documents = list(dict.fromkeys(documents))

    context = "\n\n".join(unique_documents)

    print("Normal retrieval selected")
    print("Retrieved chunks:", len(unique_documents))

    return context


# =====================================================
# 7. GENERATE ANSWER USING OLLAMA
# =====================================================

def generate_answer(question: str, context: str):

    prompt = f"""
You are an intelligent AI Placement Assistant.

The context below contains text extracted from the user's resume PDF.

Answer the user's question using only the provided context.

IMPORTANT INSTRUCTIONS:

1. For summary questions, summarize all important sections.
2. Organize the answer using headings and bullet points.
3. Do not repeat the same information unnecessarily.
4. Never claim that you cannot access the PDF.
5. Do not invent skills, qualifications, projects or experience.
6. If information is missing, clearly mention that it is
   not available in the provided context.
7. Use simple and professional English.
8. Distinguish internship experience from academic projects.

Context:
{context}

Question:
{question}

Answer:
"""

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False
            },
            timeout=180
        )

        response.raise_for_status()

        result = response.json()

        return result["message"]["content"]

    except requests.RequestException as error:

        print("OLLAMA CONNECTION ERROR:")
        traceback.print_exc()

        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to Ollama: {error}"
        )

    except (KeyError, ValueError) as error:

        print("OLLAMA RESPONSE ERROR:")
        traceback.print_exc()

        raise HTTPException(
            status_code=502,
            detail=f"Invalid response received from Ollama: {error}"
        )


# =====================================================
# 8. HOME ENDPOINT
# =====================================================

@app.get("/")
def home():

    return {
        "message": "Welcome to AI Placement Assistant API",
        "status": "Running"
    }


# =====================================================
# 9. CHAT ENDPOINT
# =====================================================

@app.post("/chat")
def chat(request: ChatRequest):

    try:

        question = request.question.strip()

        if not question:

            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty"
            )

        print("\nCHAT REQUEST RECEIVED")

        # Step 1: Retrieve context
        context = retrieve_context(question)

        print("Context retrieved successfully!")

        if not context.strip():

            raise HTTPException(
                status_code=404,
                detail="No relevant resume information found."
            )

        # Step 2: Generate answer
        answer = generate_answer(
            question,
            context
        )

        print("Answer generated successfully!")

        return {
            "question": question,
            "retrieved_context": context,
            "answer": answer
        }

    except HTTPException:
        raise

    except Exception as error:

        print("\nCHAT ERROR:")
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(error)}"
        )


# =====================================================
# 10. UPLOAD PDF ENDPOINT
# =====================================================

@app.post("/upload")
async def upload_resume(file: UploadFile = File(...)):

    global latest_upload_id

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    # Read uploaded PDF
    file_bytes = await file.read()

    if not file_bytes:

        raise HTTPException(
            status_code=400,
            detail="Uploaded PDF is empty."
        )

    try:

        reader = PdfReader(BytesIO(file_bytes))

        resume_text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                resume_text += page_text + "\n"

    except Exception as error:

        print("PDF EXTRACTION ERROR:")
        traceback.print_exc()

        raise HTTPException(
            status_code=400,
            detail=f"Could not read the uploaded PDF: {str(error)}"
        )

    if not resume_text.strip():

        raise HTTPException(
            status_code=400,
            detail="No readable text found in the PDF."
        )

    print("PDF text extracted successfully!")

    # -------------------------------------------------
    # SPLIT RESUME INTO CHUNKS
    # -------------------------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50
    )

    chunks = splitter.split_text(resume_text)

    if not chunks:

        raise HTTPException(
            status_code=400,
            detail="Could not generate chunks from the PDF."
        )

    print("Total chunks generated:", len(chunks))

    # -------------------------------------------------
    # GENERATE EMBEDDINGS
    # -------------------------------------------------

    embeddings = embedding_model.encode(
        chunks
    ).tolist()

    print("Embeddings generated successfully!")

    # -------------------------------------------------
    # GENERATE UNIQUE UPLOAD ID
    # -------------------------------------------------

    upload_id = str(uuid4())

    # Update latest uploaded PDF
    latest_upload_id = upload_id

    ids = [
        f"{upload_id}_{i}"
        for i in range(len(chunks))
    ]

    # -------------------------------------------------
    # STORE DATA IN CHROMADB
    # -------------------------------------------------

    try:

        upload_collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=[
                {
                    "source": file.filename,
                    "upload_id": upload_id,
                    "chunk_number": i + 1
                }
                for i in range(len(chunks))
            ]
        )

    except Exception as error:

        print("CHROMADB STORAGE ERROR:")
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Could not store resume in ChromaDB: {str(error)}"
        )

    print("\nPDF UPLOADED SUCCESSFULLY!")
    print("Filename:", file.filename)
    print("Upload ID:", latest_upload_id)
    print("Total chunks:", len(chunks))

    return {
        "message": "Resume uploaded successfully!",
        "filename": file.filename,
        "upload_id": upload_id,
        "total_chunks": len(chunks),
        "stored_records": upload_collection.count()
    }





