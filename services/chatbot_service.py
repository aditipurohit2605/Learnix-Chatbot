import os
import re
import json
import logging
import difflib
from .ai_client import ai_client
from .web_search import fetch_web_context
from models import db
from models.models import UnansweredQuestion, KnowledgeBaseAnswer

logger = logging.getLogger(__name__)

SYSTEM_PROMPTS = {
    "Default": (
        "You are Learnix AI Engineering & Placement Assistant. "
        "Help B.Tech, BE, MCA, BCA, and CSE students learn concepts clearly and step-by-step."
    ),
    "Data Structures & Algorithms": (
        "You are Learnix DSA Mentor. Explain algorithms, data structures, and coding problems with optimized solutions. "
        "Help with LeetCode-style questions, time/space complexity analysis."
    ),
    "Object Oriented Programming": (
        "You are Learnix OOP Tutor. Explain OOP concepts: classes, objects, inheritance, polymorphism, encapsulation, abstraction. "
        "Provide examples in Python, Java, and C++."
    ),
    "Database Management Systems": (
        "You are Learnix DBMS Tutor. Explain SQL, normalization, ER diagrams, transactions, ACID properties, joins, indexes."
    ),
    "Operating Systems": (
        "You are Learnix OS Tutor. Explain processes, threads, CPU scheduling, deadlocks, memory management, file systems."
    ),
    "Computer Networks": (
        "You are Learnix CN Tutor. Explain OSI model, TCP/IP, protocols, routing, switching, network security."
    ),
    "Software Engineering": (
        "You are Learnix SE Tutor. Explain SDLC, agile, design patterns, software testing, UML diagrams."
    ),
    "Web Development": (
        "You are Learnix Web Dev Tutor. Explain HTML, CSS, JavaScript, React, Node.js, backend, APIs, databases for web."
    ),
    "Python Programming": (
        "You are Learnix Python Tutor. Explain Python syntax, libraries, data structures, OOP in Python, web dev with Python."
    ),
    "Java Programming": (
        "You are Learnix Java Tutor. Explain Java fundamentals, OOP, collections, multithreading, Spring Boot, J2EE."
    ),
    "C Programming": (
        "You are Learnix C Tutor. Explain C fundamentals, pointers, arrays, strings, structures, file handling, memory management."
    ),
    "C++ Programming": (
        "You are Learnix C++ Tutor. Explain C++ fundamentals, OOP, STL, pointers, references, templates, exceptions."
    ),
    "Artificial Intelligence": (
        "You are Learnix AI Tutor. Explain AI fundamentals, search algorithms, knowledge representation, expert systems."
    ),
    "Machine Learning": (
        "You are Learnix ML Tutor. Explain supervised/unsupervised learning, regression, classification, clustering, neural networks."
    ),
    "Data Science": (
        "You are Learnix Data Science Tutor. Explain data analysis, visualization, pandas, numpy, matplotlib, statistics."
    ),
    "Cloud Computing": (
        "You are Learnix Cloud Tutor. Explain AWS, Azure, GCP basics, virtualization, containers, serverless, cloud security."
    ),
    "Cyber Security": (
        "You are Learnix Cyber Security Tutor. Explain network security, cryptography, ethical hacking, vulnerability assessment."
    ),
    "DevOps": (
        "You are Learnix DevOps Tutor. Explain CI/CD, Docker, Kubernetes, Jenkins, Git, infrastructure as code, monitoring."
    ),
    "System Design": (
        "You are Learnix System Design Tutor. Explain scalability, availability, consistency, and large-system design patterns."
    ),
    "Generative AI": (
        "You are Learnix Generative AI Tutor. Explain LLMs, prompt engineering, LangChain, fine-tuning, diffusion models, AI ethics."
    ),
    "Communication Skills": (
        "You are Learnix Communication Coach. Help with HR interviews, group discussions, professional email writing, confidence building."
    ),
    "Placement Prep": (
        "You are Learnix Placement Coach. Help with aptitude, reasoning, coding, interview questions, and company preparation."
    ),
    "Interview Prep": (
        "You are Learnix Interview Coach. Prepare students for technical, HR, and behavioral interviews."
    ),
    "Career Guidance": (
        "You are Learnix Career Advisor. Suggest career paths, certifications, projects, and learning roadmaps."
    ),
    "Resume Help": (
        "You are Learnix Resume Expert. Improve resumes for ATS, internships, and placements."
    ),
}

