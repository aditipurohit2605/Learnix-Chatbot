import json
import os
import uuid
from datetime import date, datetime
from .ai_client import ai_client

PLACEMENT_MODULES = {
    "aptitude": {"name": "Aptitude Preparation", "icon": "fa-calculator", "topics": ["Number Systems", "Percentages", "Ratios", "Time & Work", "Profit & Loss"]},
    "logical": {"name": "Logical Reasoning", "icon": "fa-puzzle-piece", "topics": ["Series", "Blood Relations", "Direction Sense", "Coding-Decoding", "Syllogisms"]},
    "quantitative": {"name": "Quantitative Aptitude", "icon": "fa-square-root-alt", "topics": ["Algebra", "Geometry", "Probability", "Permutations", "Statistics"]},
    "verbal": {"name": "Verbal Ability", "icon": "fa-spell-check", "topics": ["Reading Comprehension", "Synonyms", "Antonyms", "Grammar", "Para Jumbles"]},
    "data_interpretation": {"name": "Data Interpretation", "icon": "fa-chart-bar", "topics": ["Bar Graphs", "Pie Charts", "Tables", "Line Graphs", "Mixed DI"]},
    "puzzle": {"name": "Puzzle Solving", "icon": "fa-cubes", "topics": ["Seating Arrangement", "Floor Puzzles", "Box Puzzles", "Scheduling", "Logical Puzzles"]},
}

DSA_TOPICS = {
    "arrays": {"name": "Arrays", "icon": "fa-th", "order": 1},
    "strings": {"name": "Strings", "icon": "fa-font", "order": 2},
    "linked_lists": {"name": "Linked Lists", "icon": "fa-link", "order": 3},
    "stacks": {"name": "Stacks", "icon": "fa-layer-group", "order": 4},
    "queues": {"name": "Queues", "icon": "fa-stream", "order": 5},
    "trees": {"name": "Trees", "icon": "fa-sitemap", "order": 6},
    "graphs": {"name": "Graphs", "icon": "fa-project-diagram", "order": 7},
    "dynamic_programming": {"name": "Dynamic Programming", "icon": "fa-table", "order": 8},
    "recursion": {"name": "Recursion", "icon": "fa-redo", "order": 9},
    "greedy": {"name": "Greedy Algorithms", "icon": "fa-bolt", "order": 10},
}

TECH_INTERVIEW_TOPICS = ["DBMS", "OOP", "Operating System", "Computer Networks", "SQL", "AI/ML", "Web Development"]
HR_INTERVIEW_TOPICS = [
    "Tell me about yourself", "Strengths and weaknesses", "Why should we hire you",
    "Project explanation", "Leadership questions"
]

COMPANIES = {
    "tcs": {"name": "TCS", "pattern": "Aptitude + Technical + HR", "focus": ["Quantitative", "Verbal", "C/Java basics", "DBMS"]},
    "infosys": {"name": "Infosys", "pattern": "Online Test + Technical + HR", "focus": ["Logical Reasoning", "Pseudo Code", "OOP", "SQL"]},
    "wipro": {"name": "Wipro", "pattern": "Aptitude + Coding + Interview", "focus": ["Verbal", "Quant", "Basic Programming", "Projects"]},
    "accenture": {"name": "Accenture", "pattern": "Cognitive + Coding + Communication", "focus": ["Communication", "Logical", "Coding Fundamentals"]},
    "cognizant": {"name": "Cognizant", "pattern": "Aptitude + Technical + HR", "focus": ["Quantitative", "Verbal", "Technical MCQs", "Projects"]},
    "amazon": {"name": "Amazon", "pattern": "OA + LP + Technical", "focus": ["DSA", "System Design basics", "Leadership Principles", "Behavioral"]},
    "microsoft": {"name": "Microsoft", "pattern": "OA + Technical Rounds", "focus": ["DSA", "Problem Solving", "OOP", "Projects"]},
    "google": {"name": "Google", "pattern": "Phone Screen + Onsite", "focus": ["Advanced DSA", "System Design", "Googleyness", "Communication"]},
}

CAREER_PATHS = {
    "software_engineer": {"name": "Software Engineer", "icon": "fa-laptop-code"},
    "data_scientist": {"name": "Data Scientist", "icon": "fa-chart-line"},
    "ai_engineer": {"name": "AI Engineer", "icon": "fa-robot"},
    "full_stack": {"name": "Full Stack Developer", "icon": "fa-code"},
    "cyber_security": {"name": "Cyber Security", "icon": "fa-shield-alt"},
    "cloud_engineer": {"name": "Cloud Engineer", "icon": "fa-cloud"},
    "devops_engineer": {"name": "DevOps Engineer", "icon": "fa-cogs"},
}

