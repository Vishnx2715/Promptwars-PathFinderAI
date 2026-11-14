# PathForge AI — Career Readiness & Adaptive Learning Platform

PathForge AI is an AI-powered personalized career-readiness platform. It combines adaptive learning roadmaps, evidence-based skill verification, practice labs, mock assessments, AI project evaluation, mentorship, and admin analytics into a single integrated system.

## Architecture

```
pathforge-ai/
├── backend/          FastAPI + SQLAlchemy + SQLite (async)
│   └── app/
│       ├── main.py            App entry, router registration, health check
│       ├── core/              Config, security (JWT/bcrypt), dependencies, rate limiting
│       ├── db/                Base, session, seed (demo users, problems, rubrics)
│       ├── models/            SQLAlchemy models (user, profile, skill, career, assessment,
│       │                      roadmap, mentor, practice, project, analytics)
│       ├── schemas/           Pydantic v2 request/response schemas
│       ├── api/v1/            REST endpoints (auth, profiles, careers, skills, roadmaps,
│       │                      assessments, practice, projects, mentors, doubts, admin,
│       │                      analytics, mentor_chat)
│       ├── services/          Business logic (assessment, practice, code execution,
│       │                      project evaluation, mentor, doubt, admin, analytics, replanning)
│       ├── agents/            OpenAI Structured Outputs agents with deterministic fallbacks
│       └── data/              JSON seed data (skills, careers, resources, questions,
│                              coding problems, project rubrics)
├── frontend/         React + Vite + TypeScript + Tailwind CSS
│   └── src/
│       ├── api/               Axios API modules
│       ├── components/        Layout, CodeEditor (Monaco), TestResultTable, etc.
│       ├── context/           AuthContext (JWT session management)
│       ├── pages/
│       │   ├── student/       Dashboard, PracticeLab, PracticeProblem, MockTests,
│       │   │                  ProjectSubmission, MentorConnect, Doubts, AiMentor
│       │   ├── mentor/        MentorDashboard, MenteeDetail, DoubtQueue, ProjectReviews
│       │   └── admin/         AdminDashboard, UserManagement, MentorManagement,
│       │                      QuestionBank, CodingProblemManagement, Analytics
│       └── types/             TypeScript interfaces
└── README.md
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, TypeScript (strict), Tailwind CSS, Monaco Editor, Recharts, TanStack Query, axios |
| Backend | FastAPI, SQLAlchemy 2.0 (async), SQLite (aiosqlite), Pydantic v2, python-multipart |
| Auth | JWT in HTTP-only cookies, bcrypt password hashing, role-based access control |
| AI | OpenAI API with Structured Outputs — every AI feature has a deterministic fallback |

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # Add your OPENAI_API_KEY (optional — fallbacks work without it)
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The server seeds demo data on first startup. Health check: `GET http://127.0.0.1:8000/health`

### Frontend

```bash
cd frontend
npm install
npm run dev    # Starts Vite dev server on http://localhost:5173
```

The Vite dev proxy forwards `/api` requests to the backend on port 8000.

## Demo Accounts

| Role | Email | Password | Username |
|------|-------|----------|----------|
| Admin | admin@pathforge.ai | admin123 | admin |
| Mentor | sarah.mentor@pathforge.ai | mentor123 | sarah_mentor |
| Mentor | mike.mentor@pathforge.ai | mentor123 | mike_mentor |
| Mentor | priya.mentor@pathforge.ai | mentor123 | priya_mentor |
| Student | alex.student@pathforge.ai | student123 | alex_student |
| Student | jamie.student@pathforge.ai | student123 | jamie_student |
| Student | carol.student@pathforge.ai | student123 | carol_student |
| Student | dave.student@pathforge.ai | student123 | dave_student |
| Student | emma.student@pathforge.ai | student123 | emma_student |

Mentor codes (auto-generated, check via admin panel or mentor dashboard):
- Sarah Chen: PF-MENTOR-XXXXXXXX (check `/mentors/profile` after login)

## Features

### Section 1 (Existing)
- JWT authentication with HTTP-only cookies
- Student profile and self-reported skills
- Career role selection (Full Stack Developer, Data Analyst, Frontend Developer, Backend Developer)
- AI-powered skill-gap analysis with readiness score
- Prerequisite-aware learning roadmap generation
- Diagnostic assessment with scoring
- Adaptive remediation and replanning (lock/unlock modules based on mastery)
- OpenAI Structured Outputs agents with Pydantic validation and deterministic fallbacks

### Section 2 (New)
- **Practice Lab**: Coding problems (JavaScript + Python), Monaco editor, sandboxed JS execution in Web Worker, test-case evaluation, AI code review, submission history, mastery updates
- **Mock Assessments**: Subject-wise tests, diagnostic, career-readiness, mentor-assigned, AI-generated practice tests
- **WeaknessTrainerAgent**: Identifies weak subtopics, builds remediation plans, triggers roadmap replanning
- **Project Evaluation**: Project submission with file upload (validated), background AI evaluation against rubrics, detailed evaluation reports
- **Mentor System**: Unique mentor codes (PF-MENTOR-XXXXXXXX), student connection, mentor dashboard with mentee analytics, risk assessment, feedback, doubt portal
- **Doubt Portal**: Student submits questions → AI drafts answer → mentor reviews/answers → student resolves
- **AI Mentor Chat**: Context-aware chat grounded in learner state (skills, roadmap, assessments, practice, projects)
- **Admin Dashboard**: User management, mentor management, question bank, coding problem management, platform analytics
- **Analytics**: Student (readiness trend, skill mastery, streaks), mentor (mentee stats, response time), admin (skill gaps, role distribution, at-risk learners)
- **Security**: Rate limiting (login, code submission, project submission, mentor chat, mentor code validation), input validation, file type/size validation, path traversal prevention, safe generic error responses

