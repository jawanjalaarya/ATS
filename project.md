# Build a Professional AI-Powered Resume Screening & Applicant Tracking System

You are a senior full-stack software engineer, AI/ML engineer, UI/UX designer, database architect, and DevOps engineer.

Build a **production-style, professional Resume Screening and Applicant Tracking System (ATS)** for a company's HR/recruitment team.

The application must be a complete **full-stack web application**, not a prototype or notebook. It should have a polished enterprise-style UI, functional backend APIs, SQLite database integration, resume parsing, AI-based candidate-job matching, ranking, filtering, analytics, and HR workflow management.

The system should be modular, maintainable, secure, responsive, and easy to run locally.

---

# 1. PROJECT OBJECTIVE

Create an HR platform where recruiters can:

1. Create and manage job openings.
2. Define job descriptions and recruitment requirements.
3. Upload one or multiple candidate resumes.
4. Automatically parse resumes.
5. Extract structured candidate information.
6. Compare candidates against a selected job.
7. Generate an explainable match score.
8. Rank candidates automatically.
9. Filter and search candidates.
10. View detailed candidate profiles.
11. Shortlist/reject candidates.
12. Compare multiple candidates.
13. Schedule and manage interviews.
14. Generate interview questions based on the job and candidate.
15. Visualize recruitment analytics.
16. Export candidate and recruitment reports.
17. Maintain secure HR user accounts and audit logs.

The system should feel like a **real internal HR recruitment platform**, not a college demo.

---

# 2. RECOMMENDED TECH STACK

Use the following stack unless there is a strong technical reason to change something.

## Frontend

* React
* Vite
* TypeScript
* Tailwind CSS
* React Router
* Recharts
* Axios
* Lucide React icons
* React Hook Form
* Zod for validation

## Backend

* Python
* FastAPI
* SQLAlchemy ORM
* Pydantic
* JWT authentication
* Passlib/bcrypt or an appropriate secure password hashing library

## Database

* SQLite
* SQLAlchemy ORM
* Alembic migrations

The application should be structured so SQLite can later be replaced with PostgreSQL without major architectural changes.

## AI / NLP

Use Python-based NLP/ML libraries.

Recommended:

* spaCy
* scikit-learn
* sentence-transformers
* PyMuPDF / fitz for PDF extraction
* python-docx for DOCX extraction
* pandas
* NumPy

Use lightweight models that can run locally where possible.

Do NOT require paid APIs.

If an LLM integration is implemented, make it optional and configurable through environment variables.

---

# 3. APPLICATION ARCHITECTURE

Use a clean architecture:

```text
Frontend
React + TypeScript + Tailwind
        |
        | REST API
        ↓
Backend
FastAPI
        |
        ├── Authentication
        ├── Job Management
        ├── Candidate Management
        ├── Resume Processing
        ├── Screening Engine
        ├── Interview Management
        ├── Analytics
        └── Reports
        |
        ├── SQLite
        |
        └── AI/NLP Engine
```

Separate frontend and backend into:

```text
/frontend
/backend
```

---

# 4. USER ROLES

Implement role-based authentication.

## Admin

Admin can:

* Manage HR users
* View system-wide analytics
* Manage jobs
* Manage candidates
* View audit logs
* Configure system settings

## HR / Recruiter

HR users can:

* Create jobs
* Upload resumes
* Screen candidates
* View candidate profiles
* Shortlist/reject candidates
* Add notes
* Schedule interviews
* View analytics
* Export reports

---

# 5. AUTHENTICATION

Implement:

* Login
* Logout
* Registration if appropriate
* JWT authentication
* Password hashing
* Protected routes
* Role-based authorization
* Session/token handling
* Unauthorized page
* Automatic redirect to login

Never store plain-text passwords.

Create a default development admin account through a seed script rather than hard-coding credentials into the frontend.

---

# 6. MAIN FRONTEND PAGES

Create the following pages.

## Authentication

```text
/login
```

Professional login page with:

* Company/application logo
* Email
* Password
* Remember me
* Login button
* Error handling

---

## Dashboard

```text
/dashboard
```

Display:

### KPI cards

* Total Jobs
* Active Jobs
* Total Candidates
* Candidates Screened
* Shortlisted Candidates
* Interviews
* Selected Candidates

### Charts

* Recruitment funnel
* Candidate score distribution
* Applications over time
* Most common skills
* Candidates by experience
* Candidates by job

### Recent activity

Examples:

```text
New resume uploaded
Candidate shortlisted
Interview scheduled
Job created
Candidate rejected
```

---

# 7. JOB MANAGEMENT

Create:

```text
/jobs
/jobs/create
/jobs/:id
/jobs/:id/edit
```

HR should be able to create a job containing:

* Job title
* Department
* Job description
* Location
* Work mode

  * Remote
  * Hybrid
  * On-site
* Employment type

  * Full-time
  * Part-time
  * Contract
  * Internship
* Minimum experience
* Maximum experience
* Required education
* Required skills
* Preferred skills
* Certifications
* Salary range
* Job status

Statuses:

```text
Draft
Active
Paused
Closed
```

---

# 8. REQUIREMENT WEIGHTS

Allow HR to configure screening weights.

Example:

```text
Skills              40%
Experience          25%
Education           10%
Projects            10%
Certifications      10%
Semantic similarity 5%
```

The weights must be configurable per job.

Validate that the total equals 100%.

Do not hard-code scoring weights.

---

# 9. RESUME UPLOAD

Create a dedicated resume upload interface.

Support:

* PDF
* DOCX

Allow:

* Single upload
* Multiple resume upload

Show upload progress.

Validate:

* File extension
* MIME type
* File size
* Empty/corrupted files

Store uploaded files securely.

Do not expose arbitrary filesystem paths to the frontend.

---

# 10. RESUME PARSING

Build an automated resume processing pipeline:

```text
Resume
 ↓
File validation
 ↓
Text extraction
 ↓
Text cleaning
 ↓
Section detection
 ↓
Information extraction
 ↓
Skill extraction
 ↓
Experience extraction
 ↓
Education extraction
 ↓
Project extraction
 ↓
Certification extraction
 ↓
Candidate profile
```

Extract:

* Full name
* Email
* Phone
* Location
* LinkedIn
* GitHub
* Portfolio
* Skills
* Education
* Experience
* Projects
* Certifications
* Achievements

Create reusable parsing services.

The parser should gracefully handle resumes with different layouts.

---

# 11. CANDIDATE MANAGEMENT

Create:

```text
/candidates
/candidates/:id
```

Candidate listing should contain:

* Name
* Job applied for
* Match score
* Experience
* Education
* Skills
* Status
* Application date

Allow:

* Search
* Sorting
* Filtering
* Pagination
* Shortlisting
* Rejection
* Status changes

Candidate statuses:

```text
Applied
Screening
Shortlisted
Interview
Selected
Rejected
```

---

# 12. AI SCREENING ENGINE

This is the core feature.

Implement a screening engine that compares:

```text
Job Requirements
        +
Job Description
        +
Candidate Resume
        ↓
Screening Engine
        ↓
Match Score
        +
Detailed Explanation
```

Calculate separate scores for:

```text
Skills Match
Experience Match
Education Match
Projects Match
Certification Match
Semantic Similarity
```

Generate an overall weighted score.

Example:

```text
Overall Match: 87%

Skills:          92%
Experience:      85%
Education:       100%
Projects:        80%
Certifications:  75%
Semantic Match:  88%
```

---

# 13. AI / NLP MATCHING

Implement at least two matching techniques.

## Technique 1 — Explicit skill matching

Compare required/preferred skills against extracted candidate skills.

Handle variations such as:

```text
Machine Learning
machine-learning
ML
Machine Learning Engineer
```

where appropriate.

Use a normalized skill vocabulary.

## Technique 2 — Semantic similarity

