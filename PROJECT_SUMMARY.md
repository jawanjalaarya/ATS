# ATS Project Summary

## 1. Project Overview

This project is a full-stack Applicant Tracking System (ATS) designed for internal recruitment teams. It supports recruiters and administrators in managing job openings, candidate pipelines, resume intake, AI-assisted screening, candidate comparison, interview coordination, and operational reporting.

The platform is built to look and behave like a professional internal HR system rather than a demo prototype. It combines a secure FastAPI backend, a React + TypeScript frontend, SQLite persistence, document parsing, and explainable ranking logic for candidate-job matching.

The overall goal is to help HR teams:
- manage recruitment workflows end to end,
- reduce manual screening burden,
- keep recruiter decisions traceable and auditable,
- maintain security around candidate data,
- and create a clear operational dashboard for hiring performance.

---

## 2. Business Context and Target Users

### Primary Users
- Recruiters
- Hiring managers
- Administrators
- Internal HR operations teams

### Core Workflows Supported
- Create and manage job postings
- Upload candidate resumes
- Parse resume content into structured profile data
- Match candidate skills against job requirements
- Review screening explanations and scores
- Shortlist or reject candidates
- Compare candidate profiles
- Schedule interviews
- Review audit logs and activity history
- Monitor team and hiring performance via analytics dashboards

### Product Intent
The product is meant to give recruitment teams a calm, dependable operational workspace. The interface prioritizes clarity, maintainability, and trust over flashy UI decoration. It is designed to feel professional and enterprise-ready while still being accessible and easy to use.

---

## 3. Product Goals

The ATS is built around several major goals:

1. Centralize candidate and job data in one system.
2. Lower operational overhead during resume intake and screening.
3. Make hiring decisions evidence-based and explainable.
4. Keep structured candidate and job data consistent.
5. Support role-based access for admin and recruiter users.
6. Maintain a verifiable audit trail for sensitive HR actions.
7. Create a dashboard for recruitment visibility and KPIs.
8. Allow local development with real deployment-ready backend logic and database structure.

---

## 4. High-Level System Architecture

The application is split into two primary layers:

### Frontend
- React + TypeScript
- Vite development environment
- Router-based page navigation
- UI components for dashboard, jobs, candidates, interviews, users, and audit logs
- Axios-based API client with cookie-based authentication

### Backend
- Python + FastAPI
- SQLAlchemy ORM
- SQLite database
- JWT-based authentication with HTTP-only cookies
- Role-based authorization for recruiters and admins
- Separate API routers for auth, jobs, candidates, interviews, settings, users, and audit

### Data Layer
- SQLite database stored locally in the backend data directory
- SQLAlchemy models for users, jobs, applications, candidates, screening results, interviews, settings, and audit logs
- Alembic migrations for schema changes

---

## 5. Project Structure

### Root-level Structure
- README.md – project overview and setup guidance
- PRODUCT.md – product and UX goals
- project.md – original project specification and requirements
- docker-compose.yml – containerized deployment setup
- backend/ – Python API and database services
- frontend/ – React application
- cookies.txt / cookies_test.txt – session-related debug artifacts

### Backend Structure
- app/api/v1/ – API route modules
- app/core/ – config, parser, PDF generation, security, screening logic, database access
- app/models/ – ORM models for system entities
- app/schemas/ – request/response validation models
- app/db/ – seeding and data initialization
- tests/ – automated tests for auth, candidates, jobs, screening, interviews, setup, and analytics
- data/ – local SQLite database and uploaded resume assets

### Frontend Structure
- src/pages/ – main screens for dashboard, jobs, candidates, interviews, audit, users, auth, settings
- src/components/ – reusable UI modules such as candidate upload, job forms, layout, auth
- src/contexts/ – app-level auth context
- src/lib/ – API client and helper utilities
- src/test/ – frontend test setup and tests

---

## 6. Key Functional Modules