COMPANY_QUESTIONS = {
    "tcs": ["Explain difference between stack and queue.", "What is normalization in DBMS?", "Find LCM of two numbers.", "Tell me about a team project."],
    "infosys": ["Write pseudo code for palindrome check.", "Explain inheritance in OOP.", "What is a primary key?", "Why Infosys?"],
    "amazon": ["Design a parking lot system.", "Explain time complexity of merge sort.", "Tell me about a time you failed.", "Customer obsession example."],
    "google": ["Find median of two sorted arrays.", "Explain BFS vs DFS.", "Design URL shortener.", "Tell me about yourself."],
}

FALLBACK_PLACEMENT_QUESTIONS = {
    "aptitude": [
        {"question_text": "If 20% of a number is 40, what is the number?", "question_type": "mcq", "option_a": "100", "option_b": "200", "option_c": "400", "option_d": "800", "correct_answer": "B", "explanation": "20% of x = 40, so x = 40/0.2 = 200."},
        {"question_text": "A train 120m long passes a pole in 6 seconds. Speed of train?", "question_type": "mcq", "option_a": "20 m/s", "option_b": "72 km/h", "option_c": "Both A and B", "option_d": "60 km/h", "correct_answer": "C", "explanation": "Speed = 120/6 = 20 m/s = 72 km/h."},
    ],
    "logical": [
        {"question_text": "Complete the series: 2, 6, 12, 20, ?", "question_type": "mcq", "option_a": "28", "option_b": "30", "option_c": "32", "option_d": "36", "correct_answer": "B", "explanation": "Differences: 4, 6, 8, 10 → next is 30."},
    ],
    "quantitative": [
        {"question_text": "What is the probability of getting a head when tossing a fair coin?", "question_type": "mcq", "option_a": "0.25", "option_b": "0.5", "option_c": "0.75", "option_d": "1", "correct_answer": "B", "explanation": "A fair coin has 2 equally likely outcomes."},
    ],
    "verbal": [
        {"question_text": "Choose the synonym of 'Abundant'.", "question_type": "mcq", "option_a": "Scarce", "option_b": "Plentiful", "option_c": "Tiny", "option_d": "Weak", "correct_answer": "B", "explanation": "Abundant means existing in large quantities; plentiful is a synonym."},
    ],
    "data_interpretation": [
        {"question_text": "If sales increased from 100 to 150, what is the percentage increase?", "question_type": "mcq", "option_a": "25%", "option_b": "50%", "option_c": "75%", "option_d": "150%", "correct_answer": "B", "explanation": "Increase = 50; percentage = 50/100 × 100 = 50%."},
    ],
    "puzzle": [
        {"question_text": "5 people sit in a row. A is not at either end. B is left of C. Who can be at the center?", "question_type": "mcq", "option_a": "A only", "option_b": "B only", "option_c": "A or B", "option_d": "C only", "correct_answer": "C", "explanation": "A can be center (positions 2-4); B can also be center depending on arrangement."},
    ],
}

FALLBACK_CODING_QUESTIONS = {
    "arrays": {"question_text": "Find the maximum element in an array.", "difficulty": "easy", "hint": "Iterate and track max.", "solution": "def max_element(arr):\n    return max(arr) if arr else None"},
    "strings": {"question_text": "Check if a string is a palindrome.", "difficulty": "easy", "hint": "Compare with reversed string.", "solution": "def is_palindrome(s):\n    s = s.lower().replace(' ', '')\n    return s == s[::-1]"},
    "linked_lists": {"question_text": "Reverse a linked list.", "difficulty": "medium", "hint": "Use three pointers: prev, curr, next.", "solution": "def reverse(head):\n    prev, curr = None, head\n    while curr:\n        nxt = curr.next\n        curr.next = prev\n        prev, curr = curr, nxt\n    return prev"},
    "stacks": {"question_text": "Validate parentheses using a stack.", "difficulty": "easy", "hint": "Push opening, pop on closing.", "solution": "Use stack to match brackets."},
    "queues": {"question_text": "Implement queue using two stacks.", "difficulty": "medium", "hint": "Use one stack for enqueue, one for dequeue.", "solution": "Classic two-stack queue design."},
    "trees": {"question_text": "Perform inorder traversal of a binary tree.", "difficulty": "easy", "hint": "Left, Root, Right recursively.", "solution": "def inorder(node):\n    if node:\n        inorder(node.left)\n        print(node.val)\n        inorder(node.right)"},
    "graphs": {"question_text": "Detect cycle in an undirected graph.", "difficulty": "medium", "hint": "Use DFS with parent tracking.", "solution": "DFS-based cycle detection."},
    "dynamic_programming": {"question_text": "Find nth Fibonacci number using DP.", "difficulty": "easy", "hint": "Bottom-up with memoization.", "solution": "dp[0]=0, dp[1]=1, dp[i]=dp[i-1]+dp[i-2"},
    "recursion": {"question_text": "Calculate factorial recursively.", "difficulty": "easy", "hint": "Base case n<=1.", "solution": "def fact(n):\n    return 1 if n <= 1 else n * fact(n-1)"},
    "greedy": {"question_text": "Activity selection problem.", "difficulty": "medium", "hint": "Sort by finish time, pick non-overlapping.", "solution": "Greedy selection by earliest finish."},
}


