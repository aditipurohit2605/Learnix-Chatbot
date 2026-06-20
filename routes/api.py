import os
from flask import Blueprint, jsonify, request, current_app, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, date, timedelta
import json
from models import db
from models.models import (
    User, StudentProfile, Subject, Conversation, ChatHistory,
    Quiz, QuizQuestion, QuizResult, DailyChallenge,
    StudyMaterial, Summary, WeakTopic, Achievement, Notification, ActivityLog,
    PlacementProgress, CodingProgress, Resume, InterviewHistory, CareerRoadmap
)
from services import (
    get_chatbot_response, generate_quiz as generate_quiz_data,
    generate_quiz_from_conversation, evaluate_conversation_quiz,
    extract_text_from_file, generate_summary as generate_summary_data,
    generate_placement_quiz, get_coding_explanation, get_coding_practice,
    start_mock_interview, evaluate_interview_answer, generate_resume_content,
    score_resume, generate_resume_pdf, generate_career_roadmap
)

api_bp = Blueprint('api', __name__, url_prefix='/api')

def check_and_award_achievements(user_id):
    """
    Checks student stats and unlocks badges/achievements, creating notifications.
    """
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return
        
    unlocked = []
    
    # Helper to award badge
    def award_badge(badge_code, badge_name):
        existing = Achievement.query.filter_by(user_id=user_id, badge_code=badge_code).first()
        if not existing:
            new_ach = Achievement(user_id=user_id, badge_name=badge_name, badge_code=badge_code)
            db.session.add(new_ach)
            
            # Send Notification
            notif = Notification(
                user_id=user_id,
                title="Achievement Unlocked!",
                message=f"Congratulations! You've earned the '{badge_name}' badge.",
                type="achievement"
            )
            db.session.add(notif)
            unlocked.append(badge_name)
            
    # 1. Beginner Learner: >= 50 points
    if profile.total_points >= 50:
        award_badge('beginner_learner', 'Beginner Learner')
        
    # 2. Quiz Master: >= 200 points
    if profile.total_points >= 200:
        award_badge('quiz_master', 'Quiz Master')
        
    # 3. Study Streak Hero: streak >= 5 days
    if profile.current_streak >= 5:
        award_badge('streak_hero', 'Study Streak Hero')
        
    # 4. AI Explorer: >= 5 chat sessions
    chats_count = Conversation.query.filter_by(user_id=user_id, is_deleted=False).count()
    if chats_count >= 5:
        award_badge('ai_explorer', 'AI Explorer')
        
    # 5. Top Ranker: Rank 1 on leaderboard
    # Quick ranking check
    all_profiles = StudentProfile.query.order_by(StudentProfile.total_points.desc()).all()
    if all_profiles and all_profiles[0].user_id == user_id:
        award_badge('top_ranker', 'Top Ranker')
        
    if unlocked:
        db.session.commit()
        
    return unlocked

@api_bp.route('/chat/send', methods=['POST'])
@login_required
def send_chat_message():
    data = request.json or {}
    subject_id = data.get('subject_id')
    conv_id = data.get('conversation_id')
    message_text = data.get('message', '').strip()
    
    if not message_text:
        return jsonify({"status": "error", "message": "Message content is empty."}), 400
        
    # Find or Create Conversation
    conversation = None
    if conv_id:
        conversation = Conversation.query.filter_by(id=conv_id, user_id=current_user.id, is_deleted=False).first()
        
    if not conversation:
        if not subject_id:
            return jsonify({"status": "error", "message": "Subject ID is required to start a new chat."}), 400
        subject = Subject.query.get(subject_id)
        if not subject:
            return jsonify({"status": "error", "message": "Subject not found."}), 404
            
        title = message_text[:40] + ("..." if len(message_text) > 40 else "")
        conversation = Conversation(
            user_id=current_user.id,
            subject_id=subject.id,
            title=title
        )
        db.session.add(conversation)
        db.session.flush() # populate conversation.id
        
    # 1. Save User Message
    user_msg = ChatHistory(
        conversation_id=conversation.id,
        role='user',
        content=message_text
    )
    db.session.add(user_msg)
    db.session.commit()
    
    # 2. Extract History for LLM Context
    history_items = ChatHistory.query.filter_by(conversation_id=conversation.id)\
        .order_by(ChatHistory.timestamp.asc()).all()
    
    # Exclude the current message to send it as the prompt
    history_context = []
    for item in history_items[:-1]:
        history_context.append({
            "role": item.role,
            "content": item.content
        })
        
    # 3. Call Chatbot Service
    subject_obj = Subject.query.get(conversation.subject_id)
    chatbot_result = get_chatbot_response(
        subject_name=subject_obj.name,
        history=history_context,
        new_message=message_text,
        subject_id=conversation.subject_id,
        user_id=current_user.id
    )
    
    # 4. Save Bot Message if successful
    if chatbot_result.get("success", False):
        bot_msg = ChatHistory(
            conversation_id=conversation.id,
            role='assistant',
            content=chatbot_result["answer"]
        )
        db.session.add(bot_msg)
    
    # Log action
    log = ActivityLog(
        user_id=current_user.id,
        action="Chatted with Bot",
        details=f"Subject: {subject_obj.name}, Conversation ID: {conversation.id}"
    )
    db.session.add(log)
    
    db.session.commit()
    
    # Trigger achievements check
    check_and_award_achievements(current_user.id)
    
    return jsonify({
        "success": chatbot_result.get("success", False),
        "status": "success" if chatbot_result.get("success", False) else "error",
        "source": chatbot_result.get("source", "error"),
        "answer": chatbot_result.get("answer"),
        "reply": chatbot_result.get("answer"),
        "is_quiz": chatbot_result.get("is_quiz", False),
        "conversation_id": conversation.id,
        "conversation_title": conversation.title
    })