REMOVED_SUBJECTS = {
    "Physics", "Chemistry", "Biology", "History", "English", "General Science",
    "Social Science", "Geography", "Civics", "Environmental Studies",
    "Mathematics", "Computer Science", "English Literature", "School Science",
    "School Physics", "School Chemistry", "School Mathematics",
}

QUIZ_TRIGGERS = re.compile(
    r"\b(generate\s+quiz|create\s+quiz|make\s+quiz|quiz\s+me|test\s+me|"
    r"practice\s+questions?|mcq|give\s+me\s+a\s+quiz|quiz\s+on)\b",
    re.I,
)

LEARNIX_GLOBAL_INSTRUCTIONS = """
You are Learnix AI, an intelligent college learning and placement assistant for engineering students.

## Engineering Focus
Focus on: DSA, OS, DBMS, CN, OOP, Software Engineering, Web Development, Python, Java, C/C++,
AI, ML, Data Science, Cloud, Cyber Security, DevOps, System Design, Generative AI,
Placement Prep, Interview Prep, Communication Skills, Resume Help, Career Guidance.

Reject school-level subjects (Biology, History, Geography, School Science, etc.) politely.

## Response Style (ChatGPT-like)
- Use ## headings, ### subheadings, bullet points, numbered lists, tables, code blocks
- Never return a wall of text
- Structure: Overview → Key Concepts → Example → Interview Perspective → Summary
- Use web research context when provided to give up-to-date answers

## Quiz Generation
When user asks for a quiz (e.g. "Generate quiz", "Test me", "Practice questions"):
- Generate exactly 10 MCQs from the CURRENT conversation topic: 5 Easy, 3 Medium, 2 Hard
- Format each question with A/B/C/D options
- When user submits answers, provide: Score (X/10), Wrong answers, Weak areas, Suggestions

## Capabilities
You can generate: quizzes, interview questions, coding challenges, study plans, placement roadmaps.
Always provide useful, educational content. Never say you are unavailable.
"""

