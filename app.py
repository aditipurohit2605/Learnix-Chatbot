import os
from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from models import db
from models.models import (
    User, Subject, StudentProfile, Conversation,
    ChatHistory, WeakTopic, Quiz, QuizQuestion, QuizResult,
    DailyChallenge, KnowledgeBaseAnswer
)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    # Fetch active, non-deleted users
    return User.query.filter_by(id=int(user_id), is_deleted=False).first()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize config requirements (like folders)
    config_class.init_app(app)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.admin import admin_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    @app.context_processor
    def inject_avatar_helpers():
        def has_custom_avatar(user):
            return user and user.avatar and user.avatar != 'default_avatar.png'

        def user_initials(user):
            if not user or not user.username:
                return '?'
            return user.username[:2].upper()

        return dict(has_custom_avatar=has_custom_avatar, user_initials=user_initials)

    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Database setup and seed data
    with app.app_context():
        db.create_all()
        seed_database()

    return app

def seed_database():
    allowed_subjects = [
        {"name": "Data Structures & Algorithms", "code": "DSA"},
        {"name": "Object Oriented Programming", "code": "OOP"},
        {"name": "Database Management Systems", "code": "DBMS"},
        {"name": "Operating Systems", "code": "OS"},
        {"name": "Computer Networks", "code": "CN"},
        {"name": "Software Engineering", "code": "SE"},
        {"name": "Python Programming", "code": "PYTHON"},
        {"name": "Java Programming", "code": "JAVA"},
        {"name": "C Programming", "code": "C"},
        {"name": "C++ Programming", "code": "CPP"},
        {"name": "Web Development", "code": "WEB"},
        {"name": "Artificial Intelligence", "code": "AI"},
        {"name": "Machine Learning", "code": "ML"},
        {"name": "Data Science", "code": "DS"},
        {"name": "Cloud Computing", "code": "CLOUD"},
        {"name": "Cyber Security", "code": "CYBER"},
        {"name": "DevOps", "code": "DEVOPS"},
        {"name": "System Design", "code": "SYSTEM"},
        {"name": "Generative AI", "code": "GENAI"},
        {"name": "Placement Prep", "code": "PLACEMENT"},
        {"name": "Interview Prep", "code": "INTERVIEW"},
        {"name": "Communication Skills", "code": "COMM"},
        {"name": "Resume Help", "code": "RESUME"},
        {"name": "Career Guidance", "code": "CAREER"}
    ]
    allowed_names = {sub["name"] for sub in allowed_subjects}
    allowed_codes = {sub["code"] for sub in allowed_subjects}

    # Delete subjects NOT in the allowed list and their related entities
    all_subjects = Subject.query.all()
    with db.session.no_autoflush:
        for s in all_subjects:
            if s.name not in allowed_names or s.code not in allowed_codes:
                convs = Conversation.query.filter_by(subject_id=s.id).all()
                for c in convs:
                    ChatHistory.query.filter_by(conversation_id=c.id).delete(synchronize_session=False)
                    db.session.delete(c)

                WeakTopic.query.filter_by(subject_id=s.id).delete(synchronize_session=False)
                KnowledgeBaseAnswer.query.filter_by(subject_id=s.id).delete(synchronize_session=False)

                quizzes = Quiz.query.filter_by(subject_id=s.id).all()
                for q in quizzes:
                    DailyChallenge.query.filter_by(quiz_id=q.id).delete(synchronize_session=False)
                    QuizResult.query.filter_by(quiz_id=q.id).delete(synchronize_session=False)
                    QuizQuestion.query.filter_by(quiz_id=q.id).delete(synchronize_session=False)
                    db.session.delete(q)

                db.session.delete(s)

    db.session.commit()

    # Seed allowed subjects
    subject_map = {}
    for sub in allowed_subjects:
        existing = Subject.query.filter_by(code=sub["code"]).first()
        if not existing:
            new_sub = Subject(name=sub["name"], code=sub["code"], is_custom=False)
            db.session.add(new_sub)
            db.session.flush()
            subject_map[sub["code"]] = new_sub
        else:
            existing.name = sub["name"]
            existing.is_deleted = False
            subject_map[sub["code"]] = existing

    # Seed Default Admin User
    admin_user = User.query.filter_by(role='admin').first()
    if not admin_user:
        admin = User(
            username="admin",
            email="admin@learnix.com",
            role="admin"
        )
        admin.set_password("adminpassword")
        db.session.add(admin)
        
    # Seed Default Student User
    student_user = User.query.filter_by(username='student').first()
    if not student_user:
        student = User(
            username="student",
            email="student@learnix.com",
            role="student"
        )
        student.set_password("studentpassword")
        db.session.add(student)
        db.session.flush()
        
        # Create profile for the student
        profile = StudentProfile(
            user_id=student.id,
            bio="Let's learn smarter with AI!",
            total_points=120,
            current_streak=3,
            max_streak=5
        )
        db.session.add(profile)

    # Seed knowledge base
    seed_knowledge_base(subject_map)
        
    try:
        db.session.commit()
        print("Database seeded successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding database: {e}")