def generate_placement_quiz(module, topic=None, difficulty='medium', num_questions=5):
    module_info = PLACEMENT_MODULES.get(module, {})
    module_name = module_info.get('name', module)
    topic_str = topic or (module_info.get('topics', ['General'])[0])

    if ai_client.is_available():
        try:
            prompt = (
                f"Generate {num_questions} multiple choice placement aptitude questions for "
                f"{module_name} - topic: {topic_str}, difficulty: {difficulty}. "
                f"Return ONLY a JSON array with objects having: question_text, question_type (mcq), "
                f"option_a, option_b, option_c, option_d, correct_answer (A/B/C/D), explanation."
            )
            messages = [{"role": "system", "content": "You are a placement test question generator. Return valid JSON only."},
                        {"role": "user", "content": prompt}]
            reply = ai_client.get_completion(messages, temperature=0.8, max_tokens=2000)
            start = reply.find('[')
            end = reply.rfind(']') + 1
            if start >= 0 and end > start:
                return json.loads(reply[start:end])
        except Exception:
            pass

    base = FALLBACK_PLACEMENT_QUESTIONS.get(module, FALLBACK_PLACEMENT_QUESTIONS['aptitude'])
    return base[:num_questions]


def get_coding_explanation(topic, question=None):
    topic_info = DSA_TOPICS.get(topic, {"name": topic})
    topic_name = topic_info.get('name', topic)
    fallback = FALLBACK_CODING_QUESTIONS.get(topic, FALLBACK_CODING_QUESTIONS['arrays'])

    if ai_client.is_available():
        try:
            q = question or fallback['question_text']
            messages = [
                {"role": "system", "content": f"You are a DSA tutor explaining {topic_name} concepts clearly with examples and code."},
                {"role": "user", "content": f"Explain this problem and provide a solution with time/space complexity:\n{q}"}
            ]
            return ai_client.get_completion(messages, max_tokens=1500)
        except Exception:
            pass

    return (
        f"### {topic_name}: {fallback['question_text']}\n\n"
        f"**Difficulty:** {fallback['difficulty']}\n\n"
        f"**Hint:** {fallback['hint']}\n\n"
        f"**Solution:**\n```python\n{fallback['solution']}\n```"
    )


def get_coding_practice(topic, difficulty='medium'):
    fallback = FALLBACK_CODING_QUESTIONS.get(topic, FALLBACK_CODING_QUESTIONS['arrays'])
    if ai_client.is_available():
        try:
            topic_name = DSA_TOPICS.get(topic, {}).get('name', topic)
            messages = [
                {"role": "system", "content": "Generate one coding practice problem. Return JSON with question_text, hint, difficulty."},
                {"role": "user", "content": f"Generate a {difficulty} {topic_name} practice problem."}
            ]
            reply = ai_client.get_completion(messages, max_tokens=800)
            start = reply.find('{')
            end = reply.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(reply[start:end])
                data['solution'] = fallback.get('solution', '')
                return data
        except Exception:
            pass
    return {**fallback, 'difficulty': difficulty}


def start_mock_interview(interview_type, topic):
    questions = []
    if interview_type == 'technical':
        pool = TECH_INTERVIEW_TOPICS
        topic = topic or pool[0]
        questions = [f"Explain {topic} concepts relevant to interviews.", f"What are common {topic} interview questions?", f"Describe a real-world use case of {topic}."]
    else:
        pool = HR_INTERVIEW_TOPICS
        topic = topic or pool[0]
        questions = [topic, "Describe a challenging situation you handled.", "Where do you see yourself in 5 years?"]

    if ai_client.is_available():
        try:
            messages = [
                {"role": "system", "content": "You are a professional interviewer. Generate 3 interview questions."},
                {"role": "user", "content": f"Generate 3 {interview_type} interview questions for topic: {topic}. Return JSON array of strings."}
            ]
            reply = ai_client.get_completion(messages, max_tokens=600)
            start = reply.find('[')
            end = reply.rfind(']') + 1
            if start >= 0 and end > start:
                questions = json.loads(reply[start:end])
        except Exception:
            pass

    return {"questions": questions[:3], "topic": topic, "type": interview_type}