FALLBACK_LIBRARY = {
    "trees": """## Binary Trees

### Definition
A binary tree is a hierarchical data structure where each node has at most two children (left and right).

### Key Concepts
- **Root**: Topmost node
- **Leaf**: Node with no children
- **BST**: Left child < parent < right child
- **Traversals**: Inorder, Preorder, Postorder, Level-order (BFS)

### Example
```python
class Node:
    def __init__(self, val):
        self.val = val
        self.left = self.right = None
```

### Interview Questions
- What is the difference between a binary tree and a BST?
- How do you find the height of a binary tree?

### Summary
Binary trees are fundamental for search, sorting, and expression parsing.""",

    "graphs": """## Graphs

### Definition
A graph G = (V, E) consists of vertices (nodes) and edges connecting pairs of vertices.

### Key Concepts
- **Directed vs Undirected**
- **Weighted vs Unweighted**
- **DFS** and **BFS** traversals
- **Dijkstra's** for shortest paths

### Interview Questions
- When would you use BFS over DFS?
- Explain topological sorting.

### Summary
Graphs model networks, dependencies, and routing problems.""",

    "arrays": """## Arrays

### Definition
An array stores elements in contiguous memory with O(1) random access by index.

### Key Concepts
- Fixed vs dynamic sizing
- Two-pointer technique
- Sliding window pattern

### Interview Questions
- What is the time complexity of inserting at the beginning of an array?

### Summary
Arrays are the foundation of most algorithmic problem solving.""",

    "linked_lists": """## Linked Lists

### Definition
A linked list is a linear structure where each node points to the next node.

### Key Concepts
- Singly vs Doubly linked
- O(1) insertion at head, O(n) access by index
- Fast pointer / slow pointer (Floyd's cycle detection)

### Interview Questions
- How do you reverse a linked list iteratively?

### Summary
Linked lists excel at frequent insertions and deletions.""",

    "stacks": """## Stacks

### Definition
A stack follows LIFO (Last In, First Out).

### Interview Question
How can you implement a stack using two queues?

### Summary
Stacks are used in expression evaluation, undo operations, and DFS.""",

    "queues": """## Queues

### Definition
A queue follows FIFO (First In, First Out).

### Types
Simple, Circular, Deque, Priority Queue

### Summary
Queues power BFS, task scheduling, and buffering.""",

    "dbms": """## Database Management Systems

### Key Concepts
- **ACID**: Atomicity, Consistency, Isolation, Durability
- **Normalization**: 1NF, 2NF, 3NF, BCNF
- **Joins**: INNER, LEFT, RIGHT, FULL

### Example
```sql
SELECT e.name, d.dept_name
FROM employees e
INNER JOIN departments d ON e.dept_id = d.id;
```

### Summary
DBMS manages structured data with integrity and efficient querying.""",

    "os": """## Operating Systems

### Key Concepts
- Process vs Thread
- CPU Scheduling: FCFS, Round Robin, Priority
- Deadlock: Mutual Exclusion, Hold & Wait, No Preemption, Circular Wait
- Virtual Memory: Paging and Segmentation

### Summary
OS manages hardware resources and program execution.""",

    "cn": """## Computer Networks

### Key Concepts
- OSI Model (7 layers) vs TCP/IP (4 layers)
- TCP (reliable) vs UDP (fast)
- DNS, HTTP/HTTPS, IP addressing

### Summary
Networks enable distributed communication and the internet.""",

    "oop": """## Object-Oriented Programming

### Four Pillars
1. **Encapsulation**  2. **Abstraction**  3. **Inheritance**  4. **Polymorphism**

### Summary
OOP enables modular, reusable software design.""",

    "java": """## Java Programming

### Key Concepts
- JVM, JRE, JDK
- Garbage Collection
- Collections Framework

### Summary
Java powers enterprise apps, Android, and backend systems.""",

    "python": """## Python Programming

### Key Concepts
- Dynamic typing, interpreted execution
- List comprehensions, decorators, generators
- Popular libraries: NumPy, Pandas, Flask, Django

### Summary
Python is versatile for AI, web dev, and automation.""",

    "cpp": """## C++ Programming

### Key Concepts
- Pointers and references
- STL: vector, map, set
- RAII and smart pointers

### Summary
C++ offers high performance with OOP capabilities.""",

    "ai": """## Artificial Intelligence & Machine Learning

### Key Concepts
- Supervised, Unsupervised, Reinforcement Learning
- Bias vs Variance tradeoff
- Neural networks basics

### Summary
AI/ML enables systems to learn from data.""",

    "cloud": """## Cloud Computing

### Service Models
- **IaaS**, **PaaS**, **SaaS**
- Scalability vs Elasticity

### Summary
Cloud delivers on-demand computing resources over the internet.""",

    "cyber": """## Cyber Security

### CIA Triad
Confidentiality, Integrity, Availability

### Summary
Cyber security protects systems from digital threats.""",

    "aptitude": """## Placement & Aptitude Preparation

### Topics
Quantitative Aptitude, Logical Reasoning, Verbal Ability

### Tips
- Use STAR method for behavioral questions
- Keep resume to 1 page with ATS keywords

### Summary
Consistent practice builds placement readiness.""",

    "interviews": """## Interview Preparation

### Structure
1. Technical Round (DSA, DBMS, System Design)
2. HR & Behavioral Round

### Common Questions
- Tell me about yourself
- Why this company?
- Describe a challenge you overcame

### Summary
Preparation and mock interviews build confidence.""",

    "communication": """## Communication Skills

### Focus Areas
- Interview communication (STAR technique)
- Professional email writing
- Group discussion skills

### Summary
Clear communication is essential for career success.""",

    "web_dev": """## Web Development

### Stack
- **Frontend**: HTML, CSS, JavaScript, React
- **Backend**: Node.js, Python (Flask/Django), Java (Spring)
- **APIs**: REST, GraphQL

### Summary
Full-stack skills are highly valued in placements.""",

    "software_engineering": """## Software Engineering

### Key Concepts
- SDLC phases
- Agile / Scrum methodology
- Design Patterns: Singleton, Factory, Observer

### Summary
Engineering principles ensure maintainable software.""",

    "dsa_default": """## Data Structures & Algorithms

### Study Path
1. Arrays, Linked Lists, Stacks, Queues
2. Recursion, Sorting, Searching
3. Trees, Graphs, Dynamic Programming

### Summary
DSA is the core of technical placement interviews.""",

    "general_default": """## Learnix AI Study Assistant

### How I Can Help
- **Core Subjects**: DSA, DBMS, OS, CN, OOP
- **Languages**: Python, Java, C++
- **Career**: Aptitude, Resume tips, Interview strategies

### Try Asking
- *"Explain Binary Trees"*
- *"What is deadlock in OS?"*
- *"Generate quiz on SQL joins"*""",
}


