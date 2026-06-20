import json
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, date
from models import db
from models.models import (
    User, StudentProfile, Subject, Conversation, ChatHistory,
    Quiz, QuizQuestion, QuizResult, DailyChallenge,
    StudyMaterial, Summary, WeakTopic, Achievement,
    Leaderboard as LeaderboardModel, Notification, ActivityLog,
    PlacementProgress, CodingProgress, Resume, InterviewHistory, CareerRoadmap
)
from services import (
    get_recommendations, analyze_student_performance,
    PLACEMENT_MODULES, DSA_TOPICS, TECH_INTERVIEW_TOPICS, HR_INTERVIEW_TOPICS,
    COMPANIES, CAREER_PATHS, calculate_readiness_scores, get_placement_weak_topics,
    get_company_experiences, COMPANY_QUESTIONS
)

student_bp = Blueprint('student', __name__)

@student_bp.before_request
def check_user_role():
    # Enforce role checking if user is logged in
    if current_user.is_authenticated:
        if current_user.is_deleted:
            from flask_login import logout_user
            logout_user()
            flash('Your account has been deleted.', 'danger')
            return redirect(url_for('student.landing'))
        # If admin tries to access student routes, redirect (except profile, logout)
        if current_user.role == 'admin' and request.endpoint and 'student.' in request.endpoint:
            if request.endpoint not in ['student.landing']:
                return redirect(url_for('admin.dashboard'))

@student_bp.route('/')
def landing():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
    return render_template('landing.html')

@student_bp.route('/dashboard')
@login_required
def dashboard():
    # Student Profile metrics
    profile = current_user.profile
    streak = profile.current_streak if profile else 0
    points = profile.total_points if profile else 0
    
    # Global counts
    total_students = User.query.filter_by(role='student', is_deleted=False).count()
    total_quizzes = Quiz.query.filter_by(created_by_id=current_user.id).count()
    total_chats = Conversation.query.filter_by(user_id=current_user.id, is_deleted=False).count()
    total_materials = StudyMaterial.query.filter_by(user_id=current_user.id, is_deleted=False).count()
    
    # Recent Activities
    activities = ActivityLog.query.filter_by(user_id=current_user.id)\
        .order_by(ActivityLog.timestamp.desc()).limit(5).all()
        
    # AI Recommendations
    recommendations = get_recommendations(current_user.id)
    
    # Unread notifications count
    unread_notif = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    
    # Achievements
    achievements = Achievement.query.filter_by(user_id=current_user.id).limit(4).all()

    readiness = calculate_readiness_scores(current_user.id, db.session, {
        'PlacementProgress': PlacementProgress, 'CodingProgress': CodingProgress,
        'InterviewHistory': InterviewHistory, 'Resume': Resume, 'QuizResult': QuizResult
    })

    return render_template(
        'dashboard.html',
        streak=streak,
        points=points,
        total_students=total_students,
        total_quizzes=total_quizzes,
        total_chats=total_chats,
        total_materials=total_materials,
        activities=activities,
        recommendations=recommendations,
        unread_notif=unread_notif,
        achievements=achievements,
        readiness=readiness
    )

@student_bp.route('/subjects', methods=['GET', 'POST'])
@login_required
def subjects():
    if request.method == 'POST':
        # Create a custom subject
        sub_name = request.form.get('name', '').strip()
        sub_code = request.form.get('code', '').strip().upper()
        
        if not sub_name or not sub_code:
            flash("Subject name and code are required.", "danger")
            return redirect(url_for('student.subjects'))
            
        existing = Subject.query.filter((Subject.name == sub_name) | (Subject.code == sub_code)).first()
        if existing:
            flash("Subject name or code already exists.", "danger")
            return redirect(url_for('student.subjects'))
            
        new_sub = Subject(
            name=sub_name,
            code=sub_code,
            is_custom=True,
            created_by_id=current_user.id
        )
        db.session.add(new_sub)
        
        # Log action
        log = ActivityLog(user_id=current_user.id, action="Created Custom Subject", details=sub_name)
        db.session.add(log)
        
        db.session.commit()
        flash(f"Custom subject '{sub_name}' added successfully!", "success")
        return redirect(url_for('student.subjects'))
        
    # Get standard subjects + custom subjects created by the user
    all_subjects = Subject.query.filter(
        (Subject.is_deleted == False) & 
        ((Subject.is_custom == False) | (Subject.created_by_id == current_user.id))
    ).all()
    
    return render_template('subjects.html', subjects=all_subjects)

