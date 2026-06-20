from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import db
from models.models import (
    User, StudentProfile, StudyMaterial, Quiz, Conversation, ActivityLog,
    KnowledgeBaseAnswer, UnansweredQuestion, Subject
)

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def enforce_admin_role():
    # Only allow access to admins
    if current_user.role != 'admin':
        abort(403) # Forbidden

@admin_bp.route('/admin')
def dashboard():
    # Admin stats
    total_students = User.query.filter_by(role='student', is_deleted=False).count()
    total_quizzes = Quiz.query.count()
    total_chats = Conversation.query.filter_by(is_deleted=False).count()
    total_materials = StudyMaterial.query.filter_by(is_deleted=False).count()
    pending_approvals = StudyMaterial.query.filter_by(is_approved=False, is_deleted=False).count()
    
    # Activity Log
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(15).all()
    
    return render_template(
        'admin_dashboard.html',
        total_students=total_students,
        total_quizzes=total_quizzes,
        total_chats=total_chats,
        total_materials=total_materials,
        pending_approvals=pending_approvals,
        logs=logs
    )

@admin_bp.route('/admin/students')
def manage_students():
    query = request.args.get('q', '').strip()
    
    student_query = User.query.filter_by(role='student', is_deleted=False)
    if query:
        student_query = student_query.filter(
            (User.username.ilike(f"%{query}%")) | 
            (User.email.ilike(f"%{query}%"))
        )
        
    students = student_query.all()
    
    return render_template('admin_students.html', students=students, search_query=query)

@admin_bp.route('/admin/students/<int:student_id>/edit', methods=['POST'])
def edit_student(student_id):
    student = User.query.filter_by(id=student_id, role='student', is_deleted=False).first_or_404()
    
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    points = request.form.get('points')
    
    if not username or not email:
        flash("Username and Email are required.", "danger")
        return redirect(url_for('admin.manage_students'))
        
    # Check duplicate email
    existing_email = User.query.filter(User.email == email, User.id != student_id).first()
    if existing_email:
        flash("Email is already used by another user.", "danger")
        return redirect(url_for('admin.manage_students'))
        
    student.username = username
    student.email = email
    
    if points is not None and student.profile:
        try:
            student.profile.total_points = int(points)
        except ValueError:
            pass
            
    # Log admin action
    log = ActivityLog(
        user_id=current_user.id,
        action="Admin Edited Student",
        details=f"Edited student {student.username} (ID: {student.id})"
    )
    db.session.add(log)
    
    db.session.commit()
    flash(f"Student details for '{username}' updated successfully.", "success")
    return redirect(url_for('admin.manage_students'))

@admin_bp.route('/admin/students/<int:student_id>/delete', methods=['POST'])
def delete_student(student_id):
    student = User.query.filter_by(id=student_id, role='student', is_deleted=False).first_or_404()
    
    student.is_deleted = True
    
    # Log admin action
    log = ActivityLog(
        user_id=current_user.id,
        action="Admin Deleted Student",
        details=f"Soft deleted student {student.username} (ID: {student.id})"
    )
    db.session.add(log)
    
    db.session.commit()
    flash(f"Student '{student.username}' has been deleted.", "success")
    return redirect(url_for('admin.manage_students'))

@admin_bp.route('/admin/materials')
def manage_materials():
    query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'all')
    
    mat_query = StudyMaterial.query.filter_by(is_deleted=False)
    
    if query:
        mat_query = mat_query.filter(StudyMaterial.file_name.ilike(f"%{query}%"))
        
    if status_filter == 'pending':
        mat_query = mat_query.filter_by(is_approved=False)
    elif status_filter == 'approved':
        mat_query = mat_query.filter_by(is_approved=True)
        
    materials = mat_query.order_by(StudyMaterial.uploaded_at.desc()).all()
    
    return render_template(
        'admin_materials.html',
        materials=materials,
        search_query=query,
        status_filter=status_filter
    )

@admin_bp.route('/admin/materials/<int:material_id>/approve', methods=['POST'])
def approve_material(material_id):
    material = StudyMaterial.query.filter_by(id=material_id, is_deleted=False).first_or_404()
    material.is_approved = True
    
    # Log admin action
    log = ActivityLog(
        user_id=current_user.id,
        action="Admin Approved Material",
        details=f"Approved file: {material.file_name}"
    )
    db.session.add(log)
    
    db.session.commit()
    flash(f"Material '{material.file_name}' approved successfully.", "success")
    return redirect(url_for('admin.manage_materials'))

