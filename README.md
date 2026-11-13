# AI Placement Preparation Assistant

An intelligent, multi-tenant AI placement readiness platform designed to accelerate student preparation for campus recruitments, technical rounds, coding tests, and HR interviews.

Featuring a **hybrid retrieval-augmented generation (RAG) engine** (BM25 keyword search + ChromaDB vector embeddings + Cross-Encoder reranking), an **autonomous LangGraph agent workflow**, **Bcrypt/JWT multi-tenant security**, and a **modern React + Tailwind CSS dashboard**.

---

## 1. Project Overview

Preparing for campus placements requires students to juggle multiple preparation tracks: core computer science fundamentals, coding problem-solving, company-specific job description alignment, resume structuring, aptitude practice, and mock interviews.

The **AI Placement Preparation Assistant** serves as an interactive personal mentor:
- Ingests college syllabi, lecture notes, textbooks, and past interview transcripts in PDF, DOCX, and TXT formats.
- Retains authentic document citations (filename, page numbers, exact text chunks) without LLM hallucinations.
- Automatically routes complex student requests using an autonomous LangGraph decision agent.
- Evaluates mock interviews on a 5-dimension rubric (*Correctness, Relevance, Completeness, Clarity, Communication*).
- Delivers real-time analytics, readiness metrics, and AI-prioritized study recommendations.

---

## 2. Features

### A. Document Ingestion & Hybrid RAG Engine
- **Multi-Format Extraction:** High-performance PDF parsing with PyMuPDF, table and paragraph extraction with `python-docx`, and raw text handling.
- **Accurate Page-Preserving Chunking:** Recursive text chunker preserves PDF page numbers and structural headings.
- **Dense Vector Search:** Generates 384-dimensional embeddings via `sentence-transformers/all-MiniLM-L6-v2` stored in ChromaDB.
- **Advanced Retrieval & Fusion:** Combines BM25 keyword matching with dense semantic search using Reciprocal Rank Fusion (RRF) and Cross-Encoder reranking.
- **Citation-Guaranteed Answering:** Sources every answer with verified file names and page indices.

### B. Placement Preparation Modules
- **Technical Interview Simulator:** Covers 11 CS domains (Java, Python, C/C++, OOP, DSA, DBMS, SQL, Operating Systems, Computer Networks, AI/ML, and LLM/RAG) with configurable difficulty levels (Easy, Medium, Hard).
- **Personalized HR Interview Guidance:** Drafts authentic answers for standard behavioral questions (Self-introduction, Strengths/Weaknesses, Career Goals, Teamwork, Conflict Resolution) without fabricating facts.
- **Interactive Aptitude Testing:** Real-time MCQs across Quantitative Aptitude, Logical Reasoning, and Verbal Ability with instant explanations and score tracking.
- **Resume Analyzer:** Extracts technical skills, education, internships, projects, and ATS formatting recommendations from uploaded resumes.
- **Job Description (JD) Matcher:** Calculates job match percentages, identifies missing technical keywords, and provides concrete tailoring suggestions.
- **Mock Interview Evaluator:** Conducts role-specific technical and behavioral interviews, providing automated rubric scores (out of 10) across 5 core criteria.

### C. Autonomous LangGraph Agent Workflow
- **Intent Classification Node:** Categorizes student queries into RAG QA, Resume Analysis, Job Description Matching, Technical Prep, HR Prep, Mock Interview, Aptitude, or General Chat.
- **Tool Calling Node:** Dispatches requests to specialized internal services without duplicating business logic.
- **Synthesizer & Fallback Nodes:** Formulates structured conversational outputs with multi-turn memory while politely redirecting off-topic queries.

### D. User Management & Multi-Tenant Isolation
- **Secure Password Hashing:** Salted bcrypt hashing with 12 rounds. Plain-text passwords are never stored.
- **JWT Authorization:** HS256 signed bearer tokens with 24-hour expiration.
- **Isolated Storage:** Documents, vector embeddings, and conversation histories are strictly scoped by `user_id`. Attempting to access foreign documents returns `HTTP 403 Forbidden`.

### E. Analytics Dashboard
- Visualizes indexed documents, answered questions, CS fundamentals mastery, and aptitude readiness.
- AI-driven recommendation cards prioritize weak subjects and suggest immediate study actions.

---

## 3. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | Python 3.13, FastAPI 0.115+, Pydantic v2, Uvicorn |
| **Agentic AI & Orchestration** | LangGraph 0.2+, LangChain Core |
| **Local LLM Engine** | Ollama with `llama3.2:3b` |
| **Embeddings & Vector Storage** | Sentence Transformers (`all-MiniLM-L6-v2`), ChromaDB 0.5+ |
| **Hybrid Search & Reranking** | Rank-BM25, Scikit-learn, Cross-Encoder |
| **Document Processing** | PyMuPDF (fitz), python-docx |
| **Database & Persistence** | MongoDB Community Server 7.0+, PyMongo 4.8+ |
| **Security & Authentication** | Bcrypt 5.0, PyJWT 2.15 |
| **Frontend Framework** | React 19, Vite, Tailwind CSS v4, Lucide React, Axios |
| **Testing** | Pytest, Pytest-Asyncio, Vitest, Testing Library |
| **DevOps & Containers** | Docker, Docker Compose, Nginx Alpine |