@student_bp.route('/chatbot')
@login_required
def chatbot():
    subject_id = request.args.get('subject_id')
    conv_id = request.args.get('conv_id')
    
    active_subject = None
    active_conv = None
    
    if subject_id:
        active_subject = Subject.query.get(subject_id)
    if conv_id:
        active_conv = Conversation.query.filter_by(id=conv_id, user_id=current_user.id, is_deleted=False).first()
        if active_conv:
            active_subject = Subject.query.get(active_conv.subject_id)
            
    subjects = Subject.query.filter(
        (Subject.is_deleted == False) & 
        ((Subject.is_custom == False) | (Subject.created_by_id == current_user.id))
    ).all()
    
    return render_template(
        'chatbot.html',
        subjects=subjects,
        active_subject=active_subject,
        active_conv=active_conv
    )

@student_bp.route('/chat-history')
@login_required
def chat_history():
    query = request.args.get('q', '').strip()
    
    conv_query = Conversation.query.filter_by(user_id=current_user.id, is_deleted=False)
    
    if query:
        # Search title
        conv_query = conv_query.filter(Conversation.title.ilike(f"%{query}%"))
        
    conversations = conv_query.order_by(Conversation.created_at.desc()).all()
    
    return render_template('chat_history.html', conversations=conversations, search_query=query)

@student_bp.route('/quiz-gen')
@login_required
def quiz_gen():
    subjects = Subject.query.filter(
        (Subject.is_deleted == False) & 
        ((Subject.is_custom == False) | (Subject.created_by_id == current_user.id))
    ).all()
    
    # Pre-select subject if passed in URL
    selected_subject_name = request.args.get('subject', '')
    
    # Get uploaded materials to allow quiz generation from files
    materials = StudyMaterial.query.filter_by(user_id=current_user.id, is_approved=True, is_deleted=False).all()
    
    return render_template(
        'quiz_gen.html',
        subjects=subjects,
        selected_subject_name=selected_subject_name,
        materials=materials
    )

@student_bp.route('/quiz/<int:quiz_id>')
@login_required
def quiz_view(quiz_id):
    quiz = Quiz.query.filter_by(id=quiz_id, created_by_id=current_user.id).first_or_404()
    # Check if user already took the quiz
    result = QuizResult.query.filter_by(quiz_id=quiz.id, user_id=current_user.id).first()
    if result:
        flash("You have already completed this quiz. Here are your results.", "info")
        return render_template('quiz_view.html', quiz=quiz, completed_result=result)
        
    return render_template('quiz_view.html', quiz=quiz, completed_result=None)

