import json
from models.models import StudentProfile, WeakTopic, StudyMaterial, Subject, Quiz, PlacementProgress, CodingProgress, Resume

def get_recommendations(user_id):
    """
    Analyzes student data to produce actionable recommendations.
    Returns: list of dicts with keys (title, description, action_url, action_text, icon, type)
    """
    recs = []
    
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    
    # 1. Streak Recommendation
    if profile:
        if profile.current_streak == 0:
            recs.append({
                "title": "Start Your Streak!",
                "description": "You haven't completed a learning activity today. Solve today's Daily Quiz Challenge to start your streak!",
                "action_url": "/daily-quiz",
                "action_text": "Play Daily Quiz",
                "icon": "fire-alt",
                "type": "streak"
            })
        elif profile.current_streak < 3:
            recs.append({
                "title": "Keep the Streak Burning!",
                "description": f"You're on a {profile.current_streak}-day streak. Keep your momentum going by playing today's challenge!",
                "action_url": "/daily-quiz",
                "action_text": "Extend Streak",
                "icon": "fire-alt",
                "type": "streak"
            })
            
    # 2. Weak Topics Recommendation
    weak_topics = WeakTopic.query.filter_by(user_id=user_id).all()
    if weak_topics:
        # Sort by confidence score (lowest first)
        weak_topics.sort(key=lambda x: x.confidence_score)
        worst_topic = weak_topics[0]
        subject = Subject.query.get(worst_topic.subject_id)
        if subject:
            recs.append({
                "title": f"Strengthen {subject.name}",
                "description": f"Your confidence score in {subject.name} is {int(worst_topic.confidence_score * 100)}%. Generate a personalized quiz to practice.",
                "action_url": f"/quiz-gen?subject={subject.name}",
                "action_text": "Practice Now",
                "icon": "graduation-cap",
                "type": "weak_topic"
            })
            
    # 3. Unsummarized Material Recommendation
    unsummarized_materials = StudyMaterial.query.filter_by(user_id=user_id, is_deleted=False).all()
    # Find one material that doesn't have a summary yet
    target_material = None
    for mat in unsummarized_materials:
        if mat.summaries.count() == 0:
            target_material = mat
            break
            
    if target_material:
        recs.append({
            "title": "Summarize Your Notes",
            "description": f"You uploaded '{target_material.file_name}' but haven't summarized it yet. Let Learnix AI summarize it for you.",
            "action_url": "/summarizer",
            "action_text": "Summarize Notes",
            "icon": "file-alt",
            "type": "material"
        })
        
    # 4. Placement readiness recommendation
    placement_count = PlacementProgress.query.filter_by(user_id=user_id).count()
    if placement_count == 0:
        recs.append({
            "title": "Start Placement Prep",
            "description": "Begin your campus placement journey with aptitude, reasoning, and puzzle modules.",
            "action_url": "/placement",
            "action_text": "Start Prep",
            "icon": "briefcase",
            "type": "placement"
        })

    # 5. Coding practice recommendation
    coding_count = CodingProgress.query.filter_by(user_id=user_id).count()
    if coding_count == 0:
        recs.append({
            "title": "Practice DSA",
            "description": "Build coding interview skills with AI-powered explanations across 10 DSA topics.",
            "action_url": "/coding",
            "action_text": "Start Coding",
            "icon": "code",
            "type": "coding"
        })

    # 6. Resume recommendation
    if not Resume.query.filter_by(user_id=user_id).first():
        recs.append({
            "title": "Build Your Resume",
            "description": "Create an ATS-friendly resume with AI optimization and get your resume score.",
            "action_url": "/resume-builder",
            "action_text": "Build Resume",
            "icon": "file-alt",
            "type": "resume"
        })

    # 7. Default general recommendations if recommendation list is short
    if len(recs) < 2:
        recs.append({
            "title": "Solve Doubts with Chatbot",
            "description": "Stuck on a tricky homework question? Start a chat with the Learnix AI Assistant in any subject.",
            "action_url": "/subjects",
            "action_text": "Start Learning",
            "icon": "comments",
            "type": "general"
        })
        recs.append({
            "title": "Aim for Quiz Master",
            "description": "Earn points by passing practice quizzes to unlock the 'Quiz Master' badge!",
            "action_url": "/quiz-gen",
            "action_text": "Generate Quiz",
            "icon": "trophy",
            "type": "general"
        })
        
    return recs[:3]  # Return top 3 recommendations