---

## 4. Architecture Diagram

```
+---------------------------------------------------------------------------------+
|                                 REACT FRONTEND (Vite)                           |
|       Dashboard  |  Document Manager  |  Agentic Chat  |  Technical Prep        |
|       HR Guide   |  Aptitude Quiz     |  Resume Review |  Mock Interview        |
+----------------------------------------+----------------------------------------+
                                         |  HTTP / Bearer JWT
                                         v
+---------------------------------------------------------------------------------+
|                             FASTAPI BACKEND GATEWAY                             |
|  [/auth]       [/documents]     [/chat]        [/agent]       [/analytics]      |
|  [/technical]  [/hr]            [/aptitude]    [/resume]      [/mock-interview] |
+----------------------------------------+----------------------------------------+
         |                               |                               |
         v                               v                               v
+-------------------+          +-------------------+          +-------------------+
|  LANGGRAPH AGENT  |          | HYBRID RAG ENGINE |          |  PERSISTENCE & DB |
|  - Classifier     |          | - PyMuPDF Loader  |          | - MongoDB (Users, |
|  - Tool Router    |          | - ChromaDB (Dense)|          |   Scores, History)|
|  - Synthesizer    |          | - BM25 (Sparse)   |          | - Bcrypt Passwords|
|  - Multi-Turn Mem |          | - RRF & Reranker  |          | - JWT Validation  |
+---------+---------+          +---------+---------+          +-------------------+
          |                              |
          +--------------+---------------+
                         | HTTP Prompts
                         v
              +---------------------+
              |    OLLAMA SERVER    |
              |    (llama3.2:3b)    |
              +---------------------+
```

---

## 5. Folder Structure

```
AI-Placement-Assistant/
├── backend/
│   ├── app/
│   │   ├── core/                  # Configuration, security, deps, logging
│   │   │   ├── config.py
│   │   │   ├── deps.py
│   │   │   ├── logger.py
│   │   │   └── security.py
│   │   ├── db/                    # MongoDB manager and models
│   │   │   └── mongo.py
│   │   ├── routers/               # Modular FastAPI endpoints
│   │   │   ├── agent.py
│   │   │   ├── analytics.py
│   │   │   ├── aptitude.py
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── documents.py
│   │   │   ├── hr.py
│   │   │   ├── jd.py
│   │   │   ├── mock_interview.py
│   │   │   ├── resume.py
│   │   │   └── technical.py
│   │   ├── schemas/               # Pydantic request/response schemas
│   │   ├── services/              # Core business logic
│   │   │   ├── agent/             # LangGraph state graph and nodes
│   │   │   ├── chunking.py
│   │   │   ├── document_loader.py
│   │   │   ├── embeddings.py
│   │   │   ├── hybrid_retriever.py
│   │   │   ├── mock_interview.py
│   │   │   ├── ollama_client.py
│   │   │   ├── technical_prep.py
│   │   │   └── vector_store.py
│   │   └── main.py                # Application entrypoint & lifespan
│   ├── tests/                     # Comprehensive test suites (Phases 1-7)
│   ├── Dockerfile                 # Backend container definition
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── api/                   # Axios client and service endpoints
│   │   ├── components/            # Reusable UI widgets & modals
│   │   ├── context/               # Auth and Theme providers
│   │   ├── pages/                 # Full-page views
│   │   ├── test/                  # Vitest frontend component tests
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile                 # Multi-stage production container
│   ├── nginx.conf                 # SPA routing & reverse proxy
│   └── package.json               # Node.js dependencies
├── docker-compose.yml             # Full-stack container orchestration
├── pytest.ini                     # Pytest runner configuration
├── requirements.txt               # Root Python dependencies
├── .env.example                   # Environment configuration template
└── README.md                      # Project documentation
```

---

## 6. Installation Instructions

### Prerequisites
- **Python 3.11 – 3.13** installed and added to `PATH`.
- **Node.js 18+** and `npm` installed.
- **Ollama** installed with `llama3.2:3b`.
- **MongoDB Community Server 7.0+** running locally on port 27017 (or MongoDB Atlas).

### Clone & Environment Setup
```bash
git clone https://github.com/<your-username>/AI-Placement-Assistant.git
cd AI-Placement-Assistant

# Copy environment configuration
cp .env.example .env
```

---

## 7. Windows Setup Instructions

### 1. Create Python Virtual Environment
```powershell
python -m venv backend\venv
.\backend\venv\Scripts\Activate.ps1
```

### 2. Install Python Dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies
```powershell
cd frontend
npm install
cd ..
```

---

## 8. Backend Execution

Activate the virtual environment and launch Uvicorn:

```powershell
.\backend\venv\Scripts\Activate.ps1
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

- API Base URL: `http://127.0.0.1:8000`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`
- ReDoc Documentation: `http://127.0.0.1:8000/redoc`