@student_bp.route('/daily-quiz')
@login_required
def daily_quiz():
    today = date.today()
    challenge = DailyChallenge.query.filter_by(date=today).first()
    
    # If no daily challenge is generated for today, look for/create one
    if not challenge:
        # Grab a quiz marked as daily or generate a simple general math quiz as daily
        general_sub = Subject.query.filter_by(code='DSA').first()
        if not general_sub:
            general_sub = Subject.query.first()
            
        if not general_sub:
            flash("Configure database subjects first.", "danger")
            return redirect(url_for('student.dashboard'))
            
        # Create a new quiz for the daily challenge
        from services import generate_quiz as create_quiz_data
        quiz_data = create_quiz_data(general_sub.name, 'subject', difficulty='easy', num_questions=3)
        
        new_quiz = Quiz(
            title=f"Daily Challenge: {today.strftime('%b %d, %Y')}",
            created_from='subject',
            subject_id=general_sub.id,
            difficulty='easy',
            created_by_id=current_user.id
        )
        db.session.add(new_quiz)
        db.session.flush()
        
        for q in quiz_data:
            db_q = QuizQuestion(
                quiz_id=new_quiz.id,
                question_text=q["question_text"],
                question_type=q["question_type"],
                option_a=q["option_a"],
                option_b=q["option_b"],
                option_c=q["option_c"],
                option_d=q["option_d"],
                correct_answer=q["correct_answer"],
                explanation=q["explanation"]
            )
            db.session.add(db_q)
            
        db.session.flush()
        challenge = DailyChallenge(date=today, quiz_id=new_quiz.id)
        db.session.add(challenge)
        db.session.commit()
        
    # Check if student completed today's challenge
    result = QuizResult.query.filter_by(quiz_id=challenge.quiz_id, user_id=current_user.id).first()
    
    profile = current_user.profile
    streak = profile.current_streak if profile else 0
    max_streak = profile.max_streak if profile else 0
    
    quiz = Quiz.query.get(challenge.quiz_id)
    
    return render_template(
        'daily_quiz.html',
        quiz=quiz,
        completed_result=result,
        streak=streak,
        max_streak=max_streak
    )

@student_bp.route('/summarizer')
@login_required
def summarizer():
    # List uploaded materials & summaries
    materials = StudyMaterial.query.filter_by(user_id=current_user.id, is_deleted=False).all()
    summaries = Summary.query.filter_by(user_id=current_user.id).order_by(Summary.created_at.desc()).all()
    
    return render_template('summarizer.html', materials=materials, summaries=summaries)

@student_bp.route('/progress')
@login_required
def progress():
    # Analyze and sync weak topics dynamically
    analyze_student_performance(current_user.id)
    
    # Weekly/Monthly report calculations
    results = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.completed_at.asc()).all()
    
    # Gather data for Chart.js
    labels = [r.completed_at.strftime('%m/%d') for r in results[-10:]] # last 10 quizzes
    scores = [int((r.score / r.total_questions) * 100) if r.total_questions > 0 else 0 for r in results[-10:]]
    points = [r.points_earned for r in results[-10:]]
    
    # Gather subject distribution
    subject_counts = {}
    for r in results:
        quiz = Quiz.query.get(r.quiz_id)
        if quiz and quiz.subject:
            sub_name = quiz.subject.name
            subject_counts[sub_name] = subject_counts.get(sub_name, 0) + 1
            
    sub_labels = list(subject_counts.keys())
    sub_data = list(subject_counts.values())
    
    # Summarized stats
    total_quizzes = len(results)
    avg_score = int(sum(scores) / len(scores)) if scores else 0
    total_points_earned = sum([r.points_earned for r in results])

    readiness = calculate_readiness_scores(current_user.id, db.session, {
        'PlacementProgress': PlacementProgress, 'CodingProgress': CodingProgress,
        'InterviewHistory': InterviewHistory, 'Resume': Resume, 'QuizResult': QuizResult
    })
    
    return render_template(
        'progress.html',
        labels=labels,
        scores=scores,
        points=points,
        sub_labels=sub_labels,
        sub_data=sub_data,
        total_quizzes=total_quizzes,
        avg_score=avg_score,
        total_points_earned=total_points_earned,
        readiness=readiness,
        subject_performance=readiness.get('subject_performance', {})
    )