@api_bp.route('/chat/generate-quiz', methods=['POST'])
@login_required
def generate_quiz_from_chat():
    """Generate a quiz from the current conversation context."""
    data = request.json or {}
    conv_id = data.get('conversation_id')
    subject_id = data.get('subject_id')

    conversation = None
    if conv_id:
        conversation = Conversation.query.filter_by(
            id=conv_id, user_id=current_user.id, is_deleted=False
        ).first()

    if not conversation:
        if not subject_id:
            return jsonify({"status": "error", "message": "Conversation or subject required."}), 400
        subject = Subject.query.get(subject_id)
        if not subject:
            return jsonify({"status": "error", "message": "Subject not found."}), 404
        return jsonify({
            "status": "error",
            "message": "Start a conversation first, then generate a quiz from it.",
        }), 400

    subject_obj = Subject.query.get(conversation.subject_id)
    history_items = ChatHistory.query.filter_by(conversation_id=conversation.id)\
        .order_by(ChatHistory.timestamp.asc()).all()

    if len(history_items) < 2:
        return jsonify({
            "status": "error",
            "message": "Discuss a topic first (e.g. explain binary trees), then generate a quiz.",
        }), 400

    messages = [{"role": m.role, "content": m.content} for m in history_items]
    topic = None
    for m in reversed(history_items):
        if m.role == "user" and len(m.content) > 10:
            topic = m.content[:80]
            break

    quiz_data = generate_quiz_from_conversation(
        subject_obj.name, messages, topic=topic
    )

    all_questions = quiz_data["easy"] + quiz_data["medium"] + quiz_data["hard"]

    quiz = Quiz(
        title=f"Chat Quiz: {quiz_data['topic']}",
        created_from="conversation",
        subject_id=subject_obj.id,
        difficulty="mixed",
        created_by_id=current_user.id,
    )
    db.session.add(quiz)
    db.session.flush()

    for q in all_questions:
        db.session.add(QuizQuestion(
            quiz_id=quiz.id,
            question_text=q["question_text"],
            question_type="mcq",
            option_a=q["option_a"],
            option_b=q["option_b"],
            option_c=q["option_c"],
            option_d=q["option_d"],
            correct_answer=q["correct_answer"],
            explanation=q.get("explanation", ""),
        ))

    bot_summary = (
        f"## {quiz_data['topic']} Quiz Ready\n\n"
        f"### Question Breakdown\n"
        f"- **Easy**: {len(quiz_data['easy'])} questions\n"
        f"- **Medium**: {len(quiz_data['medium'])} questions\n"
        f"- **Hard**: {len(quiz_data['hard'])} questions\n\n"
        f"### Total: 10 Questions\n\n"
        f"Click **Take Quiz** below to start."
    )

    db.session.add(ChatHistory(
        conversation_id=conversation.id,
        role="assistant",
        content=bot_summary,
    ))

    log = ActivityLog(
        user_id=current_user.id,
        action="Generated Chat Quiz",
        details=f"Topic: {quiz_data['topic']}, Quiz ID: {quiz.id}",
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "status": "success",
        "quiz_id": quiz.id,
        "topic": quiz_data["topic"],
        "easy_count": len(quiz_data["easy"]),
        "medium_count": len(quiz_data["medium"]),
        "hard_count": len(quiz_data["hard"]),
        "questions": all_questions,
        "summary": bot_summary,
    })