def seed_knowledge_base(subject_map):
    from models.models import KnowledgeBaseAnswer

    kb_entries = [
        {
            "subject_code": "DBMS",
            "question": "What is DBMS?",
            "keywords": "dbms, database management system, definition",
            "answer": "## Database Management System (DBMS)\n\nA **DBMS** is a software system that allows users to define, create, maintain, and control access to databases.\n\n### Key Functions\n- Define database schema\n- Insert, update, delete, and retrieve data\n- Ensure data integrity and security\n- Manage concurrent access\n- Provide backup and recovery\n\n### Examples\nMySQL, PostgreSQL, Oracle, SQL Server, MongoDB"
        },
        {
            "subject_code": "DBMS",
            "question": "What are ACID properties?",
            "keywords": "acid properties, transaction, database",
            "answer": "## ACID Properties\n\nACID is a set of properties that guarantee reliable database transactions:\n\n### 1. Atomicity\n- All or nothing\n- Either entire transaction succeeds or fails completely\n\n### 2. Consistency\n- Database moves from one valid state to another\n- All constraints are satisfied\n\n### 3. Isolation\n- Concurrent execution of transactions is isolated\n- Intermediate states are not visible to other transactions\n\n### 4. Durability\n- Committed changes are permanent\n- Survive system failures"
        },
        {
            "subject_code": "DSA",
            "question": "What is an algorithm?",
            "keywords": "algorithm, definition, dsa",
            "answer": "## Algorithm\n\nAn **algorithm** is a step-by-step set of well-defined instructions to solve a specific problem or perform a specific task.\n\n### Properties\n1. Input: 0 or more inputs\n2. Output: at least one output\n3. Definiteness: clear and unambiguous steps\n4. Finiteness: terminates after finite steps\n5. Effectiveness: each step is basic and executable\n\n### Example\nLinear Search: Check each element in order until target is found"
        },
        {
            "subject_code": "DSA",
            "question": "Explain Floyd Warshall algorithm",
            "keywords": "floyd warshall, algorithm, shortest path",
            "answer": "## Floyd-Warshall Algorithm\n\nThe Floyd-Warshall algorithm is a **dynamic programming** algorithm that finds the **shortest paths between all pairs of vertices** in a weighted graph (positive or negative edge weights, but no negative cycles).\n\n### Approach\n- Uses a 2D array `dist[][]` where `dist[i][j]` is distance from i to j\n- Gradually includes intermediate vertices to find shorter paths\n- Formula: `dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])`\n\n### Time Complexity\n**O(V³)**, where V is number of vertices\n\n### Use Cases\n- Finding all-pairs shortest paths in dense graphs\n- Detecting negative cycles\n\n### Example\n```python\ndef floyd_warshall(graph, V):\n    dist = [[0]*V for _ in range(V)]\n    for i in range(V):\n        for j in range(V):\n            dist[i][j] = graph[i][j]\n    \n    for k in range(V):\n        for i in range(V):\n            for j in range(V):\n                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])\n    \n    return dist\n```"
        },
        {
            "subject_code": "DSA",
            "question": "What is a linked list?",
            "keywords": "linked list, data structure",
            "answer": "## Linked List\n\nA **linked list** is a linear data structure where elements are stored in **nodes**, and each node contains a data field and a reference (pointer/link) to the next node in the sequence.\n\n### Types\n1. **Singly Linked List**: Each node has data and next pointer\n2. **Doubly Linked List**: Each node has data, next, and prev pointers\n3. **Circular Linked List**: Last node points back to head\n\n### Advantages\n- Dynamic size\n- Efficient insertion/deletion at beginning/end (O(1) with head/tail)\n\n### Disadvantages\n- No random access (O(n) to access nth element)\n- Extra memory for pointers\n\n### Example Node\n```python\nclass Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n```"
        },
        {
            "subject_code": "OS",
            "question": "What is a process?",
            "keywords": "process, operating system, os",
            "answer": "## Process\n\nA **process** is a **program in execution**.\n\n### Components of a Process\n1. **Program Counter**: Address of next instruction to execute\n2. **Stack**: Local variables, function call frames\n3. **Data Section**: Global variables\n4. **Heap**: Dynamic memory allocation\n\n### Process States\n- New: Process being created\n- Ready: Waiting to be assigned to CPU\n- Running: Instructions being executed\n- Waiting: Waiting for event (I/O, etc.)\n- Terminated: Process finished execution\n\n### Process Control Block (PCB)\nData structure that stores all process information (state, registers, PID, etc.)"
        },
        {
            "subject_code": "OS",
            "question": "What is a deadlock?",
            "keywords": "deadlock, operating system, synchronization",
            "answer": "## Deadlock\n\nA **deadlock** is a situation where a set of processes are blocked indefinitely because each process is holding a resource and waiting for another resource held by another process in the set.\n\n### Four Necessary Conditions (Coffman Conditions)\n1. **Mutual Exclusion**: Only one process can use a resource at a time\n2. **Hold and Wait**: Process holds resources while waiting for others\n3. **No Preemption**: Resources can't be forcefully taken away; must be released voluntarily\n4. **Circular Wait**: Processes form a cycle waiting for each other\n\n### Handling Deadlocks\n- Prevention: Break one of the four conditions\n- Avoidance: Safe state (Banker's algorithm)\n- Detection and Recovery: Detect and recover (kill process, preempt resource)\n- Ignore: Pretend deadlocks never happen (most OS)"
        }
    ]

    for entry in kb_entries:
        existing = KnowledgeBaseAnswer.query.filter_by(
            question=entry["question"],
            subject_id=subject_map.get(entry["subject_code"]).id if subject_map.get(entry["subject_code"]) else None
        ).first()
        if not existing:
            kb_answer = KnowledgeBaseAnswer(
                subject_id=subject_map.get(entry["subject_code"]).id if subject_map.get(entry["subject_code"]) else None,
                question=entry["question"],
                keywords=entry["keywords"],
                answer=entry["answer"]
            )
            db.session.add(kb_answer)
            db.session.flush()
    db.session.commit()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