### 6.1 Authentication and Authorization
The system includes:
- login/logout endpoints,
- JWT issuance and validation,
- HTTP-only cookie storage,
- protected route gating,
- role checks for recruiter/admin access,
- secure user account management.

There are admin and recruiter roles with different permissions. Admin users can typically access system-wide actions such as user management and audit log review, while recruiter users handle day-to-day hiring operations.

### 6.2 Job Management
The ATS allows recruiters to:
- create jobs,
- update jobs,
- list jobs with filters and pagination,
- view job details,
- maintain job requirements such as skills, salary ranges, experience ranges, department, and active/inactive state,
- validate required business rules such as weight totals and experience ranges.

Job creation and editing enforce validation logic to avoid inconsistent or incomplete job definitions.

### 6.3 Candidate Management
The candidate module supports:
- single-file and batch resume uploads,
- PDF and DOCX file validation,
- file-size and MIME validation,
- secure storage of uploaded resumes,
- candidate record creation and updates,
- duplicate handling via email matching,
- candidate profile parsing from text extraction,
- status tracking such as complete or pending review.

This module is central to the ATS and represents the main intake workflow.

### 6.4 Resume Parsing
Resume parsing is handled in the backend parser layer. It extracts:
- candidate name,
- email,
- phone,
- location,
- linked profiles,
- skills,
- education sections,
- experience sections,
- projects,
- certifications,
- achievements.

It supports PDF extraction using PyMuPDF and DOCX extraction using python-docx. Parsed data is then normalized into structured fields for candidate profiles and screening.

### 6.5 Screening and Ranking
A screening engine evaluates candidate fit against a job using structured logic and heuristics. It can compute:
- overall candidate score,
- skill match score,
- experience alignment,
- education fit,
- project relevance,
- certification alignment,
- semantic or contextual relevance.

The application aims to be explainable rather than black-box: the score is tied to visible factors relevant to hiring decisions. The system can generate score breakdowns and commentary to explain the outcome.

### 6.6 Applications and Candidate Matching
Candidates can be linked to jobs through application records. This allows:
- candidate profiles to be matched against job needs,
- screening results to be tied to a job-specific application,
- ranking and selection workflows to be performed per role.

### 6.7 Interviews
The project includes interview management, including:
- interview scheduling,
- job-candidate linkage,
- interview notes or record handling,
- workflow support for hiring decision stages.

### 6.8 Analytics and Dashboarding
The dashboard provides KPI cards and charts covering:
- total jobs and active jobs,
- candidate counts,
- applications,
- interviews,
- pipeline distribution,
- candidate volume by department,
- recruitment trends and operational stats.

This gives recruiters a quick view of their hiring pipeline health.

### 6.9 Audit and Settings
The project includes:
- immutable or reviewable audit logs,
- system settings management,
- secure configuration for application behavior,
- operational consistency around core platform controls.

---

## 7. Data Model Summary

The system is centered on a small but important set of domain models.

### User
Represents a recruiter/admin account with fields such as:
- email
- password hash
- role
- active status
- creation/update timestamps

### Job
Represents a hiring opening with attributes such as:
- title
- department
- description
- location
- salary range
- required experience
- skills and score weights
- status
- timestamps

### Candidate
Represents a person in the pipeline and stores:
- name
- email
- phone
- location
- profile links
- skills
- education
- experience
- projects
- certifications
- achievements
- resume path
- original filename
- status
- metadata timestamps

### Application
Connects a candidate to a job and enables screening results tied to a specific job opportunity.

### ScreeningResult
Stores computed match scores and their breakdowns, allowing explainable comparison and ranking.

### Interview
Tracks interview scheduling and associated candidate/job records.

### AuditLog
Logs important system actions for accountability and compliance.

### Settings
Stores admin configuration for app behavior and operational preferences.

---

## 8. Resume Upload and Processing Flow

The typical resume intake flow is:

1. Recruiter uploads PDF or DOCX file through the frontend.
2. Frontend sends the file with form data to the backend upload API.
3. Backend validates extension, filesystem size, MIME type, and content signatures.
4. File is saved under a generated secure filename in the resume storage directory.
5. Text is extracted from the PDF or DOCX file.
6. The parser heuristically reads contact info, skills, and sections.
7. A candidate record is created or updated.
8. The parsed result is stored in the database.
9. Candidate status is set to complete or pending review.
10. If linked to a job, the candidate is associated with an application.
11. Screening logic can evaluate the candidate against the job requirements.

---

## 9. Screening Logic and Candidate Evaluation

The screening engine is designed to be practical and explainable. It evaluates multiple dimensions, often including:
- skills match,
- experience match,
- project relevance,
- education relevance,
- certification alignment,
- semantic similarity or contextual relevance.

This produces a structured scoring object where recruiters can understand why a candidate was ranked highly or poorly. This is important because ATS tools need operational trust, not just opaque numerical outputs.

---

## 10. Frontend Experience

The frontend is designed around a clean internal tools aesthetic. The app includes:
- login page,
- dashboard with KPI tiles and charts,
- job pages,
- candidate pages,
- comparison views,
- settings pages,
- user management pages,
- recruitment analytics,
- interview management flows.

The UI is meant to support both quick operational decisions and longer review tasks without overwhelming the user. It balances density and clarity through structured layouts, status badges, and focused workflows.

---

## 11. Security Model

The application includes several security controls:
- JWT-based authentication
- HTTP-only cookies for session storage
- role-based access control
- password hashing with secure algorithms
- protected API routes behind dependency checks
- environment-based configuration for sensitive values
- internal audit logging for actions relevant to HR operations

This is an important feature because resumes and candidate data often contain personal information and need at least baseline governance and access control.

---

## 12. Deployment and Local Development

### Local Development
The repo supports a local development setup:
- Backend with Python virtual environment and FastAPI
- Frontend with Vite + React
- SQLite database in the backend directory
- Environment variables in a backend .env file

### Docker Deployment
The project also includes Docker Compose setup for container-based launches, with:
- backend service,
- frontend service,
- shared volumes for persisted data and uploaded resumes.

This makes the app practical for both local development and containerized deployments.

---

## 13. Testing Strategy

The project includes a test suite covering:
- authentication,
- job creation and validation,
- job listing,
- candidate upload and parsing,
- screening behavior,
- analytics,
- seed and setup cases,
- interview flows,
- audit behavior.

The test structure indicates a focus on ensuring both database logic and API behavior remain stable as features evolve.

---

## 14. Current Project Status

The project is a functional ATS foundation with a strong emphasis on real-world recruitment workflows. It already includes:
- secure authentication and role handling,
- job lifecycle management,
- candidate intake and parsing,
- resume file storage and validation,
- application-to-job linking,
- screening score generation,
- dashboard analytics,
- audit/user management integration,
- containerized local deployment support.

The codebase is structured in a way that clearly separates API logic, models, validation schemas, UI pages, and supporting utilities.

---

## 15. Overall Assessment

This project is a serious full-stack recruitment platform that goes beyond a trivial candidate CRUD app. It is designed to support real HR operations: intake, scoring, selection, review, and visibility into the recruiting pipeline. The architecture exhibits a good balance between product realism, code organization, and functional depth.

Its strongest areas are:
- operational ATS flow,
- structured backend design,
- candidate parsing and evaluation logic,
- role-based security,
- recruiter-centric dashboard and workflow support.

The project is particularly strong as an internal business system because it combines data structure, hiring logic, and decision support in a single operational tool.

---

## 16. Short Executive Summary

The ATS is an internal recruitment management system that helps recruiters manage job openings, candidate submissions, resume parsing, applicant screening, and hiring decisions in a professional, secure, and scalable web application. Built with Python FastAPI and React, it uses SQLite for persistence and includes a structured candidate evaluation engine, role-based access control, audit capabilities, and a modern recruitment dashboard.

It is intended to serve as a realistic HR operations platform rather than a static prototype, with strong emphasis on usability, security, and explainable candidate screening.
