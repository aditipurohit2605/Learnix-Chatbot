import json
from models import db
from models.models import QuizResult, Quiz, WeakTopic, Subject

SUGGESTED_PLANS = {
    "DSA": [
        "Review linked list operations and solve 2 practice problems.",
        "Recap time and space complexity of common sorting algorithms.",
        "Use Learnix Chatbot to explain step-by-step problem solving."
    ],
    "DBMS": [
        "Practice writing SQL queries for joins and subqueries.",
        "Review normalization forms (1NF to 3NF).",
        "Use Learnix Chatbot to explain database concepts."
    ],
    "OS": [
        "Review process scheduling algorithms with examples.",
        "Practice deadlock detection and prevention scenarios.",
        "Use Learnix Chatbot to clarify operating system concepts."
    ],
    "CN": [
        "Recap OSI model layers and their functions.",
        "Practice TCP/IP protocol suite concepts.",
        "Use Learnix Chatbot for computer network explanations."
    ],
    "COMM": [
        "Practice HR interview questions daily.",
        "Work on professional email writing exercises.",
        "Use Learnix Chatbot to improve your communication skills."
    ],
    "Default": [
        "Discuss confusing concepts with the Learnix AI Assistant.",
        "Read uploaded study materials in detail.",
        "Create summaries of your notes using the Summarizer tool."
    ]
}

def analyze_student_performance(user_id):
    """
    Evaluates user's QuizResults. If performance is low, identifies weak topic areas.
    """
    # Fetch all quiz results for the user
    results = QuizResult.query.filter_by(user_id=user_id).all()
    if not results:
        return []
        
    subject_scores = {} # maps subject_id -> list of scores
    
    for r in results:
        quiz = Quiz.query.get(r.quiz_id)
        if not quiz:
            continue
        sub_id = quiz.subject_id
        if sub_id not in subject_scores:
            subject_scores[sub_id] = []
        # Calculate percentage
        percent = (r.score / r.total_questions) * 100 if r.total_questions > 0 else 0
        subject_scores[sub_id].append(percent)
        
    # Analyze scores per subject
    updated_weak_topics = []
    for sub_id, scores in subject_scores.items():
        avg_score = sum(scores) / len(scores)
        
        # If average score is less than 70%, mark as a weak topic
        if avg_score < 70.0:
            subject = Subject.query.get(sub_id)
            if not subject:
                continue
                
            # Find or create WeakTopic
            weak = WeakTopic.query.filter_by(user_id=user_id, subject_id=sub_id).first()
            
            # Formulate topic suggestions
            plans = SUGGESTED_PLANS.get(subject.code, SUGGESTED_PLANS["Default"])
            
            if not weak:
                weak = WeakTopic(
                    user_id=user_id,
                    subject_id=sub_id,
                    topic_name=f"General {subject.name} Review",
                    confidence_score=round(avg_score / 100, 2),
                    suggested_materials=json.dumps(plans)
                )
                db.session.add(weak)
            else:
                weak.confidence_score = round(avg_score / 100, 2)
                weak.suggested_materials = json.dumps(plans)
                weak.topic_name = f"General {subject.name} Review"
                
            updated_weak_topics.append(weak)
            
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error saving weak topic analysis: {e}")
        
    return updated_weak_topics
