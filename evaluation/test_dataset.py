"""
Benchmark Test Dataset for Advanced RAG Evaluation.
Contains 30 diverse placement, technical, resume, and negative verification questions
with ground-truth relevance annotations for precision, recall, and MRR measurement.
"""

from typing import Any, Dict, List

BENCHMARK_QUESTIONS: List[Dict[str, Any]] = [
    # -------------------------------------------------------------
    # Category 1: Java OOP Concepts (Target: java_oop_guide.pdf - Page 1)
    # -------------------------------------------------------------
    {
        "id": 1,
        "question": "How is inheritance declared in Java and what keyword is used?",
        "target_document": "java_oop_guide.pdf",
        "expected_page": 1,
        "expected_keywords": ["extends", "inheritance", "subclass", "superclass"],
        "is_relevant_in_corpus": True,
        "category": "java_oop",
    },
    {
        "id": 2,
        "question": "What is the diamond problem and how does Java avoid it?",
        "target_document": "java_oop_guide.pdf",
        "expected_page": 1,
        "expected_keywords": ["diamond problem", "single inheritance", "superclass"],
        "is_relevant_in_corpus": True,
        "category": "java_oop",
    },
    {
        "id": 3,
        "question": "What is the purpose of the super keyword in Java subclasses?",
        "target_document": "java_oop_guide.pdf",
        "expected_page": 1,
        "expected_keywords": ["super", "constructor", "subclass", "parent"],
        "is_relevant_in_corpus": True,
        "category": "java_oop",
    },
    {
        "id": 4,
        "question": "How does method overriding work in a Java subclass?",
        "target_document": "java_oop_guide.pdf",
        "expected_page": 1,
        "expected_keywords": ["override", "@override", "method overriding", "subclass"],
        "is_relevant_in_corpus": True,
        "category": "java_oop",
    },
    {
        "id": 5,
        "question": "What is the difference between a superclass and a subclass in Java?",
        "target_document": "java_oop_guide.pdf",
        "expected_page": 1,
        "expected_keywords": ["superclass", "subclass", "inherits", "parent"],
        "is_relevant_in_corpus": True,
        "category": "java_oop",
    },
    {
        "id": 6,
        "question": "Explain single inheritance vs multiple inheritance in Java.",
        "target_document": "java_oop_guide.pdf",
        "expected_page": 1,
        "expected_keywords": ["single inheritance", "multiple inheritance", "extends"],
        "is_relevant_in_corpus": True,
        "category": "java_oop",
    },

    # -------------------------------------------------------------
    # Category 2: Java Polymorphism & Interfaces (Target: java_oop_guide.pdf - Page 2)
    # -------------------------------------------------------------
    {
        "id": 7,
        "question": "How is multiple inheritance of type achieved in Java?",
        "target_document": "java_oop_guide.pdf",
        "expected_page": 2,
        "expected_keywords": ["interface", "interfaces", "implements"],
        "is_relevant_in_corpus": True,
        "category": "java_oop",
    },
    {
        "id": 8,
        "question": "What keyword is used to implement an interface in Java?",
        "target_document": "java_oop_guide.pdf",
        "expected_page": 2,
        "expected_keywords": ["implements", "interface"],
        "is_relevant_in_corpus": True,
        "category": "java_oop",
    },
    {
        "id": 9,
        "question": "Explain dynamic method dispatch in Java runtime polymorphism.",
        "target_document": "java_oop_guide.pdf",
        "expected_page": 2,
        "expected_keywords": ["dynamic method dispatch", "polymorphism", "runtime"],
        "is_relevant_in_corpus": True,
        "category": "java_oop",
    },
    {
        "id": 10,
        "question": "What is the definition of an interface contract in Java?",
        "target_document": "java_oop_guide.pdf",
        "expected_page": 2,
        "expected_keywords": ["interface", "contract", "abstract method"],
        "is_relevant_in_corpus": True,
        "category": "java_oop",
    },
    {
        "id": 11,
        "question": "How do objects of different classes respond to polymorphism in Java?",
        "target_document": "java_oop_guide.pdf",
        "expected_page": 2,
        "expected_keywords": ["polymorphism", "classes", "method call"],
        "is_relevant_in_corpus": True,
        "category": "java_oop",
    },

    # -------------------------------------------------------------
    # Category 3: Candidate Profile & Resume (Target: sample_resume.pdf - Page 1)
    # -------------------------------------------------------------
    {
        "id": 12,
        "question": "What programming languages does Jyoti know?",
        "target_document": "sample_resume.pdf",
        "expected_page": 1,
        "expected_keywords": ["python", "java", "c"],
        "is_relevant_in_corpus": True,
        "category": "resume",
    },
    {
        "id": 13,
        "question": "What web development technologies and frameworks are listed on the resume?",
        "target_document": "sample_resume.pdf",
        "expected_page": 1,
        "expected_keywords": ["html5", "css3", "javascript", "react.js", "node.js"],
        "is_relevant_in_corpus": True,
        "category": "resume",
    },
    {
        "id": 14,
        "question": "What databases does the candidate have experience with?",
        "target_document": "sample_resume.pdf",
        "expected_page": 1,
        "expected_keywords": ["sql", "mysql", "mongodb"],
        "is_relevant_in_corpus": True,
        "category": "resume",
    },
    {
        "id": 15,
        "question": "What is the candidate's educational degree and specialization?",
        "target_document": "sample_resume.pdf",
        "expected_page": 1,
        "expected_keywords": ["computer science", "engineering", "b.e"],
        "is_relevant_in_corpus": True,
        "category": "resume",
    },
    {
        "id": 16,
        "question": "What projects has Jyoti developed according to the resume?",
        "target_document": "sample_resume.pdf",
        "expected_page": 1,
        "expected_keywords": ["project", "projects", "placement", "assistant"],
        "is_relevant_in_corpus": True,
        "category": "resume",
    },
    {
        "id": 17,
        "question": "What machine learning or AI technologies are mentioned in the profile?",
        "target_document": "sample_resume.pdf",
        "expected_page": 1,
        "expected_keywords": ["rag", "llm", "embeddings", "chromadb", "sentence transformers"],
        "is_relevant_in_corpus": True,
        "category": "resume",
    },
    {
        "id": 18,
        "question": "What internship or practical work experience is described in the resume?",
        "target_document": "sample_resume.pdf",
        "expected_page": 1,
        "expected_keywords": ["internship", "fastapi", "rag", "docker"],
        "is_relevant_in_corpus": True,
        "category": "resume",
    },
    {
        "id": 19,
        "question": "What developer tools and version control systems does the candidate use?",
        "target_document": "sample_resume.pdf",
        "expected_page": 1,
        "expected_keywords": ["git", "github", "docker", "vscode"],
        "is_relevant_in_corpus": True,
        "category": "resume",
    },
    {
        "id": 20,
        "question": "What contact information or email address is provided on the resume?",
        "target_document": "sample_resume.pdf",
        "expected_page": 1,
        "expected_keywords": ["jyotigudlamani@gmail.com", "8861941579"],
        "is_relevant_in_corpus": True,
        "category": "resume",
    },

    # -------------------------------------------------------------
    # Category 4: Combined Technical & Semantic Queries
    # -------------------------------------------------------------
    {
        "id": 21,
        "question": "How does the candidate apply Python and FastAPI in their backend work?",
        "target_document": "sample_resume.pdf",
        "expected_page": 1,
        "expected_keywords": ["python", "fastapi"],
        "is_relevant_in_corpus": True,
        "category": "resume",
    },
    {
        "id": 22,
        "question": "Which keyword in Java connects a child class to its parent superclass?",
        "target_document": "java_oop_guide.pdf",
        "expected_page": 1,
        "expected_keywords": ["extends", "subclass", "superclass"],
        "is_relevant_in_corpus": True,
        "category": "java_oop",
    },
    {
        "id": 23,
        "question": "How are abstract methods implemented in Java concrete classes?",
        "target_document": "java_oop_guide.pdf",
        "expected_page": 2,
        "expected_keywords": ["implements", "interface", "abstract method"],
        "is_relevant_in_corpus": True,
        "category": "java_oop",
    },
    {
        "id": 24,
        "question": "What vector database is utilized for document chunk storage?",
        "target_document": "sample_resume.pdf",
        "expected_page": 1,
        "expected_keywords": ["chromadb"],
        "is_relevant_in_corpus": True,
        "category": "resume",
    },
    {
        "id": 25,
        "question": "What is the candidate's experience with React and frontend interfaces?",
        "target_document": "sample_resume.pdf",
        "expected_page": 1,
        "expected_keywords": ["react.js", "javascript"],
        "is_relevant_in_corpus": True,
        "category": "resume",
    },

    # -------------------------------------------------------------
    # Category 5: Out-of-Domain / Negative Verification Queries
    # (Must NOT invent answers or falsely match documents)
    # -------------------------------------------------------------
    {
        "id": 26,
        "question": "What is the capital city of Australia and what is its population?",
        "target_document": None,
        "expected_page": None,
        "expected_keywords": [],
        "is_relevant_in_corpus": False,
        "category": "negative",
    },
    {
        "id": 27,
        "question": "How do you bake a classic Italian Margherita pizza in a wood-fired oven?",
        "target_document": None,
        "expected_page": None,
        "expected_keywords": [],
        "is_relevant_in_corpus": False,
        "category": "negative",
    },
    {
        "id": 28,
        "question": "What are the stages of photosynthesis in cellular biology?",
        "target_document": None,
        "expected_page": None,
        "expected_keywords": [],
        "is_relevant_in_corpus": False,
        "category": "negative",
    },
    {
        "id": 29,
        "question": "Who was the first emperor of the Roman Empire?",
        "target_document": None,
        "expected_page": None,
        "expected_keywords": [],
        "is_relevant_in_corpus": False,
        "category": "negative",
    },
    {
        "id": 30,
        "question": "What are the primary symptoms and treatments for seasonal influenza?",
        "target_document": None,
        "expected_page": None,
        "expected_keywords": [],
        "is_relevant_in_corpus": False,
        "category": "negative",
    },
]