def _search_knowledge_base(query, subject_id=None):
    query_lower = query.lower()

    # 1. Check exact match
    exact_match = KnowledgeBaseAnswer.query.filter(
        db.func.lower(KnowledgeBaseAnswer.question) == query_lower
    ).first()
    if exact_match:
        return exact_match

    # 2. Get all relevant answers
    answers = KnowledgeBaseAnswer.query.all()
    if not answers:
        return None

    # 3. Check keyword match
    best_match = None
    best_score = 0

    for ans in answers:
        score = 0

        # Similarity match
        similarity = difflib.SequenceMatcher(None, query_lower, ans.question.lower()).ratio()
        if similarity > 0.7:
            score += similarity * 5

        # Keyword match
        if ans.keywords:
            keywords = [k.strip().lower() for k in ans.keywords.split(',') if k.strip()]
            for k in keywords:
                if k in query_lower:
                    score += 2

        # Partial question match
        if ans.question.lower() in query_lower or query_lower in ans.question.lower():
            score += 3

        if score > best_score and score >= 1:
            best_score = score
            best_match = ans

    return best_match


def get_chatbot_response(*args, **kwargs):
    user_query = kwargs.get("user_query")
    subject_name = kwargs.get("subject_name")
    history = kwargs.get("history") or []
    new_message = kwargs.get("new_message")
    subject_id = kwargs.get("subject_id")
    user_id = kwargs.get("user_id")

    if args:
        if len(args) == 1:
            user_query = args[0]
        elif len(args) >= 3:
            subject_name = args[0]
            history = args[1]
            new_message = args[2]
            subject_id = args[3] if len(args) >= 4 else subject_id
            user_id = args[4] if len(args) >= 5 else user_id

    query = (user_query or new_message or "").strip()
    if not query:
        return {
            "success": True,
            "source": "system",
            "answer": "## Help\n\nPlease type a question and I'll explain it step-by-step.",
        }

    if subject_name in REMOVED_SUBJECTS:
        return {
            "success": True,
            "source": "system",
            "answer": (
                "## Subject Not Available\n\n"
                "Learnix focuses on **engineering and placement preparation** subjects. "
                "Please select a subject like DSA, DBMS, OS, Python, or Placement Prep."
            ),
        }

    try:
        # Check knowledge base first
        kb_answer = _search_knowledge_base(query, subject_id)
        if kb_answer:
            return {
                "success": True,
                "source": "knowledge_base",
                "answer": kb_answer.answer,
            }

        is_quiz_request = bool(QUIZ_TRIGGERS.search(query))
        topic_context = _extract_conversation_topic(history, query)

        web_context = fetch_web_context(
            f"{subject_name or ''} {topic_context or query}".strip()
        )

        ai_answer = _call_ai(
            subject_name or "Default",
            history,
            query,
            web_context=web_context,
            is_quiz_request=is_quiz_request,
            topic_context=topic_context,
        )

        if ai_answer:
            _log_unanswered_question(query, subject_id, user_id)
            return {
                "success": True,
                "source": "ai",
                "answer": ai_answer,
                "is_quiz": is_quiz_request,
            }

        fallback = _generate_local_fallback(query, subject_name, topic_context)
        return {
            "success": True,
            "source": "knowledge_base",
            "answer": fallback,
            "is_quiz": is_quiz_request,
        }

    except Exception as exc:
        logger.exception("Chatbot error: %s", exc)
        fallback = _generate_local_fallback(query, subject_name, None)
        return {
            "success": True,
            "source": "knowledge_base",
            "answer": fallback,
        }