@admin_bp.route('/admin/materials/<int:material_id>/delete', methods=['POST'])
def delete_material(material_id):
    material = StudyMaterial.query.filter_by(id=material_id, is_deleted=False).first_or_404()
    material.is_deleted = True
    
    # Log admin action
    log = ActivityLog(
        user_id=current_user.id,
        action="Admin Deleted Material",
        details=f"Deleted file: {material.file_name}"
    )
    db.session.add(log)
    
    db.session.commit()
    flash(f"Material '{material.file_name}' deleted.", "success")
    return redirect(url_for('admin.manage_materials'))

@admin_bp.route('/admin/chatbot')
def manage_chatbot():
    unanswered = UnansweredQuestion.query.filter_by(is_resolved=False).order_by(UnansweredQuestion.timestamp.desc()).all()
    kb_answers = KnowledgeBaseAnswer.query.order_by(KnowledgeBaseAnswer.created_at.desc()).all()
    subjects = Subject.query.filter_by(is_deleted=False).all()
    return render_template(
        'admin_chatbot.html',
        unanswered=unanswered,
        kb_answers=kb_answers,
        subjects=subjects
    )

@admin_bp.route('/admin/chatbot/kb/add', methods=['POST'])
def add_kb_answer():
    question = request.form.get('question', '').strip()
    answer = request.form.get('answer', '').strip()
    keywords = request.form.get('keywords', '').strip()
    subject_id = request.form.get('subject_id')
    unanswered_id = request.form.get('unanswered_id')
    
    if not question or not answer:
        flash("Question and Answer are required.", "danger")
        return redirect(url_for('admin.manage_chatbot'))
        
    try:
        sub_id = int(subject_id) if subject_id else None
    except ValueError:
        sub_id = None
        
    existing = KnowledgeBaseAnswer.query.filter_by(question=question, subject_id=sub_id).first()
    if existing:
        flash("This question is already in the knowledge base.", "warning")
        return redirect(url_for('admin.manage_chatbot'))
        
    new_kb = KnowledgeBaseAnswer(
        question=question,
        answer=answer,
        keywords=keywords,
        subject_id=sub_id,
        created_by_id=current_user.id
    )
    db.session.add(new_kb)
    
    if unanswered_id:
        unanswered = UnansweredQuestion.query.get(unanswered_id)
        if unanswered:
            unanswered.is_resolved = True
            
    log = ActivityLog(
        user_id=current_user.id,
        action="Admin Added KB Answer",
        details=f"Added answer for: '{question[:50]}...'"
    )
    db.session.add(log)
    db.session.commit()
    
    flash("Knowledge base answer added successfully.", "success")
    return redirect(url_for('admin.manage_chatbot'))

@admin_bp.route('/admin/chatbot/kb/<int:kb_id>/edit', methods=['POST'])
def edit_kb_answer(kb_id):
    kb = KnowledgeBaseAnswer.query.get_or_404(kb_id)
    
    question = request.form.get('question', '').strip()
    answer = request.form.get('answer', '').strip()
    keywords = request.form.get('keywords', '').strip()
    subject_id = request.form.get('subject_id')
    
    if not question or not answer:
        flash("Question and Answer are required.", "danger")
        return redirect(url_for('admin.manage_chatbot'))
        
    try:
        sub_id = int(subject_id) if subject_id else None
    except ValueError:
        sub_id = None
        
    kb.question = question
    kb.answer = answer
    kb.keywords = keywords
    kb.subject_id = sub_id
    
    log = ActivityLog(
        user_id=current_user.id,
        action="Admin Edited KB Answer",
        details=f"Edited answer for ID: {kb.id}"
    )
    db.session.add(log)
    db.session.commit()
    
    flash("Knowledge base answer updated successfully.", "success")
    return redirect(url_for('admin.manage_chatbot'))

@admin_bp.route('/admin/chatbot/kb/<int:kb_id>/delete', methods=['POST'])
def delete_kb_answer(kb_id):
    kb = KnowledgeBaseAnswer.query.get_or_404(kb_id)
    
    log = ActivityLog(
        user_id=current_user.id,
        action="Admin Deleted KB Answer",
        details=f"Deleted answer for ID: {kb.id}"
    )
    db.session.add(log)
    db.session.delete(kb)
    db.session.commit()
    
    flash("Knowledge base answer deleted.", "success")
    return redirect(url_for('admin.manage_chatbot'))

@admin_bp.route('/admin/chatbot/unanswered/<int:uq_id>/delete', methods=['POST'])
def delete_unanswered_question(uq_id):
    uq = UnansweredQuestion.query.get_or_404(uq_id)
    uq.is_resolved = True
    
    log = ActivityLog(
        user_id=current_user.id,
        action="Admin Dismissed Question",
        details=f"Dismissed unanswered question: '{uq.question[:50]}...'"
    )
    db.session.add(log)
    db.session.commit()
    
    flash("Unanswered question dismissed.", "success")
    return redirect(url_for('admin.manage_chatbot'))
