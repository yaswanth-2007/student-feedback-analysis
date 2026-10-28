# Student Feedback Analysis System

> **A Production-Minded Academic SaaS Platform for Anonymous Course Evaluations, Statistical Insights, and Institutional Reporting.**

---

## 1. Project Overview

The **Student Feedback Analysis System** is an enterprise-grade academic web application engineered with Python 3, Flask, SQLAlchemy, MySQL, Pandas, NumPy, and Chart.js.

The system addresses the core needs of modern universities and academic institutions:
- **Strict Cryptographic Anonymity:** Collects course and faculty evaluations from students without requiring user accounts or storing student names, roll numbers, institutional emails, IP addresses, or device fingerprints.
- **Configurable Evaluation Questionnaires:** Enables administrators to define rating questions (1 to 5 numeric scale) and optional qualitative comment prompts across academic categories (Instruction, Course Content, Assessment, Support).
- **Deterministic Analytics Engine:** Powered by Pandas and NumPy, calculating exact means, medians, standard deviations, rating distributions, and sample-size reliability flags without black-box AI hallucinations.
- **Interactive Visual Dashboard:** Real-time Chart.js horizontal bar charts for course comparisons, discrete rating distributions (1–5), question-wise ratings, and chronological submission timelines.
- **One-Click Institutional Exports:** Generates RFC-4180 compliant CSV analytical summaries (with formula injection defense) and publication-ready PDF evaluation reports via ReportLab with server-rendered Matplotlib charts.
- **Role-Based Security:** Complete Flask-Login authentication, Werkzeug password hashing, session fixation defense, and CSRF protection.

---

## 2. Technology Stack & Architecture

### Backend
- **Language:** Python 3.10+ (tested on Python 3.14)
- **Web Framework:** Flask 3
- **ORM & Database Abstraction:** SQLAlchemy 2 / Flask-SQLAlchemy 3
- **Database Migrations:** Flask-Migrate / Alembic
- **Authentication & Sessions:** Flask-Login & Werkzeug security
- **Form Security & CSRF:** Flask-WTF
- **Analytics & Computation:** Pandas & NumPy
- **Visuals & Report Generation:** Matplotlib (headless) & ReportLab PDF Engine

### Database
- **Primary Persistent Engine:** MySQL 8+ (via `pymysql` driver and connection pooling)
- **Fallback / Testing Engine:** SQLite 3 (supported automatically for isolated unit test suites and offline local development)

### Frontend
- **Templating:** Server-rendered Jinja2 templates
- **Layout & Responsiveness:** Bootstrap 5.3 + custom CSS variables design system
- **Icons:** Bootstrap Icons 1.11
- **Client-Side Charts:** Chart.js 4 (UMD)
- **Typography:** Inter font family

---

## 3. Database Schema & Entity Relationships

```
+------------------+       1:N       +----------------------+
|     Faculty      | <-------------- |        Course        |
+------------------+                 +----------------------+
| id (PK)          |                 | id (PK)              |
| faculty_name     |                 | course_code (UQ, IDX)|
| department       |                 | course_name          |
| is_active        |                 | faculty_id (FK)      |
+------------------+                 | department (IDX)     |
                                     | is_active (IDX)      |
                                     +----------------------+
                                                |
                                                | 1:N
                                                v
                                     +----------------------+
                                     |  FeedbackSubmission  |
                                     +----------------------+
                                     | id (PK)              |
                                     | course_id (FK, IDX)  |
                                     | submitted_at (IDX)   |
                                     | survey_version       |
                                     +----------------------+
                                                |
                                                | 1:N
                                                v
+----------------------+   1:N       +----------------------+
|   FeedbackQuestion   | <---------- |   FeedbackResponse   |
+----------------------+             +----------------------+
| id (PK)              |             | id (PK)              |
| question_text        |             | submission_id (FK)   |
| category (IDX)       |             | question_id (FK)     |
| question_type        |             | rating (1..5, NULL)  |
| is_required          |             | comment (TEXT, NULL) |
| display_order        |             | is_redacted (BOOL)   |
+----------------------+             +----------------------+
```

### Anonymity & Data Integrity Guardrails
1. `FeedbackSubmission` holds **no** foreign key or identifier to any student record, session cookie, or client IP address.
2. A compound uniqueness constraint on `(submission_id, question_id)` guarantees each question is answered at most once per submission envelope.
3. Check constraints enforce `rating IS NULL OR (rating >= 1 AND rating <= 5)`.
4. Multi-answer submissions are committed transactionally: if any question fails validation, the entire submission rolls back.

---

## 4. Local Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Git
- MySQL Server 8.0+ (optional for local testing; SQLite fallback is available)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd student-feedback-analysis
```

### Step 2: Set Up Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env` and adjust the variables:
```bash
cp .env.example .env
```

