from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student' or 'admin'
    avatar = db.Column(db.String(200), nullable=True, default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationships
    profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic')
    quiz_results = db.relationship('QuizResult', backref='user', lazy='dynamic')
    materials = db.relationship('StudyMaterial', backref='uploader', lazy='dynamic')
    summaries = db.relationship('Summary', backref='user', lazy='dynamic')
    weak_topics = db.relationship('WeakTopic', backref='user', lazy='dynamic')
    achievements = db.relationship('Achievement', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy='dynamic')
    placement_progress = db.relationship('PlacementProgress', backref='user', lazy='dynamic')
    coding_progress = db.relationship('CodingProgress', backref='user', lazy='dynamic')
    resumes = db.relationship('Resume', backref='user', lazy='dynamic')
    interview_histories = db.relationship('InterviewHistory', backref='user', lazy='dynamic')
    career_roadmaps = db.relationship('CareerRoadmap', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def delete(self):
        self.is_deleted = True
        db.session.add(self)
        db.session.commit()

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    bio = db.Column(db.Text, nullable=True)
    current_streak = db.Column(db.Integer, default=0, nullable=False)
    max_streak = db.Column(db.Integer, default=0, nullable=False)
    last_activity_date = db.Column(db.Date, nullable=True)
    total_points = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Subject(db.Model):
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    code = db.Column(db.String(20), nullable=False, unique=True)  # e.g., 'MATH', 'SCI'
    is_custom = db.Column(db.Boolean, default=False, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    conversations = db.relationship('Conversation', backref='subject', lazy='dynamic')
    quizzes = db.relationship('Quiz', backref='subject', lazy='dynamic')
    weak_topics = db.relationship('WeakTopic', backref='subject', lazy='dynamic')

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False, default="New Chat Session")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationships
    messages = db.relationship('ChatHistory', backref='conversation', cascade="all, delete-orphan", lazy='joined')

class ChatHistory(db.Model):
    __tablename__ = 'chat_histories'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    created_from = db.Column(db.String(50), nullable=False)  # 'notes', 'subject', 'weak_topic'
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, default='medium')  # 'easy', 'medium', 'hard'
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('QuizQuestion', backref='quiz', cascade="all, delete-orphan", lazy='joined')
    results = db.relationship('QuizResult', backref='quiz', cascade="all, delete-orphan", lazy='dynamic')

class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(30), nullable=False)  # 'mcq', 'true_false', 'fill_in'
    option_a = db.Column(db.String(200), nullable=True)
    option_b = db.Column(db.String(200), nullable=True)
    option_c = db.Column(db.String(200), nullable=True)
    option_d = db.Column(db.String(200), nullable=True)
    correct_answer = db.Column(db.String(200), nullable=False)  # e.g., 'A', 'True', or exact text
    explanation = db.Column(db.Text, nullable=True)

class QuizResult(db.Model):
    __tablename__ = 'quiz_results'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    points_earned = db.Column(db.Integer, default=0, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

class DailyChallenge(db.Model):
    __tablename__ = 'daily_challenges'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False, default=date.today)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    
    # Relationship
    quiz = db.relationship('Quiz', backref='daily_challenge', uselist=False)

class StudyMaterial(db.Model):
    __tablename__ = 'study_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # 'pdf', 'docx', 'txt'
    size = db.Column(db.Integer, nullable=False)  # bytes
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    summaries = db.relationship('Summary', backref='material', cascade="all, delete-orphan", lazy='dynamic')

class Summary(db.Model):
    __tablename__ = 'summaries'
    
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('study_materials.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    short_summary = db.Column(db.Text, nullable=False)
    detailed_summary = db.Column(db.Text, nullable=False)
    bullet_points = db.Column(db.Text, nullable=False)  # Comma or newline separated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WeakTopic(db.Model):
    __tablename__ = 'weak_topics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    topic_name = db.Column(db.String(150), nullable=False)
    confidence_score = db.Column(db.Float, default=0.0, nullable=False)  # 0.0 to 1.0
    suggested_materials = db.Column(db.Text, nullable=True)  # JSON/serialized text suggestions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Achievement(db.Model):
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    badge_name = db.Column(db.String(100), nullable=False)
    badge_code = db.Column(db.String(50), nullable=False)  # e.g., 'beginner_learner'
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

class Leaderboard(db.Model):
    __tablename__ = 'leaderboards'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    rank = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, default=0, nullable=False)
    streak = db.Column(db.Integer, default=0, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('leaderboard_entry', uselist=False))

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'streak', 'quiz', 'achievement', 'general'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(150), nullable=False)  # e.g. 'Logged In', 'Completed Quiz'
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class PlacementProgress(db.Model):
    __tablename__ = 'placement_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module = db.Column(db.String(50), nullable=False)
    topic = db.Column(db.String(100), nullable=True)
    difficulty = db.Column(db.String(20), default='medium', nullable=False)
    score = db.Column(db.Integer, default=0, nullable=False)
    total_questions = db.Column(db.Integer, default=0, nullable=False)
    weak_topics = db.Column(db.Text, nullable=True)
    last_practiced = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CodingProgress(db.Model):
    __tablename__ = 'coding_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), default='medium', nullable=False)
    problems_solved = db.Column(db.Integer, default=0, nullable=False)
    total_attempted = db.Column(db.Integer, default=0, nullable=False)
    score_avg = db.Column(db.Float, default=0.0, nullable=False)
    roadmap_progress = db.Column(db.Text, nullable=True)
    last_practiced = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Resume(db.Model):
    __tablename__ = 'resumes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    education = db.Column(db.Text, nullable=True)
    skills = db.Column(db.Text, nullable=True)
    projects = db.Column(db.Text, nullable=True)
    experience = db.Column(db.Text, nullable=True)
    achievements = db.Column(db.Text, nullable=True)
    resume_score = db.Column(db.Integer, default=0, nullable=False)
    content = db.Column(db.Text, nullable=True)
    pdf_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InterviewHistory(db.Model):
    __tablename__ = 'interview_histories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    interview_type = db.Column(db.String(30), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    questions = db.Column(db.Text, nullable=True)
    answers = db.Column(db.Text, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    confidence_score = db.Column(db.Float, default=0.0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CareerRoadmap(db.Model):
    __tablename__ = 'career_roadmaps'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    career_path = db.Column(db.String(80), nullable=False)
    roadmap_data = db.Column(db.Text, nullable=True)
    courses = db.Column(db.Text, nullable=True)
    progress_percent = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class KnowledgeBaseAnswer(db.Model):
    __tablename__ = 'knowledge_base_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)
    question = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.Text, nullable=True)  # Comma-separated keywords
    answer = db.Column(db.Text, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    subject = db.relationship('Subject', backref='knowledge_base_answers')
    created_by = db.relationship('User', backref='knowledge_base_answers')

class UnansweredQuestion(db.Model):
    __tablename__ = 'unanswered_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_resolved = db.Column(db.Boolean, default=False, nullable=False)
    
    subject = db.relationship('Subject', backref='unanswered_questions')
    user = db.relationship('User', backref='unanswered_questions')
