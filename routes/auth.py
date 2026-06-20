import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db
from models.models import User, StudentProfile, ActivityLog

auth_bp = Blueprint('auth', __name__)

def allowed_file(filename, file_type='avatar'):
    allowed_set = current_app.config['ALLOWED_EXTENSIONS'][file_type]
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'student') # default is student
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.register'))
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))
            
        # Check existence
        if User.query.filter_by(username=username).first():
            flash('Username is already taken.', 'danger')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email is already registered.', 'danger')
            return redirect(url_for('auth.register'))
            
        # Create User
        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush() # Populate new_user.id
        
        # Create student profile if role is student
        if role == 'student':
            new_profile = StudentProfile(user_id=new_user.id, bio="Welcome to my Learnix profile!")
            db.session.add(new_profile)
            
        # Log action
        log = ActivityLog(user_id=new_user.id, action="Registered Account", details=f"Role: {role}")
        db.session.add(log)
        
        try:
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'danger')
            
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username, is_deleted=False).first()
        
        if not user or not user.check_password(password):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=remember)
        
        # Log activity
        log = ActivityLog(user_id=user.id, action="Logged In", details="Success")
        db.session.add(log)
        db.session.commit()
        
        flash(f'Welcome back, {user.username}!', 'success')
        
        # Redirect based on role
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
        
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    # Log activity before logout
    log = ActivityLog(user_id=current_user.id, action="Logged Out")
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('student.landing'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email, is_deleted=False).first()
        if user:
            flash(f'Password reset instructions have been sent to {email}.', 'success')
        else:
            flash('If that email is registered, we have sent instructions.', 'info')
        return redirect(url_for('auth.login'))
        
    return render_template('login.html', forgot_mode=True)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        bio = request.form.get('bio', '').strip()
        email = request.form.get('email', '').strip()
        
        # Email update validation
        if email != current_user.email:
            existing = User.query.filter_by(email=email).first()
            if existing:
                flash('Email is already in use.', 'danger')
                return redirect(url_for('auth.profile'))
            current_user.email = email
            
        # Update Bio in profile
        if current_user.role == 'student' and current_user.profile:
            current_user.profile.bio = bio
            
        # Handle Avatar Upload
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename != '':
            if allowed_file(avatar_file.filename, 'avatar'):
                filename = secure_filename(f"user_{current_user.id}_{avatar_file.filename}")
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars', filename)
                
                # Remove old avatar if it's not the default
                if current_user.avatar:
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars', current_user.avatar)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except Exception as e:
                            print(f"Failed to remove old avatar: {e}")
                            
                avatar_file.save(upload_path)
                current_user.avatar = filename
            else:
                flash('Invalid file extension for profile avatar.', 'danger')
                return redirect(url_for('auth.profile'))
                
        # Log action
        log = ActivityLog(user_id=current_user.id, action="Updated Profile")
        db.session.add(log)
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {e}', 'danger')
            
        return redirect(url_for('auth.profile'))
        
    return render_template('profile.html')