@api_bp.route('/chat/evaluate-quiz', methods=['POST'])
@login_required
def evaluate_chat_quiz():
    """Evaluate inline quiz answers from chat."""
    data = request.json or {}
    questions = data.get("questions", [])
    answers = data.get("answers", {})

    if not questions:
        return jsonify({"status": "error", "message": "No questions provided."}), 400

    result = evaluate_conversation_quiz(questions, answers)

    report = (
        f"## Quiz Results\n\n"
        f"### Score: **{result['score']}/{result['total']}** ({result['percentage']}%)\n\n"
    )
    if result["weak_areas"]:
        report += "### Weak Areas\n"
        for area in result["weak_areas"]:
            report += f"- {area.title()} difficulty questions\n"
        report += "\n"
    if result["wrong_answers"]:
        report += "### Incorrect Answers\n"
        for w in result["wrong_answers"]:
            report += f"- Q{w['index']+1}: Your answer **{w['your_answer']}**, Correct: **{w['correct_answer']}**\n"
        report += "\n"
    report += "### Suggestions\n"
    for s in result["suggestions"]:
        report += f"- {s}\n"

    return jsonify({"status": "success", "result": result, "report": report})

@api_bp.route('/chat/delete/<int:conv_id>', methods=['POST'])
@login_required
def delete_conversation(conv_id):
    conversation = Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first_or_404()
    conversation.is_deleted = True
    db.session.commit()
    return jsonify({"status": "success", "message": "Conversation deleted."})

@api_bp.route('/quiz/generate', methods=['POST'])
@login_required
def generate_quiz_endpoint():
    data = request.json or {}
    subject_id = data.get('subject_id')
    source_type = data.get('source_type', 'subject')  # 'subject', 'material', 'weak_topic'
    material_id = data.get('material_id')
    difficulty = data.get('difficulty', 'medium')
    num_questions = int(data.get('num_questions', 3))
    
    # Validation
    subject = Subject.query.get(subject_id)
    if not subject:
        return jsonify({"status": "error", "message": "Subject not found."}), 404
        
    content_text = ""
    quiz_title = f"{subject.name} Practice Quiz"
    
    if source_type == 'material' and material_id:
        material = StudyMaterial.query.filter_by(id=material_id, user_id=current_user.id).first()
        if not material:
            return jsonify({"status": "error", "message": "Material not found."}), 404
        content_text = extract_text_from_file(material.file_path, material.file_type)
        quiz_title = f"Quiz: {material.file_name}"
        
    elif source_type == 'weak_topic':
        # Generate focus quiz
        quiz_title = f"Weak Topic Refocus: {subject.name}"
        
    # Generate Questions
    questions_data = generate_quiz_data(
        subject.name, 
        source_type, 
        content_text=content_text, 
        difficulty=difficulty, 
        num_questions=num_questions
    )
    
    # Save Quiz to DB
    quiz = Quiz(
        title=quiz_title,
        created_from=source_type,
        subject_id=subject.id,
        difficulty=difficulty,
        created_by_id=current_user.id
    )
    db.session.add(quiz)
    db.session.flush() # get quiz.id
    
    for q in questions_data:
        question = QuizQuestion(
            quiz_id=quiz.id,
            question_text=q["question_text"],
            question_type=q["question_type"],
            option_a=q["option_a"],
            option_b=q["option_b"],
            option_c=q["option_c"],
            option_d=q["option_d"],
            correct_answer=q["correct_answer"],
            explanation=q["explanation"]
        )
        db.session.add(question)
        
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "quiz_id": quiz.id
    })