def evaluate_interview_answer(question, answer, interview_type, topic):
    confidence = 50.0
    feedback = "Good effort! Keep practicing to improve clarity and depth."

    if ai_client.is_available():
        try:
            messages = [
                {"role": "system", "content": "You are an interview coach. Evaluate answers and give constructive feedback. Return JSON with feedback (string) and confidence_score (0-100)."},
                {"role": "user", "content": f"Interview type: {interview_type}, Topic: {topic}\nQuestion: {question}\nAnswer: {answer}"}
            ]
            reply = ai_client.get_completion(messages, max_tokens=800)
            start = reply.find('{')
            end = reply.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(reply[start:end])
                return data.get('feedback', feedback), float(data.get('confidence_score', confidence))
        except Exception:
            pass

    word_count = len(answer.split()) if answer else 0
    if word_count > 50:
        confidence = 75.0
        feedback = "Solid answer with good detail. Add specific examples to stand out."
    elif word_count > 20:
        confidence = 60.0
        feedback = "Decent response. Expand with metrics, outcomes, and STAR format."
    else:
        confidence = 35.0
        feedback = "Answer is too brief. Structure using Situation, Task, Action, Result."

    return feedback, confidence


def generate_resume_content(name, education, skills, projects, experience, achievements):
    content = f"# {name}\n\n## Education\n{education}\n\n## Skills\n{skills}\n\n## Projects\n{projects}\n\n## Experience\n{experience}\n\n## Achievements\n{achievements}"

    if ai_client.is_available():
        try:
            messages = [
                {"role": "system", "content": "Create an ATS-friendly professional resume in clean markdown format. Use action verbs and quantify achievements."},
                {"role": "user", "content": f"Create resume for:\nName: {name}\nEducation: {education}\nSkills: {skills}\nProjects: {projects}\nExperience: {experience}\nAchievements: {achievements}"}
            ]
            content = ai_client.get_completion(messages, max_tokens=2000)
        except Exception:
            pass

    return content


def score_resume(name, education, skills, projects, experience, achievements, content=None):
    score = 40
    checks = []
    if name and len(name.strip()) > 2:
        score += 10
        checks.append("Name present")
    if education and len(education.strip()) > 20:
        score += 15
        checks.append("Education detailed")
    if skills and len(skills.split(',')) >= 3:
        score += 15
        checks.append("Skills listed")
    if projects and len(projects.strip()) > 30:
        score += 10
        checks.append("Projects included")
    if experience and len(experience.strip()) > 20:
        score += 5
        checks.append("Experience added")
    if achievements and len(achievements.strip()) > 10:
        score += 5
        checks.append("Achievements highlighted")
    if content and len(content) > 200:
        score = min(100, score + 10)
        checks.append("ATS-friendly formatting")

    return min(100, score), checks


def generate_career_roadmap(career_path):
    path_info = CAREER_PATHS.get(career_path, {"name": career_path.replace('_', ' ').title()})
    path_name = path_info.get('name', career_path)

    default_roadmap = {
        "phases": [
            {"name": "Foundation", "duration": "2-3 months", "skills": ["Programming basics", "Data Structures", "Git"], "status": "pending"},
            {"name": "Core Skills", "duration": "3-4 months", "skills": ["Advanced DSA", "System basics", "Projects"], "status": "pending"},
            {"name": "Specialization", "duration": "2-3 months", "skills": [f"{path_name} tools", "Portfolio", "Certifications"], "status": "pending"},
            {"name": "Placement Ready", "duration": "1-2 months", "skills": ["Resume", "Mock interviews", "Applications"], "status": "pending"},
        ],
        "courses": [
            {"name": f"Introduction to {path_name}", "platform": "Coursera", "duration": "4 weeks"},
            {"name": "Data Structures & Algorithms", "platform": "LeetCode", "duration": "8 weeks"},
            {"name": f"{path_name} Specialization", "platform": "LinkedIn Learning", "duration": "6 weeks"},
        ]
    }

    if ai_client.is_available():
        try:
            messages = [
                {"role": "system", "content": "Create a career roadmap. Return JSON with phases (array of {name, duration, skills, status}) and courses (array of {name, platform, duration})."},
                {"role": "user", "content": f"Create a detailed learning roadmap for becoming a {path_name}."}
            ]
            reply = ai_client.get_completion(messages, max_tokens=1500)
            start = reply.find('{')
            end = reply.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(reply[start:end])
        except Exception:
            pass

    return default_roadmap