---

## 9. Frontend Execution

From the `frontend` folder:

```powershell
cd frontend
npm run dev
```

- Web Application: `http://localhost:5173`

---

## 10. Ollama Setup

1. Download and install Ollama from [ollama.com](https://ollama.com/download).
2. Start the Ollama background daemon.
3. Pull the required 3-billion parameter Llama model:
   ```bash
   ollama pull llama3.2:3b
   ```
4. Verify local model availability:
   ```bash
   ollama list
   ```
5. Test direct inference:
   ```bash
   curl http://localhost:11434/api/generate -d '{"model": "llama3.2:3b", "prompt": "Explain polymorphism in Java", "stream": false}'
   ```

---

## 11. MongoDB Setup

1. Install MongoDB Community Server from [mongodb.com](https://www.mongodb.com/try/download/community).
2. Ensure the MongoDB service is running on `mongodb://localhost:27017`.
   ```powershell
   Get-Service -Name MongoDB
   # Or start manually:
   net start MongoDB
   ```
3. The application automatically initializes necessary collections and unique indexes upon first boot.

---

## 12. API Documentation

| Group | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **System** | `GET` | `/` | API version, documentation links, and registered routes |
| **System** | `GET` | `/health` | Subsystem health probe (ChromaDB, Ollama, MongoDB, Models) |
| **Auth** | `POST` | `/auth/register` | Register student, hash password with bcrypt, issue JWT |
| **Auth** | `POST` | `/auth/login` | Authenticate student credentials, issue JWT |
| **Auth** | `GET` | `/auth/me` | Fetch authenticated student profile |
| **Analytics**| `GET` | `/analytics/dashboard` | Placement stats, topic breakdown, and recommendations |
| **Documents**| `POST` | `/documents/upload` | Upload & index PDF, DOCX, or TXT into ChromaDB |
| **Documents**| `GET` | `/documents` | List uploaded documents scoped to current user |
| **Documents**| `DELETE` | `/documents/{id}` | Purge document metadata and ChromaDB vectors |
| **Chat RAG** | `POST` | `/chat` | Context-grounded RAG QA with page-level citations |
| **Chat RAG** | `GET` | `/chats` | Retrieve conversation sessions for authenticated user |
| **Agent** | `POST` | `/agent/chat` | Autonomous LangGraph multi-tool placement assistant |
| **Agent** | `GET` | `/agent/workflow` | Inspect LangGraph nodes, routing edges, and registered tools |
| **Technical**| `POST` | `/technical/generate` | Generate topic-specific technical interview questions |
| **HR** | `POST` | `/hr/draft` | Draft authentic behavioral interview responses |
| **Aptitude** | `POST` | `/aptitude/evaluate` | Submit MCQ test attempt and calculate performance |
| **Resume** | `POST` | `/resume/analyze` | Parse resume PDF/DOCX for ATS score and skills |
| **JD Match** | `POST` | `/jd/match` | Compare resume against job description requirements |
| **Mock** | `POST` | `/mock-interview/evaluate`| Evaluate interview response across 5 rubric criteria |

---

## 13. Testing Instructions

### Run Backend Tests (Pytest)
Execute all test suites with verbose output:

```powershell
.\backend\venv\Scripts\Activate.ps1
pytest backend/tests/ -v
```

Run a specific phase:
```powershell
pytest backend/tests/test_phase7.py -v
```

### Run Frontend Tests (Vitest)
```powershell
cd frontend
npm test
```

### Run Frontend Linting
```powershell
cd frontend
npm run lint
```

---

## 14. Docker Deployment

The application includes complete container definitions and multi-container orchestration.

### Build and Launch Full Stack
```bash
docker compose up --build -d
```

### Reaching Ollama on Windows Host
When running in Docker, the backend container reaches Ollama running on your Windows host via `http://host.docker.internal:11434`. The `docker-compose.yml` file includes:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

### Container Endpoints:
- **Frontend:** `http://localhost:80`
- **Backend API:** `http://localhost:8000`
- **MongoDB:** `localhost:27017`

---

## 15. Screenshots Section

*(Place UI screenshots in `docs/screenshots/` and link them here)*

- **Dashboard:** Comprehensive readiness overview with metrics and topic recommendations.
- **Agentic Chat:** Multi-turn autonomous assistant routing technical questions and document queries.
- **Mock Interview Simulator:** Dynamic role selection, rubric evaluation, and criteria feedback.
- **Aptitude Practice:** Timed MCQ interface with instant explanations.

---

## 16. Future Improvements

1. **Audio Speech-to-Text:** Integrate Whisper API or local faster-whisper for spoken voice mock interviews.
2. **Coding Sandbox:** Interactive in-browser Python and Java code execution environment with automated test suites.
3. **Company-Specific Placement Question Banks:** Curated sets of questions asked by top recruiters (Google, Microsoft, Amazon, TCS, Infosys, Wipro).
4. **WebSocket Streaming:** Real-time token streaming for chat generation and interview feedback.
