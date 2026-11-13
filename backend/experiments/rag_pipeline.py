
import chromadb
import requests

from sentence_transformers import SentenceTransformer


# 1. Load the embedding model
print("Loading embedding model...")

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# 2. Connect to existing ChromaDB
client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_collection(
    name="resume_collection"
)

print("Connected to ChromaDB!")
print("Stored records:", collection.count())


# 3. Ollama API configuration
OLLAMA_URL = "http://localhost:11434/api/chat"

MODEL_NAME = "llama3.2:3b"


# 4. Function to retrieve relevant documents
def retrieve_context(question):

    question_embedding = embedding_model.encode(
        [question]
    ).tolist()

    results = collection.query(
        query_embeddings=question_embedding,
        n_results=4
    )

    documents = results["documents"][0]

    context = "\n\n".join(documents)

    return context


# 5. Function to generate an answer using Ollama
def generate_answer(question, context):

    prompt = f"""
You are an AI Placement Assistant.

Answer the user's question using only the information
provided in the context.

If the answer is not available in the context,
say that the information is not available in the resume.

Context:
{context}

User Question:
{question}

Answer:
"""

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
        timeout=120
    )

    response.raise_for_status()

    result = response.json()

    return result["message"]["content"]


# 6. Complete RAG pipeline
def rag_pipeline(question):

    print("\nUSER QUESTION:")
    print(question)

    # Retrieve information from ChromaDB
    context = retrieve_context(question)

    print("\nRETRIEVED CONTEXT:")
    print(context)

    # Generate answer using Llama 3.2
    answer = generate_answer(question, context)

    print("\nGENERATED ANSWER:")
    print(answer)


# 7. Test the RAG application
if __name__ == "__main__":

    question = input(
        "\nAsk a question about Jyoti's resume: "
    )

    rag_pipeline(question)