Example `.env` configuration:
```env
FLASK_APP=run.py
FLASK_ENV=development
DEBUG=True
SECRET_KEY=generate-a-strong-random-key-here-minimum-32-chars

# Primary MySQL Database:
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/student_feedback_db

# Or use local SQLite if MySQL is not running on your workstation:
# DATABASE_URL=sqlite:///instance/feedback_app.db

# Enable synthetic demonstration notice
SEED_DEMO_DATA=true
```

### Step 5: MySQL Database Setup
If using MySQL, create the database in the MySQL console:
```sql
CREATE DATABASE student_feedback_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 5. Database Initialization & Seed Data

### Bootstrap Administrator Account
Run the CLI script to create your first administrative user:
```bash
python scripts/create_admin.py --email admin@university.edu --password "AdminSecure2026!" --name "Academic Dean"
```

### Populate Synthetic Demonstration Data
Load realistic sample courses (7 courses), questions (6 questions across instruction, content, support), and 100+ distributed ratings spanning the past 45 days:
```bash
python scripts/seed_data.py --reset
```

Default seeded credentials:
- **Email:** `admin@university.edu`
- **Password:** `AdminSecure2026!`

---

## 6. Running the Application

Start the Flask development server:
```bash
python run.py
```
The application will be accessible at:
- **Public Portal & Landing Page:** `http://127.0.0.1:5000/`
- **Student Course Evaluation Form:** `http://127.0.0.1:5000/feedback`
- **Administrator Login:** `http://127.0.0.1:5000/auth/login`
- **Analytics Dashboard:** `http://127.0.0.1:5000/admin/dashboard`
- **Reports & PDF / CSV Exports:** `http://127.0.0.1:5000/admin/reports/`

---

## 7. Running Automated Tests

Run the complete test suite with pytest:
```bash
pytest tests -v
```

The test suite covers:
- **Authentication:** Login, invalid credentials, unauthorized URL redirects, logout session clearance.
- **Feedback Service:** Valid submissions, 1-5 rating constraints, mandatory field enforcement, inactive course rejection, transactional rollback.
- **Analytics Engine:** Mean, median, standard deviation, rating distributions, zero-division prevention, empty dataset handling.
- **Course & Question Management:** Authorized CRUD operations, duplicate code constraints, historical data preservation.
- **Reports Service:** Safe RFC CSV escaping (formula injection defense), ReportLab PDF rendering, embedded Matplotlib charts.

---

## 8. Application Features Guide

### 1. Student Evaluation Portal
- Distraction-free interface optimized for mobile and desktop.
- Interactive 1 to 5 rating cards with clear labels:
  - `1 — Poor`
  - `2 — Below Average`
  - `3 — Average`
  - `4 — Good`
  - `5 — Excellent`
- Live progress bar tracking completion.
- Accidental double-submission prevention through button state locking.

### 2. Administrator Analytics Dashboard
- 4 High-Level KPI Cards: Total Submissions, Overall Average, Active Courses, Evaluated Courses.
- Date range, Course, and Faculty filter controls.
- Dynamic Chart.js visualizations:
  - Horizontal bar chart of course ratings.
  - Discrete 1–5 distribution bar chart.
  - Daily submission line chart.
  - Question-wise performance comparison.
- Explainable, deterministic observations (identifies top-rated courses, areas requiring review, predominant rating mode, and low-sample size warnings).

### 3. Comment Review & Redaction Workflow
- Protected feedback responses table with pagination and search.
- Allows administrators to redact sensitive or identifying text within written remarks while preserving the numeric score for statistical integrity.

### 4. Official Reports & Exports
- **CSV Summary:** RFC-4180 compliant export with prepended escape characters for formula injection prevention.
- **PDF Report:** High-resolution document with institutional title header, KPI executive summary, embedded Matplotlib distribution graph, course breakdown table, and sample-size interpretation disclaimers.

---

## 9. Production Deployment Considerations

1. **Production WSGI Server:** Run Flask behind Gunicorn or uWSGI (e.g. `gunicorn -w 4 -b 0.0.0.0:8000 run:app`).
2. **Reverse Proxy & SSL:** Terminate TLS/HTTPS using Nginx or Caddy. Enable `SESSION_COOKIE_SECURE = True`.
3. **Environment Security:** Never commit `.env` or hardcoded database passwords to version control.
4. **Connection Pooling:** SQLAlchemy connection pre-ping and recycling are enabled by default in `config.py` to handle MySQL connection timeouts gracefully.

---

## 10. License
Academic & Institutional Open Source License &bull; FeedbackInsight System
