"""
Service for Module 1: Technical Interview Preparation.
Generates technical interview questions, in-depth explanations, code examples,
and follow-up questions across all 11 core CS and AI topics.
"""

from uuid import uuid4
import json
import random
import re
from typing import Any, Dict, List, Optional
import httpx

from backend.app.core.config import settings
from backend.app.db.mongo import MongoDBManager
from backend.app.schemas.technical import TECHNICAL_TOPICS, DIFFICULTY_LEVELS


# Curated high-yield placement question bank (serves as robust base and fallback)
CURATED_QUESTIONS: Dict[str, List[Dict[str, Any]]] = {
    "Java": [
        {
            "subtopic": "Memory Management & Garbage Collection",
            "difficulty": "medium",
            "question": "How does Garbage Collection work in Java, and what is the difference between Minor GC and Major GC?",
            "answer": "Java memory is divided into the Heap and Stack. The Heap is further divided into the Young Generation (Eden, S0, S1) and Old (Tenured) Generation. New objects are allocated in Eden. When Eden fills, a Minor GC occurs: live objects are moved to Survivor spaces and aged. After passing an age threshold (tenuring threshold, default 15), survivors are promoted to Old Generation. Major (Full) GC cleans the Old Generation, which causes longer 'Stop-the-World' pauses.",
            "explanation": "Modern JVMs use generational collectors like G1, ZGC, or Shenandoah. G1 splits the heap into equal-sized regions and collects regions with the most garbage first (Garbage-First). Memory leaks in Java occur when unused objects remain referenced in static fields, unclosed connections, or improperly overridden equals()/hashCode() in HashMaps.",
            "code_example": "// Tuning JVM GC and checking memory usage\nRuntime runtime = Runtime.getRuntime();\nlong totalMem = runtime.totalMemory();\nlong freeMem = runtime.freeMemory();\nSystem.out.println(\"Used Memory: \" + (totalMem - freeMem) / (1024 * 1024) + \" MB\");\n\n// Suggesting GC (non-guaranteed)\nSystem.gc();",
            "code_language": "java",
            "follow_up_questions": [
                "What is the difference between G1GC and ZGC?",
                "How do weak references (WeakReference) differ from soft references (SoftReference)?",
            ],
            "key_takeaways": [
                "Generational hypothesis: most objects die young.",
                "Minor GC targets Young Gen; Major/Full GC targets Old Gen.",
                "System.gc() is only a hint to the JVM and does not guarantee immediate collection."
            ]
        },
        {
            "subtopic": "Collections & Multithreading",
            "difficulty": "hard",
            "question": "How does ConcurrentHashMap achieve thread safety in Java 8 compared to Hashtable or SynchronizedMap?",
            "answer": "In Java 7, ConcurrentHashMap used Segment-level locking (reentrant locks on 16 buckets). In Java 8+, it abandoned segments and uses Compare-And-Swap (CAS) for node insertion when a bucket is empty, and synchronized blocks on only the first node (head) of a bucket list/tree when collisions occur. Hashtable and Collections.synchronizedMap lock the entire table on every read/write, causing extreme contention.",
            "explanation": "ConcurrentHashMap never locks on read operations (get() is lock-free via volatile val and next pointers). Furthermore, when bucket size exceeds 8 and total capacity exceeds 64, buckets transform from linked lists (O(N)) to Red-Black trees (O(log N)), preventing hash collision DoS attacks.",
            "code_example": "ConcurrentMap<String, Integer> map = new ConcurrentHashMap<>();\n// Atomic compute-if-absent\nmap.computeIfAbsent(\"placement\", k -> 1);\n// Atomic increment\nmap.merge(\"placement\", 1, Integer::sum);",
            "code_language": "java",
            "follow_up_questions": [
                "Why does ConcurrentHashMap not allow null keys or values?",
                "What is the difference between fail-fast and fail-safe iterators?",
            ],
            "key_takeaways": [
                "Java 8 ConcurrentHashMap uses CAS + synchronized on table bucket heads.",
                "Reads are lock-free; writes lock only the target bucket.",
                "Does not support null keys or values to avoid ambiguity in multithreaded environments."
            ]
        }
    ],
    "Python": [
        {
            "subtopic": "Concurrency & GIL",
            "difficulty": "medium",
            "question": "What is Python's Global Interpreter Lock (GIL), and how do you bypass it for CPU-bound tasks?",
            "answer": "The GIL is a mutex in CPython that prevents multiple native threads from executing Python bytecode simultaneously. It exists because CPython's memory management is not thread-safe and relies on reference counting. Consequently, multi-threading in Python speeds up I/O-bound tasks (network, disk) where threads release the GIL while waiting, but does NOT speed up CPU-bound tasks. To bypass the GIL for CPU-bound operations, use the `multiprocessing` module (separate processes with independent GILs), C-extensions (Cython/Rust), or Python 3.13 free-threaded builds.",
            "explanation": "For I/O concurrency, `asyncio` with an event loop is preferred over threads because of lower memory overhead and avoidance of race conditions on shared memory without locks.",
            "code_example": "from multiprocessing import Pool\n\ndef heavy_calculation(n: int) -> int:\n    return sum(i * i for i in range(n))\n\nif __name__ == '__main__':\n    with Pool(processes=4) as pool:\n        results = pool.map(heavy_calculation, [10_000_000] * 4)\n    print(\"Finished calculations across 4 processes.\")",
            "code_language": "python",
            "follow_up_questions": [
                "What is the difference between threading.Thread and multiprocessing.Process?",
                "How does asyncio cooperate without multi-threading?",
            ],
            "key_takeaways": [
                "CPython GIL restricts execution to 1 thread at a time per process.",
                "Use threading or asyncio for I/O-bound tasks.",
                "Use multiprocessing or native extensions for CPU-bound parallelism."
            ]
        }
    ],
    "C and C++": [
        {
            "subtopic": "Smart Pointers & Memory Management",
            "difficulty": "medium",
            "question": "What are Smart Pointers in C++11, and how do std::unique_ptr and std::shared_ptr manage resource lifecycles?",
            "answer": "Smart pointers are RAII (Resource Acquisition Is Initialization) wrapper classes around raw pointers that automatically deallocate heap memory when the pointer goes out of scope, preventing memory leaks.\n1. `std::unique_ptr`: Enforces exclusive ownership of the object. It cannot be copied, only moved (`std::move`). Overhead is zero (same as raw pointer).\n2. `std::shared_ptr`: Implements shared reference-counted ownership. Memory is freed only when the last `shared_ptr` pointing to it is destroyed or reset.\n3. `std::weak_ptr`: Non-owning observer that breaks circular references between `shared_ptr` instances.",
            "explanation": "Always prefer `std::make_unique` and `std::make_shared` over raw `new` because they provide exception safety and allocate the control block and managed object in a single contiguous memory block.",
            "code_example": "#include <iostream>\n#include <memory>\n\nclass Node {\npublic:\n    int value;\n    Node(int val) : value(val) { std::cout << \"Created \" << value << \"\\n\"; }\n    ~Node() { std::cout << \"Destroyed \" << value << \"\\n\"; }\n};\n\nint main() {\n    // Exclusive ownership\n    auto uPtr = std::make_unique<Node>(10);\n    \n    // Shared ownership\n    auto sPtr1 = std::make_shared<Node>(20);\n    auto sPtr2 = sPtr1; // Ref count = 2\n    std::cout << \"Use count: \" << sPtr1.use_count() << \"\\n\";\n    return 0;\n}",
            "code_language": "cpp",
            "follow_up_questions": [
                "What happens if two std::shared_ptr instances point to each other in a cycle?",
                "What is the virtual destructor requirement when deleting through a base class pointer?",
            ],
            "key_takeaways": [
                "Use std::unique_ptr by default for zero-overhead RAII ownership.",
                "Use std::shared_ptr only when shared ownership is genuinely needed.",
                "Use std::weak_ptr to break circular reference memory leaks."
            ]
        }
    ],
    "OOP": [
        {
            "subtopic": "Design Principles & Polymorphism",
            "difficulty": "easy",
            "question": "What are the SOLID principles in Object-Oriented Programming, and why are they critical in enterprise software?",
            "answer": "SOLID represents five essential design principles:\n1. Single Responsibility Principle (SRP): A class should have one, and only one, reason to change.\n2. Open/Closed Principle (OCP): Classes should be open for extension but closed for modification.\n3. Liskov Substitution Principle (LSP): Subtypes must be substitutable for their base types without altering correctness.\n4. Interface Segregation Principle (ISP): Clients should not be forced to depend on methods they do not use (prefer small, role-specific interfaces).\n5. Dependency Inversion Principle (DIP): High-level modules should not depend on low-level modules; both should depend on abstractions.",
            "explanation": "Violating LSP often happens when a subclass throws UnsupportedOperationException for an inherited method (e.g. Square inheriting Rectangle and breaking width/height setters). Violating DIP causes tight coupling where unit testing requires actual databases or web services instead of mocks.",
            "code_example": "// Dependency Inversion Example:\n// Good: High level depends on interface abstraction\ninterface NotificationService {\n    void notify(String msg);\n}\nclass EmailService implements NotificationService {\n    public void notify(String msg) { /* send email */ }\n}\nclass PlacementAlert {\n    private final NotificationService service;\n    public PlacementAlert(NotificationService service) {\n        this.service = service; // Injected dependency\n    }\n}",
            "code_language": "java",
            "follow_up_questions": [
                "How does the Strategy Pattern demonstrate the Open/Closed Principle?",
                "What is the difference between abstraction and encapsulation?",
            ],
            "key_takeaways": [
                "SOLID prevents code rot, tight coupling, and fragile inheritance trees.",
                "LSP ensures that polymorphism does not break program contracts.",
                "DIP enables testability via dependency injection."
            ]
        }
    ],
    "DSA": [
        {
            "subtopic": "Dynamic Programming & Trees",
            "difficulty": "medium",
            "question": "How do you detect and remove a cycle in a Singly Linked List using Floyd's Cycle-Finding Algorithm?",
            "answer": "Floyd's algorithm uses two pointers: `slow` moving 1 step and `fast` moving 2 steps.\n1. Detection: If `fast` or `fast.next` reaches null, no cycle exists. If `slow == fast`, a cycle is detected.\n2. Finding Start of Cycle: Keep `slow` at the meeting point and reset `fast` to `head`. Move both pointers 1 step at a time. The node where they meet is the start of the loop.\n3. Cycle Removal: Traverse to the node whose `.next` points back to the loop start and set its `.next = null`.",
            "explanation": "Proof: Let distance from head to loop start be L. Let distance from loop start to meeting point be k. Let loop length be C. When they meet: 2 * (L + k) = L + k + nC => L + k = nC => L = nC - k. Therefore, moving both from head and meeting point step-by-step guarantees they meet at the loop start after L steps.",
            "code_example": "class ListNode {\n    int val;\n    ListNode next;\n    ListNode(int x) { val = x; }\n}\n\npublic static void removeCycle(ListNode head) {\n    if (head == null || head.next == null) return;\n    ListNode slow = head, fast = head;\n    while (fast != null && fast.next != null) {\n        slow = slow.next;\n        fast = fast.next.next;\n        if (slow == fast) break;\n    }\n    if (slow != fast) return; // No cycle\n    fast = head;\n    while (slow.next != fast.next) {\n        slow = slow.next;\n        fast = fast.next;\n    }\n    slow.next = null; // Break cycle\n}",
            "code_language": "java",
            "follow_up_questions": [
                "What is the time and space complexity of Floyd's Cycle Algorithm?",
                "Can Floyd's cycle detection be applied to arrays? (e.g. LeetCode 287 - Find the Duplicate Number)",
            ],
            "key_takeaways": [
                "Time Complexity: O(N); Space Complexity: O(1).",
                "Two-pointer technique avoids O(N) hash set auxiliary storage.",
                "Crucial interview pattern applicable to linked lists and sequence cycle detection."
            ]
        }
    ],
    "DBMS": [
        {
            "subtopic": "Transactions & ACID",
            "difficulty": "medium",
            "question": "Explain the ACID properties in DBMS and the four standard Transaction Isolation Levels.",
            "answer": "ACID properties ensure database integrity:\n- Atomicity: All operations in a transaction succeed or all are rolled back (All-or-Nothing).\n- Consistency: Database moves from one valid state to another satisfying all constraints.\n- Isolation: Concurrent transactions do not interfere with each other.\n- Durability: Once committed, updates persist even in system crashes.\n\nIsolation Levels (lowest to highest isolation):\n1. Read Uncommitted: Permits Dirty Reads.\n2. Read Committed: Prevents Dirty Reads; permits Non-repeatable Reads.\n3. Repeatable Read: Prevents Dirty & Non-repeatable Reads; may permit Phantom Reads (MySQL InnoDB prevents phantom reads here using Next-Key Locks).\n4. Serializable: Complete serial isolation via range locks (highest safety, lowest concurrency).",
            "explanation": "Dirty read = reading uncommitted changes of another transaction. Non-repeatable read = reading a row, another transaction modifies and commits it, re-reading returns different data. Phantom read = reading a range of rows, another transaction inserts a new row matching the range, re-reading returns new rows.",
            "code_example": "-- Setting isolation level in SQL\nSET TRANSACTION ISOLATION LEVEL REPEATABLE READ;\nSTART TRANSACTION;\nSELECT balance FROM accounts WHERE user_id = 101 FOR UPDATE; -- Row-level lock\nUPDATE accounts SET balance = balance - 500 WHERE user_id = 101;\nCOMMIT;",
            "code_language": "sql",
            "follow_up_questions": [
                "What is WAL (Write-Ahead Logging) and how does it guarantee durability?",
                "How does MVCC (Multi-Version Concurrency Control) work in Postgres and MySQL?",
            ],
            "key_takeaways": [
                "Atomicity & Durability are managed by logs (undo/redo logs, WAL).",
                "Isolation is managed by locks and MVCC.",
                "Repeatable Read is the default in MySQL InnoDB; Read Committed is default in PostgreSQL and Oracle."
            ]
        }
    ],
    "SQL": [
        {
            "subtopic": "Window Functions & Joins",
            "difficulty": "medium",
            "question": "What is the difference between ROW_NUMBER(), RANK(), and DENSE_RANK() in SQL?",
            "answer": "All three are window ranking functions evaluated over an `OVER (PARTITION BY ... ORDER BY ...)` clause, but handle duplicate values differently:\n- `ROW_NUMBER()`: Assigns a unique, consecutive integer to every row regardless of ties (e.g. 1, 2, 3, 4).\n- `RANK()`: Assigns the same rank to identical values, but skips subsequent rank numbers by the number of ties (e.g. 1, 2, 2, 4).\n- `DENSE_RANK()`: Assigns the same rank to identical values without skipping any numbers (e.g. 1, 2, 2, 3).",
            "explanation": "In placement technical interviews, finding the Nth highest salary is universally asked. Using `DENSE_RANK()` inside a Common Table Expression (CTE) handles ties correctly without returning empty results.",
            "code_example": "-- Finding the 2nd highest salary department-wise\nWITH RankedSalaries AS (\n    SELECT \n        emp_id, \n        emp_name, \n        department, \n        salary,\n        DENSE_RANK() OVER (PARTITION BY department ORDER BY salary DESC) as salary_rank\n    FROM employees\n)\nSELECT emp_name, department, salary\nFROM RankedSalaries\nWHERE salary_rank = 2;",
            "code_language": "sql",
            "follow_up_questions": [
                "What is the difference between WHERE and HAVING in SQL?",
                "How does an INDEX seek differ from an INDEX scan?",
            ],
            "key_takeaways": [
                "ROW_NUMBER never has ties.",
                "RANK skips positions after ties.",
                "DENSE_RANK never skips rank numbers.",
                "Window functions calculate ranks without collapsing rows like GROUP BY."
            ]
        }
    ],
    "Operating Systems": [
        {
            "subtopic": "Process Synchronization & Deadlocks",
            "difficulty": "medium",
            "question": "What are the four necessary conditions for a Deadlock in an Operating System, and how can they be prevented?",
            "answer": "A deadlock occurs if and only if all four Coffman conditions hold simultaneously:\n1. Mutual Exclusion: At least one resource must be held in a non-shareable mode.\n2. Hold and Wait: A process must hold at least one resource and wait to acquire additional resources held by others.\n3. No Preemption: Resources cannot be forcibly seized; only released voluntarily by the holding process.\n4. Circular Wait: A closed chain of processes exists such that each holds one resource and waits for another held by the next process in the chain.\n\nDeadlock Prevention invalidates at least one condition (e.g. imposing a global resource ordering breaks circular wait).",
            "explanation": "Banker's Algorithm is a deadlock avoidance algorithm that checks for a 'safe sequence' before allocating requested resources. If allocation leaves the system in an unsafe state where at least one process could starve, allocation is delayed.",
            "code_example": "// Breaking Circular Wait via Global Resource Ordering\n// Thread A and Thread B acquire locks in identical order (Lock1 -> Lock2)\nstd::mutex lock1, lock2;\n\nvoid threadA() {\n    std::lock(lock1, lock2); // Atomic dead-lock free multi-lock acquisition\n    std::lock_guard<std::mutex> g1(lock1, std::adopt_lock);\n    std::lock_guard<std::mutex> g2(lock2, std::adopt_lock);\n    // Critical section\n}",
            "code_language": "cpp",
            "follow_up_questions": [
                "How does a mutex differ from a counting semaphore?",
                "What is Priority Inversion and how does Priority Inheritance solve it?",
            ],
            "key_takeaways": [
                "All 4 Coffman conditions must hold for deadlock.",
                "Enforcing global resource acquisition order prevents circular wait.",
                "Banker's algorithm avoids deadlocks dynamically by maintaining safe states."
            ]
        }
    ],
    "Computer Networks": [
        {
            "subtopic": "Transport Layer & Protocols",
            "difficulty": "easy",
            "question": "Explain the TCP Three-Way Handshake and the Four-Way Teardown.",
            "answer": "TCP is a connection-oriented, reliable transport protocol. Before exchanging data, client and server synchronize sequence numbers:\n\nThree-Way Handshake:\n1. SYN: Client sends SYN with random initial sequence number `seq = x` (Client in SYN_SENT state).\n2. SYN-ACK: Server responds with `seq = y`, acknowledgment `ack = x + 1` (Server in SYN_RCVD state).\n3. ACK: Client sends `ack = y + 1` (Connection ESTABLISHED on both sides).\n\nFour-Way Termination:\n1. FIN: Client sends FIN to terminate its sending half-channel (FIN_WAIT_1).\n2. ACK: Server sends ACK (Client in FIN_WAIT_2; Server in CLOSE_WAIT).\n3. FIN: Server finishes sending remaining data and sends its own FIN (LAST_ACK).\n4. ACK: Client sends ACK and enters TIME_WAIT (typically 2*MSL = 60s) before terminating.",
            "explanation": "TIME_WAIT on the client is critical: it ensures the final ACK reaches the server (in case it was dropped in transit) so the server does not re-send FIN and remain stuck in LAST_ACK, and prevents lingering packets from an old connection from interfering with a new incarnation of the same socket.",
            "code_example": "# Inspecting TCP connections on Windows / Linux:\n# netstat -an | findstr ESTABLISHED\n# ss -tuna | grep TIME-WAIT",
            "code_language": "bash",
            "follow_up_questions": [
                "What is a SYN Flood attack and how do SYN Cookies mitigate it?",
                "Why does DNS use UDP for queries but TCP for zone transfers?",
            ],
            "key_takeaways": [
                "3-Way Handshake: SYN -> SYN-ACK -> ACK.",
                "4-Way Teardown: FIN -> ACK -> FIN -> ACK.",
                "TIME_WAIT prevents duplicate packets from corrupting subsequent connections."
            ]
        }
    ],
    "AI and ML": [
        {
            "subtopic": "Optimization & Deep Learning",
            "difficulty": "medium",
            "question": "What is the vanishing/exploding gradient problem in Deep Neural Networks and how do modern architectures solve it?",
            "answer": "During backpropagation, gradients are computed via the chain rule by multiplying Jacobians across layers: $\\frac{\\partial L}{\\partial W_1} = \\prod_{i} W_i \\cdot \\sigma'(z_i)$. When using saturating activation functions like Sigmoid or Tanh, the derivative $\\sigma'$ is at most 0.25. Multiplying many fractions causes the gradient to shrink exponentially toward zero for early layers, stopping them from learning (vanishing gradient). If weights are large, repeated multiplication causes exponential explosion (exploding gradient).\n\nModern Solutions:\n1. Non-saturating activations: ReLU, Leaky ReLU, GELU, Swish.\n2. Residual / Skip Connections: ResNets allow gradients to flow directly backwards unchanged ($z + f(z)$).\n3. Normalization: Batch Normalization and Layer Normalization stabilize distribution shifts.\n4. Proper initialization: He (Kaiming) or Xavier initialization.",
            "explanation": "Transformers rely heavily on Pre-LayerNorm and residual connections around multi-head attention and feedforward blocks, which enables training models with dozens or hundreds of stacked layers without vanishing gradients.",
            "code_example": "import torch.nn as nn\n\n# Residual block solving vanishing gradients\nclass ResidualBlock(nn.Module):\n    def __init__(self, dim):\n        super().__init__()\n        self.net = nn.Sequential(\n            nn.Linear(dim, dim),\n            nn.LayerNorm(dim),\n            nn.GELU(),\n            nn.Linear(dim, dim)\n        )\n    def forward(self, x):\n        return x + self.net(x) # Skip connection",
            "code_language": "python",
            "follow_up_questions": [
                "How does Adam optimizer combine Momentum and RMSprop?",
                "Why is Cross-Entropy loss preferred over Mean Squared Error for classification?",
            ],
            "key_takeaways": [
                "Vanishing gradients happen when chain-rule products decay to zero.",
                "Residual skip connections provide an uninterrupted highway for backpropagating gradients.",
                "LayerNorm and ReLU/GELU activations prevent activation saturation."
            ]
        }
    ],
    "LLM and RAG": [
        {
            "subtopic": "Retrieval & Hallucination Mitigation",
            "difficulty": "hard",
            "question": "What are the primary differences between Bi-Encoders and Cross-Encoders in RAG, and why is a Two-Stage retrieval pipeline standard?",
            "answer": "1. Bi-Encoder (Embedding model, e.g. all-MiniLM-L6-v2):\n- Computes query embedding $E(Q)$ and document embedding $E(D)$ independently.\n- Relevance is measured via cosine similarity or dot product in $O(d)$ time.\n- Because embeddings can be pre-computed and indexed into vector databases (MVS/HNSW), searching millions of documents takes $< 15\\text{ ms}$.\n- Limitation: Loses token-level interaction between query and document.\n\n2. Cross-Encoder (Reranker model, e.g. ms-marco-MiniLM):\n- Passes query and passage concatenated into the transformer: $[CLS] Q [SEP] D$.\n- Full cross-attention computes attention weights between every query token and document token.\n- Extremely accurate; eliminates false positives.\n- Limitation: Very slow ($O(N \\times L^2)$); cannot pre-compute embeddings.\n\nTwo-Stage Strategy:\nStage 1: Bi-Encoder retrieves Top-20 candidates in milliseconds (high recall).\nStage 2: Cross-Encoder scores and reranks the 20 candidates into Top-3 (high precision).",
            "explanation": "Reciprocal Rank Fusion (RRF) further augments Stage 1 by blending sparse lexical BM25 rankings with dense vector embeddings before reranking, ensuring rare keywords and semantic concepts are both captured.",
            "code_example": "from sentence_transformers import CrossEncoder\n\n# Stage 2: Cross-Encoder Reranking\nreranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')\nquery = \"How does RRF fuse ranked lists?\"\npassages = [\"RRF calculates scores as 1/(60 + rank).\", \"Java is an OOP language.\"]\n\nscores = reranker.predict([[query, p] for p in passages])\n# Scores will rank passage 0 with high score and passage 1 with negative score",
            "code_language": "python",
            "follow_up_questions": [
                "How does Reciprocal Rank Fusion (RRF) handle differing score scales between BM25 and vector search?",
                "What is Self-RAG or Corrective RAG (CRAG)?",
            ],
            "key_takeaways": [
                "Bi-encoders embed independently for fast approximate nearest neighbor search.",
                "Cross-encoders process full cross-attention for high precision.",
                "Two-stage retrieval delivers both speed and accuracy."
            ]
        }
    ],
}


