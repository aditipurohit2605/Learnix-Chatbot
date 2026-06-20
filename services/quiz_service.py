import json
from .ai_client import ai_client

MOCK_QUIZZES = {
    "Data Structures & Algorithms": {
        "easy": [
            {
                "question_text": "Which data structure operates on a Last-In, First-Out (LIFO) basis?",
                "question_type": "mcq",
                "option_a": "Queue", "option_b": "Stack", "option_c": "Linked List", "option_d": "Binary Tree",
                "correct_answer": "B",
                "explanation": "A stack pushes and pops items from the same end, making the last added item the first to be removed (LIFO)."
            },
            {
                "question_text": "Time complexity of linear search in worst case is O(n).",
                "question_type": "true_false",
                "option_a": "True", "option_b": "False", "option_c": "", "option_d": "",
                "correct_answer": "True",
                "explanation": "Linear search checks each element sequentially, so worst case is O(n)."
            },
            {
                "question_text": "Python is a ________-typed language.",
                "question_type": "fill_in",
                "option_a": "", "option_b": "", "option_c": "", "option_d": "",
                "correct_answer": "dynamically",
                "explanation": "Python uses dynamic typing, where variable types are determined at runtime."
            }
        ],
        "medium": [
            {
                "question_text": "What is the average time complexity of the Quick Sort algorithm?",
                "question_type": "mcq",
                "option_a": "O(n)", "option_b": "O(n log n)", "option_c": "O(n^2)", "option_d": "O(log n)",
                "correct_answer": "B",
                "explanation": "Quick Sort has an average time complexity of O(n log n), although its worst-case complexity can degrade to O(n^2) if pivot selection is poor."
            },
            {
                "question_text": "A binary search tree with n nodes has a minimum height of log2(n+1).",
                "question_type": "true_false",
                "option_a": "True", "option_b": "False", "option_c": "", "option_d": "",
                "correct_answer": "True",
                "explanation": "Minimum height is achieved when the tree is perfectly balanced."
            }
        ],
        "hard": [
            {
                "question_text": "Which algorithm solves the single-source shortest path problem for graphs with non-negative edge weights?",
                "question_type": "mcq",
                "option_a": "Dijkstra's algorithm", "option_b": "Bellman-Ford", "option_c": "Floyd-Warshall", "option_d": "Prim's algorithm",
                "correct_answer": "A",
                "explanation": "Dijkstra's algorithm efficiently finds shortest paths in graphs with non-negative weights."
            }
        ]
    },
    "Database Management Systems": {
        "easy": [
            {
                "question_text": "What does SQL stand for?",
                "question_type": "mcq",
                "option_a": "Structured Query Language", "option_b": "Simple Question Language", "option_c": "Sequential Query Logic", "option_d": "Standard Query Library",
                "correct_answer": "A",
                "explanation": "SQL is the standard language for relational database management systems."
            },
            {
                "question_text": "A primary key can have NULL values.",
                "question_type": "true_false",
                "option_a": "True", "option_b": "False", "option_c": "", "option_d": "",
                "correct_answer": "False",
                "explanation": "Primary keys must have unique, non-null values to uniquely identify records."
            },
            {
                "question_text": "________ is used to retrieve data from a database table.",
                "question_type": "fill_in",
                "option_a": "", "option_b": "", "option_c": "", "option_d": "",
                "correct_answer": "SELECT",
                "explanation": "The SELECT statement is the fundamental SQL command for querying databases."
            }
        ],
        "medium": [
            {
                "question_text": "Which normal form eliminates transitive dependencies?",
                "question_type": "mcq",
                "option_a": "1NF", "option_b": "2NF", "option_c": "3NF", "option_d": "BCNF",
                "correct_answer": "C",
                "explanation": "Third Normal Form (3NF) removes transitive dependencies from relations."
            }
        ]
    },
    "Communication Skills": {
        "easy": [
            {
                "question_text": "What is the STAR method used for?",
                "question_type": "mcq",
                "option_a": "Writing resumes", "option_b": "Answering behavioral interview questions", "option_c": "Solving coding problems", "option_d": "Designing systems",
                "correct_answer": "B",
                "explanation": "STAR (Situation, Task, Action, Result) is a framework for structuring responses to behavioral questions."
            },
            {
                "question_text": "Active listening means interrupting the speaker to ask questions quickly.",
                "question_type": "true_false",
                "option_a": "True", "option_b": "False", "option_c": "", "option_d": "",
                "correct_answer": "False",
                "explanation": "Active listening involves fully concentrating, understanding, responding, and then remembering what is said."
            },
            {
                "question_text": "Professional emails should end with a polite ________.",
                "question_type": "fill_in",
                "option_a": "", "option_b": "", "option_c": "", "option_d": "",
                "correct_answer": "closing",
                "explanation": "Appropriate closings like 'Sincerely' or 'Best regards' add professionalism to emails."
            }
        ]
    }
}

