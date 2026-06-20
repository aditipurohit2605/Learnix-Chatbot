# Learnix — AI Engineering & Placement Platform

Learnix is a production-ready AI-powered college learning and placement preparation platform for engineering students (B.Tech, BE, MCA, BCA, CSE).

**Tagline:** *Learn Smarter with AI*

---

## Features

### For Students
- **AI Chat Assistant** — ChatGPT-style tutor with conversation memory, web-assisted answers, structured markdown responses
- **Generate Quiz from Conversation** — Discuss a topic, then auto-generate Easy/Medium/Hard MCQs with scoring and weak-area analysis
- **Quiz Generator** — MCQ, True/False, fill-in quizzes from subjects or uploaded notes
- **Notes Summarizer** — PDF, DOCX, TXT summarization
- **Placement Hub** — Aptitude, coding, interview, resume, company prep, career roadmap
- **Progress Analytics** — Charts, weak topic detection, leaderboard, achievements

### For Admins
- Student management, material moderation, chatbot knowledge base, activity logs

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python Flask, SQLAlchemy |
| Database | SQLite |
| Auth | Flask-Login |
| AI | Google Gemini API + DuckDuckGo/Wikipedia web search |
| Frontend | HTML, CSS, JavaScript (dark theme, responsive) |

---

## Installation

### Prerequisites
- Python 3.8+
- pip

### 1. Clone and install dependencies
```bash
cd "Learnix chatbot"
pip install -r requirements.txt
```

### 2. Configure environment
Copy `.env.example` to `.env` and set your values:

```bash
# Windows PowerShell
copy .env.example .env
$env:GOOGLE_API_KEY="your-gemini-api-key"
$env:SECRET_KEY="your-random-secret-key"
```

```bash
# Linux / macOS
cp .env.example .env
export GOOGLE_API_KEY="your-gemini-api-key"
export SECRET_KEY="your-random-secret-key"
```

Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).

> **Note:** Without an API key, Learnix uses rich offline educational fallbacks — the app still works.

### 3. Run the application
```bash
python app.py
```

Open: **http://127.0.0.1:5000**

---

## Deployment (Production)

### Using Gunicorn (Linux)
```bash
pip install gunicorn
export GOOGLE_API_KEY="your-key"
export SECRET_KEY="strong-random-secret"
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

### Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes (prod) | Flask session secret |
| `GOOGLE_API_KEY` | Recommended | Gemini API key |
| `GOOGLE_MODEL` | No | Default: `gemini-2.0-flash` |
| `DATABASE_URL` | No | Default: SQLite in `instance/` |

### Security Checklist
- Never commit `.env` or API keys (see `.gitignore`)
- Change default admin/student passwords before production
- Use HTTPS behind a reverse proxy (nginx/Caddy)
- Set `debug=False` for production

---

## Default Accounts

| Role | Username | Password |
|------|----------|----------|
| Student | `student` | `studentpassword` |
| Admin | `admin` | `adminpassword` |

---

## Engineering Subjects (Seeded)

DSA, OOP, DBMS, OS, CN, Software Engineering, Python, Java, C, C++, Web Development, AI, ML, Data Science, Cloud Computing, Cyber Security, DevOps, System Design, Generative AI, Placement Prep, Interview Prep, Communication Skills, Resume Help, Career Guidance

School subjects (History, Geography, Biology, etc.) are removed on startup.

---

## Issues Fixed in This Release

1. **Chatbot** — AI-first flow with Gemini + web search; never returns "service unavailable" errors
2. **Conversation quiz** — Generate 10 MCQs (5 Easy / 3 Medium / 2 Hard) from chat context
3. **Missing fallback keys** — Fixed KeyError for trees, graphs, arrays, linked_lists
4. **API key security** — Removed hardcoded key from config; env-only via `.env`
5. **Database seeding** — Idempotent subject seeding; removes deprecated school subjects
6. **Profile avatars** — Professional circular photos or user initials (no robot/cartoon avatars)
7. **UI/UX** — Dark theme, responsive subjects page, modern chat interface
8. **Import fixes** — `get_chatbot_reply` positional argument bug fixed
9. **`.gitignore`** — Expanded to exclude secrets, uploads, database
10. **Structured responses** — ChatGPT-style headings, lists, code blocks, tables

---

## Project Structure

```
Learnix chatbot/
├── app.py                 # Application factory + DB seeding
├── config.py              # Environment-based configuration
├── requirements.txt
├── .env.example
├── models/models.py       # SQLAlchemy models
├── services/
│   ├── ai_client.py       # Gemini client
│   ├── web_search.py      # DuckDuckGo + Wikipedia search
│   ├── chatbot_service.py # Chat logic + fallbacks
│   └── quiz_service.py    # Quiz generation + evaluation
├── routes/                # auth, student, admin, api blueprints
├── templates/             # Jinja2 HTML templates
└── static/                # CSS, JS, uploads
```

---

## License

Educational use. Built for engineering college students.