@api_bp.route('/quiz/submit', methods=['POST'])
@login_required
def submit_quiz():
    data = request.json or {}
    quiz_id = data.get('quiz_id')
    user_answers = data.get('answers', {}) # dict mapping question_id -> option chosen
    
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"status": "error", "message": "Quiz not found."}), 404
        
    questions = quiz.questions
    score = 0
    total = len(questions)
    
    question_feedbacks = []
    
    for q in questions:
        submitted = user_answers.get(str(q.id), '').strip().lower()
        correct = q.correct_answer.strip().lower()
        
        # Check matching
        is_correct = False
        if q.question_type == 'mcq':
            is_correct = (submitted == correct)
        elif q.question_type == 'true_false':
            is_correct = (submitted == correct)
        else: # fill_in
            # Perform loose comparison (ignore case, spaces)
            is_correct = (submitted.replace(" ", "") == correct.replace(" ", ""))
            
        if is_correct:
            score += 1
            
        question_feedbacks.append({
            "id": q.id,
            "question_text": q.question_text,
            "correct_answer": q.correct_answer,
            "submitted_answer": user_answers.get(str(q.id), ''),
            "is_correct": is_correct,
            "explanation": q.explanation
        })
        
    # Calculate score weights
    weight = 10
    if quiz.difficulty == 'medium':
        weight = 15
    elif quiz.difficulty == 'hard':
        weight = 20
        
    points_earned = score * weight
    
    # Save QuizResult
    result = QuizResult(
        quiz_id=quiz.id,
        user_id=current_user.id,
        score=score,
        total_questions=total,
        points_earned=points_earned
    )
    db.session.add(result)
    
    # Update Student Streak & Points
    profile = current_user.profile
    if profile:
        profile.total_points += points_earned
        
        # Check streak update
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        if profile.last_activity_date == yesterday:
            profile.current_streak += 1
            if profile.current_streak > profile.max_streak:
                profile.max_streak = profile.current_streak
        elif profile.last_activity_date == today:
            # Already practiced today, keep streak
            pass
        else:
            # Streak broken
            profile.current_streak = 1
            if profile.max_streak == 0:
                profile.max_streak = 1
                
        profile.last_activity_date = today
        
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action="Completed Quiz",
        details=f"Quiz ID: {quiz.id}, Score: {score}/{total}, Points: {points_earned}"
    )
    db.session.add(log)
    
    # Check streak milestones for notifications
    if profile and profile.current_streak % 5 == 0:
        streak_notif = Notification(
            user_id=current_user.id,
            title="Streak Milestone!",
            message=f"You are on a {profile.current_streak} days learning streak! Keep it up!",
            type="streak"
        )
        db.session.add(streak_notif)
        
    db.session.commit()
    
    # Trigger achievements update
    unlocked_badges = check_and_award_achievements(current_user.id)
    
    return jsonify({
        "status": "success",
        "score": score,
        "total": total,
        "points_earned": points_earned,
        "questions": question_feedbacks,
        "unlocked_badges": unlocked_badges
    })

@api_bp.route('/summarize', methods=['POST'])
@login_required
def upload_and_summarize():
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({"status": "error", "message": "No file uploaded."}), 400
        
    # Extract extension
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if ext not in current_app.config['ALLOWED_EXTENSIONS']['document']:
        return jsonify({"status": "error", "message": "Unsupported file type. Use PDF, DOCX or TXT."}), 400
        
    # Save material file
    import uuid
    unique_name = f"doc_{uuid.uuid4().hex}_{filename}"
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'materials', unique_name)
    file.save(upload_path)
    
    # Calculate file size
    size_bytes = os.path.getsize(upload_path)
    
    # Create StudyMaterial (Automatically approve student uploads for their own summary generation)
    material = StudyMaterial(
        user_id=current_user.id,
        file_name=filename,
        file_path=upload_path,
        file_type=ext,
        size=size_bytes,
        is_approved=True # Auto-approved for user own summaries
    )
    db.session.add(material)
    db.session.flush() # populate material.id
    
    # Extract plain text
    try:
        extracted_text = extract_text_from_file(upload_path, ext)
        if not extracted_text:
            return jsonify({"status": "error", "message": "Could not extract text from document."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Parsing failed: {e}"}), 500
        
    # Generate Summary
    summary_data = generate_summary_data(filename, extracted_text)
    
    # Save Summary to DB
    summary = Summary(
        material_id=material.id,
        user_id=current_user.id,
        title=summary_data["title"],
        short_summary=summary_data["short_summary"],
        detailed_summary=summary_data["detailed_summary"],
        bullet_points=summary_data["bullet_points"]
    )
    db.session.add(summary)
    
    # Log Action
    log = ActivityLog(
        user_id=current_user.id,
        action="Summarized Notes",
        details=f"File: {filename}"
    )
    db.session.add(log)
    
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "title": summary.title,
        "short_summary": summary.short_summary,
        "detailed_summary": summary.detailed_summary,
        "bullet_points": summary.bullet_points.split(" || ")
    })