## Deterministic Rules

### Mastery from coding practice
- All tests passed: +5–10 mastery points
- Some tests passed: +1–3 mastery points
- All tests failed: −2–5 mastery points
- Mastery clamped to [0, 100]

### Mastery from assessments
- Below 50%: Module → needs_revision, remediation resources added, dependent modules locked
- 50–74%: Module kept available, dependent modules remain locked
- 75–84%: Module available for completion, mini project recommended
- 85%+: Module completed, dependent modules unlocked if prerequisites met

### Risk assessment (mentor dashboard)
- High: readiness < 40%, OR 2+ skills below 50%, OR no activity 5+ days, OR repeated subtopic failures
- Medium: readiness 40–60%
- Low: readiness > 60%

## API Testing Checklist (curl)

```bash
# Health check
curl http://127.0.0.1:8000/health

# Register
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"testuser","password":"pass123","confirm_password":"pass123"}'

# Login (saves cookie)
curl -c cookies.txt -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"alex.student@pathforge.ai","password":"student123"}'

# Get profile
curl -b cookies.txt http://127.0.0.1:8000/api/v1/profiles/me

# List practice problems
curl -b cookies.txt "http://127.0.0.1:8000/api/v1/practice/problems?language=javascript"

# Get problem detail
curl -b cookies.txt http://127.0.0.1:8000/api/v1/practice/problems/1

# Submit solution
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/v1/practice/problems/1/submit \
  -H "Content-Type: application/json" \
  -d '{"code":"function sumTwoNumbers(a, b) { return a + b; }","language":"javascript","problem_id":1}'

# List assessments
curl -b cookies.txt http://127.0.0.1:8000/api/v1/assessments/

# Start assessment
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/v1/assessments/1/start

# Connect to mentor
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/v1/mentors/connect \
  -H "Content-Type: application/json" \
  -d '{"mentor_code":"PF-MENTOR-AWCV4MVY"}'

# Submit doubt
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/v1/doubts/submit \
  -H "Content-Type: application/json" \
  -d '{"subject":"Closures","question":"How do closures work?"}'

# AI mentor chat
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/v1/mentor-chat/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What should I learn next?"}'

# Submit project (multipart)
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/v1/projects/submit \
  -F "title=My App" -F "project_type=full_stack" -F "description=A full stack app" \
  -F "github_url=https://github.com/me/myapp"

# Admin overview
curl -b cookies_admin.txt http://127.0.0.1:8000/api/v1/admin/overview

# Admin analytics
curl -b cookies_admin.txt http://127.0.0.1:8000/api/v1/analytics/admin
```

## Browser Testing Checklist

1. **Login as admin** → Admin Dashboard shows 5 students, 3 mentors, stats
2. **Login as mentor** → Dashboard shows mentor code, connected students with risk levels
3. **Login as student (Alex)** → Dashboard shows career target, readiness, next action
4. **Practice Lab** → Filter JS problems → Open a problem → Write code in Monaco → Run tests → Submit → See AI review
5. **Assessments** → Start JavaScript assessment → Answer questions → Submit → See score and mastery update
6. **Score below 50%** → Module marked needs_revision, dependent modules locked, remediation added
7. **Mentor Dashboard** → Student shows as "high" risk → View mentee detail → Assign assessment
8. **Projects** → Submit a project → Wait for background evaluation → View report
9. **Doubts** → Submit doubt → See AI draft → Login as mentor → Answer doubt → Back as student → Mark resolved
10. **AI Mentor** → Ask "What should I learn next?" → Get context-aware response
11. **Admin Analytics** → View skill gaps, career role distribution, at-risk learners, mentor performance

## Features Intentionally Excluded

- OAuth / social login / email verification
- Real-time WebSocket chat (doubt portal uses async request/response)
- Video calls
- Payment systems
- Mobile apps
- Full multi-language compiler infrastructure (Python uses deterministic test matching; JS runs in browser Web Worker)
- Microservice architecture (single monolithic FastAPI app)
- Docker/containerization (not required for hackathon demo)

## File Upload Restrictions

- Max file size: 5 MB
- Allowed extensions: .zip, .txt, .md, .py, .js, .jsx, .ts, .tsx, .html, .css, .json
- Files are never executed on the server
- Filenames are sanitized to prevent path traversal

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| Login | 5 attempts / 5 min per IP+user |
| AI mentor chat | 10 messages / 5 min per user |
| Code submission | 5 submissions / min per user |
| Project submission | 3 submissions / hour per user |
| Mentor code validation | 10 attempts / 5 min per IP |

## License

Hackathon project — PathForge AI.