@student_bp.route('/weak-topics')
@login_required
def weak_topics():
    # Analyze student performance first to ensure up-to-date entries
    analyze_student_performance(current_user.id)
    
    weak_entries = WeakTopic.query.filter_by(user_id=current_user.id).all()
    
    # Parse json strings for suggested plans in Jinja template
    parsed_entries = []
    for w in weak_entries:
        plans = []
        if w.suggested_materials:
            try:
                plans = json.loads(w.suggested_materials)
            except Exception:
                plans = [w.suggested_materials]
        parsed_entries.append({
            "subject": w.subject.name if w.subject else "General",
            "topic_name": w.topic_name,
            "confidence_score": int(w.confidence_score * 100),
            "plans": plans,
            "updated_at": w.updated_at
        })
        
    return render_template('weak_topics.html', weak_topics=parsed_entries)

@student_bp.route('/leaderboard')
@login_required
def leaderboard():
    # Fetch rankings sorted by total points desc, then streak desc
    profiles = StudentProfile.query.order_by(
        StudentProfile.total_points.desc(), 
        StudentProfile.current_streak.desc()
    ).all()
    
    # Ensure current user is in leaderboard model (snapshot helper)
    # Map standings with ranks
    standings = []
    current_user_rank = None
    for idx, p in enumerate(profiles):
        rank = idx + 1
        user = User.query.get(p.user_id)
        if not user or user.is_deleted:
            continue
            
        # Check badges earned by this user
        badges = Achievement.query.filter_by(user_id=p.user_id).all()
        badge_codes = [b.badge_code for b in badges]
        
        standing_entry = {
            "rank": rank,
            "username": user.username,
            "avatar": user.avatar,
            "points": p.total_points,
            "streak": p.current_streak,
            "badges": badge_codes,
            "user_id": p.user_id
        }
        standings.append(standing_entry)
        
        if p.user_id == current_user.id:
            current_user_rank = rank
            
    # Achievements for current user
    user_achievements = Achievement.query.filter_by(user_id=current_user.id).all()
    
    return render_template(
        'leaderboard.html',
        standings=standings,
        current_user_rank=current_user_rank,
        user_achievements=user_achievements
    )

@student_bp.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).all()
        
    # Mark all notifications as read when visiting this page
    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    if unread:
        for u in unread:
            u.is_read = True
        db.session.commit()
        
    return render_template('notifications.html', notifications=notifs)


# ============================================================
# PLACEMENT PREPARATION HUB
# ============================================================

@student_bp.route('/placement')
@login_required
def placement_hub():
    weak_topics = get_placement_weak_topics(current_user.id, db.session, PlacementProgress)
    progress = PlacementProgress.query.filter_by(user_id=current_user.id).all()
    module_stats = {}
    for p in progress:
        if p.module not in module_stats:
            module_stats[p.module] = {'attempts': 0, 'avg_score': 0, 'scores': []}
        module_stats[p.module]['attempts'] += 1
        if p.total_questions > 0:
            module_stats[p.module]['scores'].append(int(p.score / p.total_questions * 100))
    for mod in module_stats:
        scores = module_stats[mod]['scores']
        module_stats[mod]['avg_score'] = int(sum(scores) / len(scores)) if scores else 0

    return render_template(
        'placement.html',
        modules=PLACEMENT_MODULES,
        module_stats=module_stats,
        weak_topics=weak_topics
    )


@student_bp.route('/placement/<module_key>')
@login_required
def placement_module(module_key):
    if module_key not in PLACEMENT_MODULES:
        flash("Module not found.", "danger")
        return redirect(url_for('student.placement_hub'))

    module = PLACEMENT_MODULES[module_key]
    progress = PlacementProgress.query.filter_by(
        user_id=current_user.id, module=module_key
    ).order_by(PlacementProgress.last_practiced.desc()).limit(5).all()

    return render_template(
        'placement_module.html',
        module_key=module_key,
        module=module,
        progress=progress
    )


# ============================================================
# DSA / CODING PREPARATION
# ============================================================