def generate_quiz(subject_name, source_type, content_text="", difficulty="medium", num_questions=3):
    """
    Generates a structured quiz from subject, notes, or weak topics.
    Returns: list of dicts matching the structure of QuizQuestion model.
    """
    
    if ai_client.is_available():
        prompt = (
            f"Generate a quiz of {num_questions} questions for the subject '{subject_name}' at '{difficulty}' difficulty level. "
            f"Source type: '{source_type}'. "
        )
        if content_text:
            prompt += f"Base the questions on the following content material:\n\n{content_text[:2000]}\n\n"
            
        prompt += (
            "You MUST output raw JSON ONLY. No markdown wrapper, no ```json formatting, just the raw JSON array. "
            "Each item in the JSON array must represent a question and contain the following keys exactly:\n"
            "- 'question_text': text of the question\n"
            "- 'question_type': 'mcq', 'true_false', or 'fill_in'\n"
            "- 'option_a': choice A (required for mcq, 'True' for true_false, empty string for fill_in)\n"
            "- 'option_b': choice B (required for mcq, 'False' for true_false, empty string for fill_in)\n"
            "- 'option_c': choice C (required for mcq, empty string for true_false and fill_in)\n"
            "- 'option_d': choice D (required for mcq, empty string for true_false and fill_in)\n"
            "- 'correct_answer': 'A', 'B', 'C', or 'D' for 'mcq'; 'True' or 'False' for 'true_false'; or the exact text answer for 'fill_in'\n"
            "- 'explanation': brief educational explanation why the answer is correct\n"
        )
        
        try:
            messages = [
                {"role": "system", "content": "You are a professional educational assessor. You output strict, valid JSON arrays matching requested schemas."},
                {"role": "user", "content": prompt}
            ]
            response = ai_client.get_completion(messages, temperature=0.5)
            # Remove any markdown formatting just in case the model added it
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response.split("\n", 1)[1]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response.rsplit("\n", 1)[0]
            cleaned_response = cleaned_response.strip("` \n")
            
            questions = json.loads(cleaned_response)
            if isinstance(questions, list) and len(questions) > 0:
                # Validate schema of each question
                validated = []
                for q in questions:
                    validated.append({
                        "question_text": q.get("question_text", "Sample question?"),
                        "question_type": q.get("question_type", "mcq"),
                        "option_a": q.get("option_a", ""),
                        "option_b": q.get("option_b", ""),
                        "option_c": q.get("option_c", ""),
                        "option_d": q.get("option_d", ""),
                        "correct_answer": q.get("correct_answer", "A"),
                        "explanation": q.get("explanation", "")
                    })
                return validated
        except Exception as e:
            print(f"Failed to generate AI quiz, falling back: {e}")
            # fall through to mock generator

    # Fallback to local structured data
    subject_group = MOCK_QUIZZES.get(subject_name, MOCK_QUIZZES["Data Structures & Algorithms"])
    questions_pool = subject_group.get(difficulty, subject_group["easy"])
    
    # Slice to fit the requested amount
    results = questions_pool[:num_questions]
    
    # If we need more questions than are in the pool, loop them or populate generic ones
    while len(results) < num_questions:
        results.append({
            "question_text": f"Bonus Practice: Under the rules of {subject_name}, this statement is always true.",
            "question_type": "true_false",
            "option_a": "True", "option_b": "False", "option_c": "", "option_d": "",
            "correct_answer": "True",
            "explanation": "Practice makes perfect in all subjects!"
        })
        
    return results


def generate_quiz_from_conversation(subject_name, conversation_messages, topic=None):
    """
    Generate a structured quiz from chat conversation context.
    Returns dict with easy/medium/hard question lists and metadata.
    """
    context_lines = []
    for msg in conversation_messages[-16:]:
        role = msg.get("role", "user")
        content = (msg.get("content") or "").strip()
        if content:
            context_lines.append(f"{role.upper()}: {content[:500]}")

    conversation_text = "\n".join(context_lines)
    topic_label = topic or subject_name

    if ai_client.is_available():
        prompt = (
            f"Based on this tutoring conversation about '{topic_label}', generate a quiz.\n\n"
            f"CONVERSATION:\n{conversation_text}\n\n"
            "Output raw JSON ONLY (no markdown). Structure:\n"
            "{\n"
            '  "topic": "topic name",\n'
            '  "easy": [5 MCQ objects],\n'
            '  "medium": [3 MCQ objects],\n'
            '  "hard": [2 MCQ objects]\n'
            "}\n"
            "Each MCQ object must have: question_text, option_a, option_b, option_c, option_d, "
            "correct_answer (A/B/C/D), explanation, difficulty (easy/medium/hard)."
        )
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an educational assessor. Output strict valid JSON only. "
                        "Questions must relate directly to the conversation topic."
                    ),
                },
                {"role": "user", "content": prompt},
            ]
            response = ai_client.get_completion(messages, temperature=0.4)
            if response:
                cleaned = response.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1]
                if cleaned.endswith("```"):
                    cleaned = cleaned.rsplit("\n", 1)[0]
                cleaned = cleaned.strip("` \n")
                data = json.loads(cleaned)
                if isinstance(data, dict) and data.get("easy"):
                    return _normalize_conversation_quiz(data, topic_label)
        except Exception as e:
            print(f"Conversation quiz AI failed, using fallback: {e}")

    return _fallback_conversation_quiz(subject_name, topic_label)