Use sentence-transformers or a similar local embedding model.

Compare:

```text
Job Description
        ↕
Candidate Resume
```

using cosine similarity.

Combine semantic similarity with explicit requirement matching.

---

# 14. EXPLAINABLE AI

Do not only display:

```text
Score = 87%
```

Show WHY.

Example:

```text
WHY THIS CANDIDATE MATCHES

✓ Python
✓ SQL
✓ Machine Learning
✓ TensorFlow
✓ 3 years relevant experience
✓ Bachelor's degree

MISSING REQUIREMENTS

⚠ Docker
⚠ AWS certification

STRENGTHS

Strong machine learning experience
Relevant project experience
Meets education requirement
```

Create an explainability component on the candidate profile.

The system should clearly distinguish:

* Required requirements
* Preferred requirements
* Missing requirements
* Matching requirements

---

# 15. CANDIDATE RANKING

For each job, automatically rank applicants:

```text
1. Candidate A     94%
2. Candidate B     91%
3. Candidate C     87%
4. Candidate D     82%
5. Candidate E     76%
```

Allow sorting by:

* Match score
* Experience
* Application date
* Candidate name

---

# 16. CANDIDATE COMPARISON

Allow HR to select 2–4 candidates.

Create a comparison page.

Example:

```text
                  Candidate A   Candidate B   Candidate C

Match Score           94%           88%           82%
Experience            4 yrs         3 yrs         2 yrs
Python                 ✓             ✓             ✓
SQL                    ✓             ✓             ✓
AWS                    ✓             ✗             ✓
Docker                 ✓             ✓             ✗
TensorFlow              ✓             ✓             ✓
```

Highlight strengths and missing requirements.

---

# 17. ANONYMOUS SCREENING

Implement an optional anonymous screening mode.

When enabled, hide potentially biasing information from the initial screening view:

* Photograph
* Gender
* Personal demographic information
* Other irrelevant personal information

Keep job-relevant information visible:

* Skills
* Experience
* Education
* Projects
* Certifications

Add a setting to enable/disable anonymous screening.

---

# 18. INTERVIEW MANAGEMENT

Create:

```text
/interviews
/interviews/create
```

Allow HR to:

* Schedule interviews
* Select candidate
* Select interviewer
* Select date/time
* Select interview type
* Add meeting link
* Add notes
* Add feedback

Interview statuses:

```text
Scheduled
Completed
Cancelled
Rescheduled
```

---

# 19. AI INTERVIEW QUESTION GENERATOR

Add a feature:

```text
Generate Interview Questions
```

Generate questions based on:

* Job description
* Required skills
* Candidate resume
* Candidate projects
* Candidate experience

Categories:

```text
Technical
Behavioral
Project-based
Problem-solving
Role-specific
```

Example:

```text
Technical:
Explain how you implemented the CNN in your project.

Project:
Why did you choose TensorFlow?

Problem Solving:
How would you handle an imbalanced dataset?
```

Allow HR to save generated questions to the interview.

---

# 20. HR NOTES

Allow HR to add private notes to candidates.

Example:

```text
Candidate Notes

"Strong Python knowledge.
Good ML project experience.
Consider for technical round."
```

Notes should contain:

* User
* Candidate
* Timestamp
* Content

---

# 21. DASHBOARD VISUALIZATION

Use Recharts.

Create professional charts for:

### Recruitment funnel

```text
Applied
 ↓
Screened
 ↓
Shortlisted
 ↓
Interview
 ↓
Selected
```

### Skill distribution

Show most frequently found candidate skills.

### Score distribution

Show candidates grouped by match score.

### Applications over time

Line chart.

### Candidate experience

Distribution of experience levels.

### Job performance

Show:

* Applicants
* Qualified candidates
* Shortlisted
* Interviews
* Selected

All charts must use real database data.

Do not use fake static charts after the backend is implemented.

---

# 22. SEARCH & FILTERING

Create advanced candidate filters:

* Job
* Match score
* Experience
* Education
* Skills
* Location
* Status
* Application date

