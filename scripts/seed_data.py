import argparse
import sys
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.extensions import db
from app.models import (
    AdminUser, Faculty, Course, FeedbackQuestion, CourseQuestion,
    FeedbackSubmission, FeedbackResponse, ApplicationSetting
)


def seed_database(reset: bool = False):
    """Populate database with realistic demonstration and test data."""
    app = create_app()
    with app.app_context():
        # Create schema if not present
        db.create_all()

        if reset:
            print("Resetting existing demonstration data...")
            FeedbackResponse.query.delete()
            FeedbackSubmission.query.delete()
            CourseQuestion.query.delete()
            Course.query.delete()
            Faculty.query.delete()
            FeedbackQuestion.query.delete()
            db.session.commit()
            print("Existing evaluation data cleared.")

        # 1. Ensure Default Admin User exists
        admin = AdminUser.query.filter_by(email='admin@university.edu').first()
        if not admin:
            admin = AdminUser(
                email='admin@university.edu',
                display_name='Academic Dean & Administrator',
                is_active=True
            )
            admin.set_password('AdminSecure2026!')
            db.session.add(admin)
            print("Created default admin user: admin@university.edu / AdminSecure2026!")

        # 2. Application Settings
        ApplicationSetting.set_value('survey_enabled', 'true', 'Global student survey availability')
        ApplicationSetting.set_value('min_sample_size', '5', 'Minimum threshold for reliable course comparison')

        # 3. Faculty Members
        faculty_data = [
            ("Dr. Alan Turing", "Computer Science"),
            ("Dr. Ada Lovelace", "Software Engineering"),
            ("Dr. Claude Shannon", "Information Science"),
            ("Dr. Grace Hopper", "Computer Systems"),
            ("Dr. John von Neumann", "Data Science"),
            ("Dr. Katherine Johnson", "Mathematics & Computing"),
        ]
        faculty_objs = []
        for name, dept in faculty_data:
            fac = Faculty.query.filter_by(faculty_name=name).first()
            if not fac:
                fac = Faculty(faculty_name=name, department=dept, is_active=True)
                db.session.add(fac)
                db.session.flush()
            faculty_objs.append(fac)

        # 4. Courses (At least 6 courses across departments)
        courses_data = [
            ("CS-101", "Introduction to Computer Science", "Computer Science", faculty_objs[0].id,
             "Fundamental programming concepts, algorithms, and computational problem solving using Python."),
            ("SE-301", "Software Engineering & Architecture", "Software Engineering", faculty_objs[1].id,
             "Software design patterns, agile methodologies, continuous integration, and large-scale system design."),
            ("DS-201", "Data Structures & Algorithms", "Computer Science", faculty_objs[2].id,
             "Analysis of algorithmic efficiency, trees, graphs, heaps, dynamic programming, and complexity."),
            ("CY-401", "Network Security & Cryptography", "Information Science", faculty_objs[3].id,
             "Applied cryptography, zero-trust architectures, protocol analysis, and threat modeling."),
            ("ML-350", "Machine Learning & Statistical Foundations", "Data Science", faculty_objs[4].id,
             "Supervised and unsupervised models, gradient descent, neural networks, and evaluation metrics."),
            ("DB-210", "Database Systems & SQL Optimization", "Software Engineering", faculty_objs[5].id,
             "Relational database design, query planning, indexing strategies, transactions, and normalization."),
            ("AI-420", "Applied Artificial Intelligence", "Computer Science", faculty_objs[0].id,
             "Search algorithms, reinforcement learning, NLP basics, and ethical considerations in AI.")
        ]

        course_objs = []
        for code, name, dept, fac_id, desc in courses_data:
            c = Course.query.filter_by(course_code=code).first()
            if not c:
                c = Course(
                    course_code=code,
                    course_name=name,
                    department=dept,
                    faculty_id=fac_id,
                    description=desc,
                    is_active=True
                )
                db.session.add(c)
                db.session.flush()
            course_objs.append(c)

        # 5. Feedback Questions
        questions_data = [
            ("The instructor clearly explained complex concepts and course expectations.", "Instruction", "rating", True, 1),
            ("Course materials, assignments, and lectures were logically structured.", "Course Content", "rating", True, 2),
            ("Assessments and examinations fairly reflected the topics taught in class.", "Assessment", "rating", True, 3),
            ("The instructor was accessible, approachable, and helpful during office hours.", "Support", "rating", True, 4),
            ("The workload and assignments contributed substantially to my learning.", "Course Content", "rating", True, 5),
            ("What aspects of this course were most effective, and what areas could be improved?", "General", "comment", False, 6),
        ]

        question_objs = []
        for text, cat, qtype, req, order in questions_data:
            q = FeedbackQuestion.query.filter_by(question_text=text).first()
            if not q:
                q = FeedbackQuestion(
                    question_text=text,
                    category=cat,
                    question_type=qtype,
                    is_required=req,
                    display_order=order,
                    is_active=True
                )
                db.session.add(q)
                db.session.flush()
            question_objs.append(q)

        db.session.commit()

        # Check existing submissions count
        existing_sub_count = FeedbackSubmission.query.count()
        if existing_sub_count > 0 and not reset:
            print(f"Database already contains {existing_sub_count} feedback submissions. Skipping generation.")
            return

        # 6. Generate Synthetic Feedback Submissions
        # We simulate realistic variations:
        # - SE-301 and CS-101: high ratings (~4.5 - 5.0)
        # - DS-201 and DB-210: good ratings (~3.8 - 4.2)
        # - CY-401: moderate (~3.2)
        # - AI-420: lower sample size (3-4 responses) to test sample reliability flag!

        course_target_profiles = {
            "CS-101": {'mean_target': 4.6, 'count': 22},
            "SE-301": {'mean_target': 4.7, 'count': 20},
            "DS-201": {'mean_target': 3.9, 'count': 18},
            "DB-210": {'mean_target': 4.1, 'count': 15},
            "ML-350": {'mean_target': 4.3, 'count': 16},
            "CY-401": {'mean_target': 3.1, 'count': 14},
            "AI-420": {'mean_target': 4.0, 'count': 3},  # Intentionally low count (< 5) to test reliability flag
        }

        synthetic_comments_positive = [
            "The lectures were engaging and very well paced. Real-world coding examples helped a lot.",
            "Instructor was always supportive during labs and offered thorough feedback on assignments.",
            "Exceptional clarity on challenging topics. The project work was the highlight of the term.",
            "The structured problem sets prepared us thoroughly for the midterm and final exam.",
            "Clear slides and responsive communication whenever questions arose."
        ]

        synthetic_comments_constructive = [
            "The pace felt a bit rushed towards the end of the semester. More tutorial time would help.",
            "Weekly assignments were heavy, but the learning outcomes were solid.",
            "Would appreciate more practical exercises on concurrency and indexing in class.",
            "Grading turnaround time on assignments could be improved to help study for tests.",
            "Good course overall, though some slides had small typos in the mathematical formulas."
        ]

        now = datetime.now(timezone.utc)
        total_submissions_created = 0

        rating_questions = [q for q in question_objs if q.question_type == 'rating']
        comment_question = next((q for q in question_objs if q.question_type == 'comment'), None)

        for course in course_objs:
            profile = course_target_profiles.get(course.course_code, {'mean_target': 4.0, 'count': 10})
            target = profile['mean_target']
            count = profile['count']

            for i in range(count):
                # Spread submission dates over the last 45 days
                days_ago = random.randint(0, 45)
                hours_ago = random.randint(0, 23)
                minutes_ago = random.randint(0, 59)
                sub_date = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

                submission = FeedbackSubmission(
                    course_id=course.id,
                    submitted_at=sub_date,
                    survey_version=1
                )
                db.session.add(submission)
                db.session.flush()

                # Generate ratings tailored around target
                for rq in rating_questions:
                    # Probabilistic rating generation
                    if target >= 4.5:
                        rating = random.choices([3, 4, 5], weights=[5, 30, 65])[0]
                    elif target >= 4.0:
                        rating = random.choices([2, 3, 4, 5], weights=[5, 20, 50, 25])[0]
                    elif target >= 3.5:
                        rating = random.choices([2, 3, 4, 5], weights=[15, 45, 30, 10])[0]
                    else:
                        rating = random.choices([1, 2, 3, 4], weights=[20, 45, 25, 10])[0]

                    resp = FeedbackResponse(
                        submission_id=submission.id,
                        question_id=rq.id,
                        rating=rating,
                        comment=None,
                        created_at=sub_date
                    )
                    db.session.add(resp)

                # Optional comment on ~35% of submissions
                if comment_question and random.random() < 0.35:
                    if target >= 4.0:
                        comment_text = random.choice(synthetic_comments_positive)
                    else:
                        comment_text = random.choice(synthetic_comments_constructive)

                    comment_resp = FeedbackResponse(
                        submission_id=submission.id,
                        question_id=comment_question.id,
                        rating=None,
                        comment=comment_text,
                        created_at=sub_date
                    )
                    db.session.add(comment_resp)

                total_submissions_created += 1

        db.session.commit()
        print(f"Demonstration data seeded successfully: {len(course_objs)} courses, {len(question_objs)} questions, and {total_submissions_created} realistic feedback submissions across 45 days.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Seed Synthetic Demonstration Data")
    parser.add_argument('--reset', action='store_true', help="Clear existing evaluation records before seeding")
    args = parser.parse_args()

    seed_database(reset=args.reset)