def _normalize_conversation_quiz(data, topic_label):
    result = {"topic": data.get("topic", topic_label), "easy": [], "medium": [], "hard": []}
    for level in ("easy", "medium", "hard"):
        for q in data.get(level, []):
            result[level].append({
                "question_text": q.get("question_text", "Sample question?"),
                "question_type": "mcq",
                "option_a": q.get("option_a", "Option A"),
                "option_b": q.get("option_b", "Option B"),
                "option_c": q.get("option_c", "Option C"),
                "option_d": q.get("option_d", "Option D"),
                "correct_answer": q.get("correct_answer", "A"),
                "explanation": q.get("explanation", ""),
                "difficulty": level,
            })
    return result


def _fallback_conversation_quiz(subject_name, topic_label):
    """Build a 10-question quiz from local mock data when AI is unavailable."""
    pool = MOCK_QUIZZES.get(subject_name, MOCK_QUIZZES["Data Structures & Algorithms"])
    easy = [_attach_difficulty(q, "easy") for q in pool.get("easy", [])[:5]]
    medium = [_attach_difficulty(q, "medium") for q in pool.get("medium", [])[:3]]
    hard = [_attach_difficulty(q, "hard") for q in pool.get("hard", [])[:2]]

    while len(easy) < 5:
        easy.append(_generic_mcq(topic_label, "easy", len(easy) + 1))
    while len(medium) < 3:
        medium.append(_generic_mcq(topic_label, "medium", len(medium) + 1))
    while len(hard) < 2:
        hard.append(_generic_mcq(topic_label, "hard", len(hard) + 1))

    return {"topic": topic_label, "easy": easy, "medium": medium, "hard": hard}


def _attach_difficulty(q, level):
    item = dict(q)
    item["difficulty"] = level
    return item


def _generic_mcq(topic, level, num):
    return {
        "question_text": f"[{level.title()}] Which statement about {topic} is correct? (Q{num})",
        "question_type": "mcq",
        "option_a": f"{topic} is a core engineering concept",
        "option_b": f"{topic} is unrelated to placements",
        "option_c": f"{topic} has no practical applications",
        "option_d": f"{topic} is only for school-level study",
        "correct_answer": "A",
        "explanation": f"{topic} is essential for engineering students.",
        "difficulty": level,
    }


def evaluate_conversation_quiz(questions, user_answers):
    """
    Evaluate quiz answers and return score, weak areas, and suggestions.
    user_answers: dict mapping question index (str) -> answer letter
    """
    correct = 0
    wrong = []
    weak_areas = []

    for i, q in enumerate(questions):
        submitted = str(user_answers.get(str(i), "")).strip().upper()
        expected = str(q.get("correct_answer", "A")).strip().upper()
        if submitted == expected:
            correct += 1
        else:
            wrong.append({
                "index": i,
                "question": q.get("question_text"),
                "your_answer": submitted or "No answer",
                "correct_answer": expected,
                "explanation": q.get("explanation", ""),
            })
            weak_areas.append(q.get("difficulty", "general"))

    total = len(questions)
    score_pct = int(correct / total * 100) if total else 0

    suggestions = []
    if score_pct >= 80:
        suggestions.append("Excellent work! Try harder problems or mock interviews.")
    elif score_pct >= 60:
        suggestions.append("Good progress. Review explanations for wrong answers.")
    else:
        suggestions.append("Re-read the topic explanation in chat, then retry the quiz.")

    if "hard" in weak_areas:
        suggestions.append("Focus on advanced concepts and interview-style problems.")
    if "medium" in weak_areas:
        suggestions.append("Practice more medium-difficulty application questions.")
    if "easy" in weak_areas:
        suggestions.append("Strengthen fundamentals before moving to harder topics.")

    return {
        "score": correct,
        "total": total,
        "percentage": score_pct,
        "wrong_answers": wrong,
        "weak_areas": list(dict.fromkeys(weak_areas)),
        "suggestions": suggestions,
    }