def generate_resume_pdf(content, name, upload_folder):
    try:
        from fpdf import FPDF
    except ImportError:
        return None

    os.makedirs(os.path.join(upload_folder, 'resumes'), exist_ok=True)
    filename = f"resume_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(upload_folder, 'resumes', filename)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=12)

    for line in content.split('\n'):
        line = line.strip()
        if not line:
            pdf.ln(4)
            continue
        if line.startswith('# '):
            pdf.set_font("Helvetica", 'B', 16)
            pdf.cell(0, 10, line[2:], ln=True)
            pdf.set_font("Helvetica", size=12)
        elif line.startswith('## '):
            pdf.set_font("Helvetica", 'B', 14)
            pdf.cell(0, 8, line[3:], ln=True)
            pdf.set_font("Helvetica", size=12)
        else:
            safe_line = line.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 6, safe_line)

    pdf.output(filepath)
    return filepath


def calculate_readiness_scores(user_id, db_session, models):
    """Calculate placement, coding, interview, and resume readiness scores."""
    PlacementProgress = models['PlacementProgress']
    CodingProgress = models['CodingProgress']
    InterviewHistory = models['InterviewHistory']
    Resume = models['Resume']
    QuizResult = models['QuizResult']

    placement_records = PlacementProgress.query.filter_by(user_id=user_id).all()
    if placement_records:
        placement_score = int(sum(
            (r.score / r.total_questions * 100) if r.total_questions > 0 else 0
            for r in placement_records
        ) / len(placement_records))
    else:
        placement_score = 0

    coding_records = CodingProgress.query.filter_by(user_id=user_id).all()
    if coding_records:
        coding_score = int(sum(r.score_avg for r in coding_records) / len(coding_records))
    else:
        coding_score = 0

    interviews = InterviewHistory.query.filter_by(user_id=user_id).all()
    if interviews:
        interview_score = int(sum(i.confidence_score for i in interviews) / len(interviews))
    else:
        interview_score = 0

    resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.updated_at.desc()).first()
    resume_score = resume.resume_score if resume else 0

    quiz_results = QuizResult.query.filter_by(user_id=user_id).all()
    subject_performance = {}
    for r in quiz_results:
        from models.models import Quiz
        quiz = Quiz.query.get(r.quiz_id)
        if quiz and quiz.subject:
            sub = quiz.subject.name
            pct = int((r.score / r.total_questions) * 100) if r.total_questions > 0 else 0
            if sub not in subject_performance:
                subject_performance[sub] = []
            subject_performance[sub].append(pct)

    subject_avg = {k: int(sum(v) / len(v)) for k, v in subject_performance.items()}

    return {
        "placement_readiness": placement_score,
        "coding_readiness": coding_score,
        "interview_readiness": interview_score,
        "resume_score": resume_score,
        "subject_performance": subject_avg,
        "overall_readiness": int((placement_score + coding_score + interview_score + resume_score) / 4) if any([placement_score, coding_score, interview_score, resume_score]) else 0
    }


def get_placement_weak_topics(user_id, db_session, PlacementProgress):
    records = PlacementProgress.query.filter_by(user_id=user_id).all()
    weak = {}
    for r in records:
        if r.total_questions > 0 and (r.score / r.total_questions) < 0.6:
            mod = r.module
            if mod not in weak:
                weak[mod] = []
            weak[mod].append({"topic": r.topic, "score_pct": int(r.score / r.total_questions * 100)})
    return weak


def get_company_experiences(company_key):
    experiences = {
        "tcs": ["Focus on aptitude speed. Technical round was mostly C and DBMS basics.", "HR asked about relocation and career goals."],
        "amazon": ["Online assessment had 2 coding + MCQs. LP round uses STAR method.", "System design at senior levels; DSA heavy for SDE."],
        "google": ["Phone screen: medium DSA. Onsite: 4-5 rounds mixing coding and design.", "Communication and structured thinking matter as much as code."],
    }
    return experiences.get(company_key, ["Research company-specific patterns.", "Practice aptitude and technical rounds.", "Prepare project stories for HR."])