class TechnicalPrepService:
    """Orchestrates technical interview question generation and bookmarking."""

    _instance: Optional["TechnicalPrepService"] = None

    def __init__(self):
        self.mongo = MongoDBManager.get_instance()

    @classmethod
    def get_instance(cls) -> "TechnicalPrepService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def generate_question(
        self,
        topic: str,
        difficulty: str = "medium",
        subtopic: Optional[str] = None,
        include_code: bool = True,
    ) -> Dict[str, Any]:
        """Generates a technical interview question with explanation, code, and follow-ups."""
        normalized_topic = next((t for t in TECHNICAL_TOPICS if t.lower() == topic.lower()), "Java")
        normalized_diff = difficulty.lower() if difficulty.lower() in DIFFICULTY_LEVELS else "medium"

        default_lang = normalized_topic.lower() if normalized_topic in ["Java", "Python", "SQL"] else "cpp"
        # Try generating dynamically via Ollama LLM if available
        try:
            prompt = (
                f"You are an expert technical interviewer for top software engineering companies.\n"
                f"Generate a rigorous interview question for Topic: {normalized_topic}, Difficulty: {normalized_diff}"
                + (f", Subtopic: {subtopic}" if subtopic else "") + ".\n\n"
                f"Format your response as a valid JSON object strictly matching this schema with no markdown code fences:\n"
                f"{{\n"
                f'  "subtopic": "specific subtopic name",\n'
                f'  "difficulty": "{normalized_diff}",\n'
                f'  "question": "clear, rigorous interview question",\n'
                f'  "answer": "concise, accurate direct answer summary",\n'
                f'  "explanation": "in-depth technical explanation, trade-offs, and edge cases",\n'
                f'  "code_example": "syntactically correct code snippet illustrating the concept or solution",\n'
                f'  "code_language": "{default_lang}",\n'
                f'  "follow_up_questions": ["follow-up 1", "follow-up 2"],\n'
                f'  "key_takeaways": ["takeaway 1", "takeaway 2", "takeaway 3"]\n'
                f"}}"
            )

            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/chat",
                    json={
                        "model": settings.OLLAMA_MODEL_NAME,
                        "messages": [
                            {"role": "system", "content": "You output only valid JSON without explanation or formatting."},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                        "options": {"temperature": 0.3},
                    },
                )
                if res.status_code == 200:
                    raw_text = res.json().get("message", {}).get("content", "").strip()
                    # Strip any ```json code blocks
                    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
                    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
                    parsed = json.loads(cleaned)
                    parsed["question_id"] = f"tech_{uuid4().hex[:12]}"
                    parsed["topic"] = normalized_topic
                    return parsed
        except Exception:
            pass  # Fall through to curated repository

        # Fallback to high-yield curated bank
        topic_pool = CURATED_QUESTIONS.get(normalized_topic, CURATED_QUESTIONS["Java"])
        diff_matches = [q for q in topic_pool if q.get("difficulty") == normalized_diff]
        selected = dict(random.choice(diff_matches if diff_matches else topic_pool))
        selected["question_id"] = f"tech_{uuid4().hex[:12]}"
        selected["topic"] = normalized_topic
        return selected

    def save_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves a technical interview question in MongoDB."""
        return self.mongo.save_technical_question(question_data)

    def list_saved_questions(self, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists bookmarked technical interview questions."""
        return self.mongo.list_saved_technical_questions(topic=topic)

    def delete_saved_question(self, question_id: str) -> bool:
        """Deletes a bookmarked technical question."""
        return self.mongo.delete_technical_question(question_id)