# ============================================================
# PLACEMENT API
# ============================================================

@api_bp.route('/placement/quiz/generate', methods=['POST'])
@login_required
def placement_quiz_generate():
    data = request.json or {}
    module = data.get('module', 'aptitude')
    topic = data.get('topic')
    difficulty = data.get('difficulty', 'medium')
    num_questions = int(data.get('num_questions', 5))

    questions = generate_placement_quiz(module, topic, difficulty, num_questions)
    return jsonify({"status": "success", "questions": questions, "module": module, "topic": topic, "difficulty": difficulty})


@api_bp.route('/placement/quiz/submit', methods=['POST'])
@login_required
def placement_quiz_submit():
    data = request.json or {}
    module = data.get('module')
    topic = data.get('topic', 'General')
    difficulty = data.get('difficulty', 'medium')
    answers = data.get('answers', [])
    questions = data.get('questions', [])

    score = 0
    total = len(questions)
    weak = []

    for i, q in enumerate(questions):
        submitted = str(answers.get(str(i), answers.get(i, ''))).strip().lower()
        correct = str(q.get('correct_answer', '')).strip().lower()
        if submitted == correct:
            score += 1
        else:
            weak.append(q.get('question_text', f'Question {i+1}'))

    weak_json = json.dumps(weak[:5]) if weak else None
    progress = PlacementProgress(
        user_id=current_user.id,
        module=module,
        topic=topic,
        difficulty=difficulty,
        score=score,
        total_questions=total,
        weak_topics=weak_json,
        last_practiced=datetime.utcnow()
    )
    db.session.add(progress)

    profile = current_user.profile
    if profile:
        profile.total_points += score * 5

    log = ActivityLog(user_id=current_user.id, action="Placement Quiz", details=f"{module}: {score}/{total}")
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "status": "success",
        "score": score,
        "total": total,
        "percentage": int(score / total * 100) if total > 0 else 0,
        "weak_topics": weak[:5]
    })


# ============================================================
# CODING API
# ============================================================

@api_bp.route('/coding/explain', methods=['POST'])
@login_required
def coding_explain():
    data = request.json or {}
    topic = data.get('topic', 'arrays')
    question = data.get('question')
    explanation = get_coding_explanation(topic, question)
    return jsonify({"status": "success", "explanation": explanation})


@api_bp.route('/coding/practice', methods=['POST'])
@login_required
def coding_practice():
    data = request.json or {}
    topic = data.get('topic', 'arrays')
    difficulty = data.get('difficulty', 'medium')
    problem = get_coding_practice(topic, difficulty)
    return jsonify({"status": "success", "problem": problem})


@api_bp.route('/coding/submit', methods=['POST'])
@login_required
def coding_submit():
    data = request.json or {}
    topic = data.get('topic', 'arrays')
    difficulty = data.get('difficulty', 'medium')
    solved = data.get('solved', False)

    existing = CodingProgress.query.filter_by(user_id=current_user.id, topic=topic).first()
    if existing:
        existing.total_attempted += 1
        if solved:
            existing.problems_solved += 1
        existing.score_avg = (existing.problems_solved / existing.total_attempted) * 100
        existing.last_practiced = datetime.utcnow()
    else:
        existing = CodingProgress(
            user_id=current_user.id,
            topic=topic,
            difficulty=difficulty,
            problems_solved=1 if solved else 0,
            total_attempted=1,
            score_avg=100.0 if solved else 0.0
        )
        db.session.add(existing)

    log = ActivityLog(user_id=current_user.id, action="Coding Practice", details=f"{topic}: {'solved' if solved else 'attempted'}")
    db.session.add(log)
    db.session.commit()

    return jsonify({"status": "success", "progress": {
        "problems_solved": existing.problems_solved,
        "total_attempted": existing.total_attempted,
        "score_avg": int(existing.score_avg)
    }})


# ============================================================
# INTERVIEW API
# ============================================================

@api_bp.route('/interview/mock/start', methods=['POST'])
@login_required
def interview_mock_start():
    data = request.json or {}
    interview_type = data.get('type', 'technical')
    topic = data.get('topic')
    session = start_mock_interview(interview_type, topic)
    return jsonify({"status": "success", **session})