Example:

```text
Match Score > 80%
Experience > 2 years
Skills: Python, SQL
Status: Shortlisted
```

Filters should work through backend API queries rather than filtering only the currently loaded frontend records.

---

# 23. DATABASE DESIGN

Use SQLAlchemy models for:

```text
users
jobs
job_requirements
candidates
skills
candidate_skills
applications
screening_results
interviews
interview_questions
notes
audit_logs
```

Relationships should be properly defined.

Use:

* Primary keys
* Foreign keys
* Unique constraints
* Indexes
* Timestamps
* Cascade behavior where appropriate

Use Alembic migrations.

---

# 24. SUGGESTED DATABASE STRUCTURE

## users

```text
id
name
email
password_hash
role
created_at
updated_at
```

## jobs

```text
id
title
department
description
location
work_mode
employment_type
min_experience
max_experience
education
salary_min
salary_max
status
created_by
created_at
updated_at
```

## job_requirements

```text
id
job_id
requirement
requirement_type
weight
```

Where requirement_type can be:

```text
required_skill
preferred_skill
education
certification
experience
```

## candidates

```text
id
name
email
phone
location
linkedin
github
portfolio
education
experience_years
resume_path
parsed_resume_text
created_at
updated_at
```

## applications

```text
id
candidate_id
job_id
status
match_score
applied_at
updated_at
```

## screening_results

```text
id
application_id
skills_score
experience_score
education_score
project_score
certification_score
semantic_score
overall_score
matched_requirements
missing_requirements
explanation
created_at
```

## interviews

```text
id
application_id
interviewer_id
scheduled_at
interview_type
meeting_link
status
feedback
created_at
```

## notes

```text
id
candidate_id
user_id
note
created_at
updated_at
```

## audit_logs

```text
id
user_id
action
entity_type
entity_id
timestamp
metadata
```

---

# 25. REST API

Create well-structured REST endpoints.

Examples:

```text
POST   /api/auth/login
POST   /api/auth/register
GET    /api/auth/me

GET    /api/jobs
POST   /api/jobs
GET    /api/jobs/{id}
PUT    /api/jobs/{id}
DELETE /api/jobs/{id}

POST   /api/resumes/upload
POST   /api/resumes/bulk-upload

GET    /api/candidates
GET    /api/candidates/{id}
PUT    /api/candidates/{id}

POST   /api/applications
PUT    /api/applications/{id}/status

POST   /api/screening/{application_id}
GET    /api/screening/{application_id}

GET    /api/jobs/{id}/rankings

GET    /api/dashboard/summary
GET    /api/dashboard/analytics

POST   /api/interviews
GET    /api/interviews
PUT    /api/interviews/{id}

POST   /api/interviews/{id}/generate-questions

POST   /api/candidates/{id}/notes
GET    /api/candidates/{id}/notes

GET    /api/reports/candidates
GET    /api/reports/jobs

GET    /api/audit-logs
```

Use proper HTTP status codes and error responses.

---

# 26. FRONTEND DESIGN

The UI must look like a modern enterprise SaaS/HR platform.

Do NOT make it look like a basic student CRUD application.

Use:

* Sidebar navigation
* Top navigation
* Cards
* Tables
* Badges
* Progress bars
* Tabs
* Modals
* Dropdowns
* Toast notifications
* Empty states
* Skeleton loaders
* Confirmation dialogs
* Responsive layouts

Navigation:

```text
Dashboard
Jobs
Candidates
Applications
Interviews
Analytics
Reports
Settings
```

Use a consistent design system.

---

# 27. CANDIDATE TABLE

Create a professional candidate table.

Columns:

```text
Candidate
Job
Match Score
Experience
Skills
Status
Applied
Actions
```

Match scores should visually communicate quality:

```text
90–100  Excellent
80–89   Strong
70–79   Moderate
<70     Low
```

Do not rely only on colors; include text/badges for accessibility.

Actions:

```text
View
Shortlist
Reject
Compare
Schedule Interview
```

---

# 28. RESPONSIVE DESIGN

The application must work on:

* Desktop
* Laptop
* Tablet

Prioritize desktop because this is an HR dashboard, but ensure smaller screens remain usable.

---

# 29. ERROR HANDLING

Implement proper handling for:

* Invalid login
* Invalid file
* Corrupted resume
* Resume parsing failure
* Database failure
* API errors
* Unauthorized access
* Missing candidate
* Missing job
* Invalid screening configuration

Show useful user-facing messages.

Do not expose Python stack traces to users.

---

# 30. SECURITY REQUIREMENTS

Implement:

* Password hashing
* JWT authentication
* Role-based access control
* API authorization
* Input validation
* File validation
* File size limits
* Secure filename handling
* SQL injection protection through ORM
* CORS configuration
* Environment variables
* No secrets committed to Git
* Audit logging

Create:

```text
.env.example
```

Never put API keys or passwords directly into source code.

---

# 31. PRIVACY

Treat resumes as sensitive HR documents.

Implement:

* Secure file access
* Authentication before downloading resumes
* No public resume URLs
* Minimal logging of personal data
* Ability to delete candidate records
* Ability to delete resume files
* Audit trail for sensitive actions

---

# 32. REPORTS

Create report generation for:

### Candidate report

Include:

* Candidate details
* Job
* Match score
* Skills
* Experience
* Education
* Screening breakdown
* Missing requirements
* HR notes

### Job report

Include:

* Total applicants
* Screened
* Shortlisted
* Interviewed
* Selected
* Average match score
* Top skills

Support CSV export and PDF generation if practical.

---

# 33. DEMO DATA

Create a database seed script.

Include:

* Demo admin
* Demo HR user
* 3–5 demo jobs
* 15–30 demo candidates
* Applications
* Screening results
* Interviews
* Skills
* Notes

Do not make the UI dependent on fake hard-coded frontend data.

All demo information must be inserted into SQLite through the seed script.

---

# 34. PROJECT STRUCTURE

Use a clean structure similar to:

```text
resume-screening-system/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   ├── utils/
│   │   └── App.tsx
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── ml/
│   │   ├── utils/
│   │   └── main.py
│   │
│   ├── migrations/
│   ├── tests/
│   ├── requirements.txt
│   └── ...
│
├── uploads/
├── docs/
├── .env.example
├── .gitignore
├── README.md
└── docker-compose.yml
```

Keep business logic out of route handlers.

---

# 35. TESTING

Implement backend tests for:

* Authentication
* Job creation
* Candidate creation
* Resume parsing
* Screening
* Ranking
* Authorization
* Database relationships

Also test important frontend components.

Include at least basic integration tests for the major workflows.

---

# 36. LOGGING

Implement structured backend logging.

Log:

* Authentication events
* Resume processing
* Screening operations
* Errors
* Important HR actions

Never log passwords or unnecessary sensitive resume content.

---

# 37. README

Create a professional README containing:

```text
Project Overview
Features
Architecture
Tech Stack
Folder Structure
Database Schema
AI Screening Pipeline
Installation
Environment Variables
Database Setup
Running Backend
Running Frontend
Demo Credentials
API Documentation
Testing
Screenshots section
Future Improvements
```

Include commands for Windows as well as Linux/macOS where practical.

---

# 38. DEVELOPMENT APPROACH

Do NOT generate the entire application as one giant untested implementation.

Build it incrementally.

Recommended order:

### Phase 1

Project setup

### Phase 2

Database models + migrations

### Phase 3

Authentication

### Phase 4

Job management

### Phase 5

Candidate/resume upload

### Phase 6

Resume parsing

### Phase 7

AI screening engine

### Phase 8

Candidate ranking

### Phase 9

Dashboard

### Phase 10

Candidate comparison

### Phase 11

Interview management

### Phase 12

AI interview questions

### Phase 13

Reports

### Phase 14

Security hardening

##