def _extract_conversation_topic(history, current_query):
    """Derive the active topic from recent conversation for quiz generation."""
    if QUIZ_TRIGGERS.search(current_query):
        relevant = []
        for item in reversed(history[-8:]):
            if item.get("role") == "user":
                text = item.get("content", "").strip()
                if text and not QUIZ_TRIGGERS.search(text):
                    relevant.append(text)
            elif item.get("role") == "assistant" and not relevant:
                content = item.get("content", "")
                match = re.search(r"^##\s+(.+)$", content, re.M)
                if match:
                    return match.group(1).strip()
        if relevant:
            return relevant[0]
    return None


def _generate_local_fallback(query, subject_name, topic_context=None):
    search_text = f"{topic_context or ''} {query}".lower()
    subject_normalized = (subject_name or "").lower()

    topic_map = [
        (["tree", "bst", "binary search tree"], "trees"),
        (["graph", "dfs", "bfs", "dijkstra"], "graphs"),
        (["array", "matrix"], "arrays"),
        (["linked list", "singly", "doubly"], "linked_lists"),
        (["stack", "lifo"], "stacks"),
        (["queue", "fifo", "enqueue"], "queues"),
        (["dbms", "database", "sql", "acid", "normalization"], "dbms"),
        (["operating system", "deadlock", "process", "thread"], "os"),
        (["network", "tcp", "udp", "osi"], "cn"),
        (["oop", "inheritance", "polymorphism"], "oop"),
        (["java"], "java"),
        (["python"], "python"),
        (["c++", "cpp"], "cpp"),
        (["machine learning", "ml", "artificial intelligence"], "ai"),
        (["cloud", "aws", "azure"], "cloud"),
        (["cyber", "security", "encryption"], "cyber"),
        (["aptitude", "placement", "resume"], "aptitude"),
        (["interview"], "interviews"),
        (["communication"], "communication"),
        (["web dev", "html", "css", "javascript"], "web_dev"),
        (["software engineering", "sdlc"], "software_engineering"),
    ]

    for keywords, key in topic_map:
        if any(k in search_text for k in keywords):
            return FALLBACK_LIBRARY[key]

    if any(k in subject_normalized for k in ["data structure", "algorithm", "dsa"]):
        return FALLBACK_LIBRARY["dsa_default"]
    if "dbms" in subject_normalized or "database" in subject_normalized:
        return FALLBACK_LIBRARY["dbms"]
    if "operating" in subject_normalized or subject_normalized == "os":
        return FALLBACK_LIBRARY["os"]
    if "network" in subject_normalized:
        return FALLBACK_LIBRARY["cn"]
    if "placement" in subject_normalized or "interview" in subject_normalized:
        return FALLBACK_LIBRARY["aptitude"]

    return FALLBACK_LIBRARY["general_default"]


def _call_ai(subject_name, history, new_message, web_context=None,
             is_quiz_request=False, topic_context=None):
    base_prompt = SYSTEM_PROMPTS.get(subject_name, SYSTEM_PROMPTS["Default"])
    system_prompt = f"{base_prompt}\n\n{LEARNIX_GLOBAL_INSTRUCTIONS}"

    if is_quiz_request and topic_context:
        system_prompt += (
            f"\n\nThe user wants a quiz on the topic discussed earlier: **{topic_context}**. "
            "Generate the quiz specifically about this topic from the conversation."
        )

    messages = [{"role": "system", "content": system_prompt}]
    for item in history[-12:]:
        messages.append({
            "role": item.get("role", "user"),
            "content": item.get("content", ""),
        })
    messages.append({"role": "user", "content": new_message})

    if ai_client.is_available():
        response = ai_client.get_completion(
            messages,
            use_search=True,
            web_context=web_context,
            temperature=0.7,
        )
        if response:
            return response

    return None


def _log_unanswered_question(question, subject_id, user_id):
    try:
        existing = UnansweredQuestion.query.filter_by(
            question=question,
            subject_id=subject_id,
            is_resolved=False,
        ).first()
        if existing:
            return
        db.session.add(UnansweredQuestion(
            question=question,
            subject_id=subject_id,
            user_id=user_id,
        ))
        db.session.commit()
    except Exception:
        logger.exception("Error logging unanswered question")
        db.session.rollback()


def get_chatbot_reply(subject_name, history, new_message, **kwargs):
    result = get_chatbot_response(
        subject_name=subject_name,
        history=history,
        new_message=new_message,
        **kwargs,
    )
    return result.get("answer") or _generate_local_fallback(new_message, subject_name, None)