@api_bp.route('/interview/mock/submit', methods=['POST'])
@login_required
def interview_mock_submit():
    data = request.json or {}
    interview_type = data.get('type', 'technical')
    topic = data.get('topic', 'General')
    questions = data.get('questions', [])
    answers = data.get('answers', [])

    all_feedback = []
    confidence_scores = []

    for i, q in enumerate(questions):
        ans = answers[i] if i < len(answers) else ''
        feedback, conf = evaluate_interview_answer(q, ans, interview_type, topic)
        all_feedback.append({"question": q, "feedback": feedback, "confidence": conf})
        confidence_scores.append(conf)

    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

    history = InterviewHistory(
        user_id=current_user.id,
        interview_type=interview_type,
        topic=topic,
        questions=json.dumps(questions),
        answers=json.dumps(answers),
        feedback=json.dumps(all_feedback),
        confidence_score=avg_confidence
    )
    db.session.add(history)

    log = ActivityLog(user_id=current_user.id, action="Mock Interview", details=f"{interview_type}: {topic}, confidence: {int(avg_confidence)}%")
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "status": "success",
        "feedback": all_feedback,
        "confidence_score": int(avg_confidence)
    })


# ============================================================
# RESUME API
# ============================================================

@api_bp.route('/resume/generate', methods=['POST'])
@login_required
def resume_generate():
    data = request.json or {}
    name = data.get('name', current_user.username)
    education = data.get('education', '')
    skills = data.get('skills', '')
    projects = data.get('projects', '')
    experience = data.get('experience', '')
    achievements = data.get('achievements', '')

    content = generate_resume_content(name, education, skills, projects, experience, achievements)
    resume_score, checks = score_resume(name, education, skills, projects, experience, achievements, content)

    pdf_path = generate_resume_pdf(content, name, current_app.config['UPLOAD_FOLDER'])

    existing = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.updated_at.desc()).first()
    if existing:
        existing.name = name
        existing.education = education
        existing.skills = skills
        existing.projects = projects
        existing.experience = experience
        existing.achievements = achievements
        existing.content = content
        existing.resume_score = resume_score
        if pdf_path:
            existing.pdf_path = pdf_path
        resume = existing
    else:
        resume = Resume(
            user_id=current_user.id,
            name=name,
            education=education,
            skills=skills,
            projects=projects,
            experience=experience,
            achievements=achievements,
            content=content,
            resume_score=resume_score,
            pdf_path=pdf_path
        )
        db.session.add(resume)

    log = ActivityLog(user_id=current_user.id, action="Resume Generated", details=f"Score: {resume_score}/100")
    db.session.add(log)
    db.session.commit()

    pdf_url = None
    if resume.pdf_path and os.path.exists(resume.pdf_path):
        basename = os.path.basename(resume.pdf_path)
        pdf_url = url_for('static', filename=f'uploads/resumes/{basename}')

    return jsonify({
        "status": "success",
        "content": content,
        "resume_score": resume_score,
        "checks": checks,
        "pdf_url": pdf_url,
        "resume_id": resume.id
    })


# ============================================================
# CAREER ROADMAP API
# ============================================================

@api_bp.route('/career/roadmap/generate', methods=['POST'])
@login_required
def career_roadmap_generate():
    data = request.json or {}
    career_path = data.get('career_path', 'software_engineer')

    roadmap_data = generate_career_roadmap(career_path)
    courses = roadmap_data.get('courses', [])

    existing = CareerRoadmap.query.filter_by(user_id=current_user.id, career_path=career_path).first()
    if existing:
        existing.roadmap_data = json.dumps(roadmap_data)
        existing.courses = json.dumps(courses)
        existing.updated_at = datetime.utcnow()
        roadmap = existing
    else:
        roadmap = CareerRoadmap(
            user_id=current_user.id,
            career_path=career_path,
            roadmap_data=json.dumps(roadmap_data),
            courses=json.dumps(courses),
            progress_percent=0
        )
        db.session.add(roadmap)

    log = ActivityLog(user_id=current_user.id, action="Career Roadmap", details=f"Generated: {career_path}")
    db.session.add(log)
    db.session.commit()

    return jsonify({"status": "success", "roadmap": roadmap_data, "career_path": career_path})