@student_bp.route('/coding')
@login_required
def coding_hub():
    progress = CodingProgress.query.filter_by(user_id=current_user.id).all()
    topic_stats = {}
    for p in progress:
        topic_stats[p.topic] = {
            'problems_solved': p.problems_solved,
            'score_avg': int(p.score_avg),
            'total_attempted': p.total_attempted
        }

    sorted_topics = dict(sorted(DSA_TOPICS.items(), key=lambda x: x[1]['order']))
    return render_template('coding.html', topics=sorted_topics, topic_stats=topic_stats)


@student_bp.route('/coding/<topic_key>')
@login_required
def coding_topic(topic_key):
    if topic_key not in DSA_TOPICS:
        flash("Topic not found.", "danger")
        return redirect(url_for('student.coding_hub'))

    topic = DSA_TOPICS[topic_key]
    progress = CodingProgress.query.filter_by(
        user_id=current_user.id, topic=topic_key
    ).order_by(CodingProgress.last_practiced.desc()).first()

    return render_template(
        'coding_topic.html',
        topic_key=topic_key,
        topic=topic,
        progress=progress,
        all_topics=DSA_TOPICS
    )


# ============================================================
# INTERVIEW PREPARATION
# ============================================================

@student_bp.route('/interview')
@login_required
def interview_hub():
    history = InterviewHistory.query.filter_by(user_id=current_user.id)\
        .order_by(InterviewHistory.created_at.desc()).limit(10).all()
    avg_confidence = 0
    if history:
        avg_confidence = int(sum(h.confidence_score for h in history) / len(history))

    return render_template(
        'interview.html',
        tech_topics=TECH_INTERVIEW_TOPICS,
        hr_topics=HR_INTERVIEW_TOPICS,
        history=history,
        avg_confidence=avg_confidence
    )


@student_bp.route('/interview/mock')
@login_required
def interview_mock():
    interview_type = request.args.get('type', 'technical')
    topic = request.args.get('topic', '')
    return render_template(
        'interview_mock.html',
        interview_type=interview_type,
        topic=topic,
        tech_topics=TECH_INTERVIEW_TOPICS,
        hr_topics=HR_INTERVIEW_TOPICS
    )


# ============================================================
# RESUME BUILDER
# ============================================================

@student_bp.route('/resume-builder')
@login_required
def resume_builder():
    resumes = Resume.query.filter_by(user_id=current_user.id)\
        .order_by(Resume.updated_at.desc()).all()
    latest = resumes[0] if resumes else None
    return render_template('resume_builder.html', resumes=resumes, latest=latest)


# ============================================================
# COMPANY PREPARATION
# ============================================================

@student_bp.route('/company-prep')
@login_required
def company_prep():
    return render_template('company_prep.html', companies=COMPANIES)


@student_bp.route('/company-prep/<company_key>')
@login_required
def company_detail(company_key):
    if company_key not in COMPANIES:
        flash("Company not found.", "danger")
        return redirect(url_for('student.company_prep'))

    company = COMPANIES[company_key]
    questions = COMPANY_QUESTIONS.get(company_key, [])
    experiences = get_company_experiences(company_key)

    return render_template(
        'company_detail.html',
        company_key=company_key,
        company=company,
        questions=questions,
        experiences=experiences
    )


# ============================================================
# CAREER ROADMAP
# ============================================================

@student_bp.route('/career-roadmap')
@login_required
def career_roadmap():
    roadmaps = CareerRoadmap.query.filter_by(user_id=current_user.id)\
        .order_by(CareerRoadmap.updated_at.desc()).all()
    active = roadmaps[0] if roadmaps else None
    active_data = json.loads(active.roadmap_data) if active and active.roadmap_data else None
    active_courses = json.loads(active.courses) if active and active.courses else []

    return render_template(
        'career_roadmap.html',
        career_paths=CAREER_PATHS,
        active=active,
        active_data=active_data,
        active_courses=active_courses,
        roadmaps=roadmaps
    )
