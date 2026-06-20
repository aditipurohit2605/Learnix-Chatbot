from .chatbot_service import get_chatbot_response, get_chatbot_reply
from .quiz_service import generate_quiz, generate_quiz_from_conversation, evaluate_conversation_quiz
from .summarizer_service import extract_text_from_file, generate_summary
from .weak_topic import analyze_student_performance
from .recommendation import get_recommendations
from .college_service import (
    PLACEMENT_MODULES, DSA_TOPICS, TECH_INTERVIEW_TOPICS, HR_INTERVIEW_TOPICS,
    COMPANIES, CAREER_PATHS, generate_placement_quiz, get_coding_explanation,
    get_coding_practice, start_mock_interview, evaluate_interview_answer,
    generate_resume_content, score_resume, generate_resume_pdf, generate_career_roadmap,
    calculate_readiness_scores, get_placement_weak_topics, get_company_experiences,
    COMPANY_QUESTIONS
)
