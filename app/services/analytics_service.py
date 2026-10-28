from datetime import datetime
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from sqlalchemy import func
from app.extensions import db
from app.models import Course, Faculty, FeedbackQuestion, FeedbackSubmission, FeedbackResponse


class AnalyticsService:
    """Statistical analytics service powered by Pandas and NumPy.
    
    Provides deterministic aggregation, distribution calculations, trend analysis,
    and explainable observations for academic feedback evaluation.
    """

    @classmethod
    def get_filtered_responses_dataframe(
        cls,
        course_id: Optional[int] = None,
        faculty_id: Optional[int] = None,
        question_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Fetch raw feedback responses matching filters and return as a clean Pandas DataFrame."""
        query = db.session.query(
            FeedbackResponse.id.label('response_id'),
            FeedbackResponse.submission_id,
            FeedbackResponse.question_id,
            FeedbackResponse.rating,
            FeedbackResponse.comment,
            FeedbackResponse.is_redacted,
            FeedbackSubmission.id.label('sub_id'),
            FeedbackSubmission.course_id,
            FeedbackSubmission.submitted_at,
            Course.course_code,
            Course.course_name,
            Course.department.label('course_department'),
            Course.faculty_id,
            Faculty.faculty_name,
            FeedbackQuestion.question_text,
            FeedbackQuestion.category.label('question_category'),
            FeedbackQuestion.question_type
        ).join(
            FeedbackSubmission, FeedbackResponse.submission_id == FeedbackSubmission.id
        ).join(
            Course, FeedbackSubmission.course_id == Course.id
        ).outerjoin(
            Faculty, Course.faculty_id == Faculty.id
        ).join(
            FeedbackQuestion, FeedbackResponse.question_id == FeedbackQuestion.id
        )

        if course_id:
            query = query.filter(FeedbackSubmission.course_id == course_id)
        if faculty_id:
            query = query.filter(Course.faculty_id == faculty_id)
        if question_id:
            query = query.filter(FeedbackResponse.question_id == question_id)
        if start_date:
            query = query.filter(FeedbackSubmission.submitted_at >= start_date)
        if end_date:
            query = query.filter(FeedbackSubmission.submitted_at <= end_date)

        rows = query.all()
        if not rows:
            return pd.DataFrame(columns=[
                'response_id', 'submission_id', 'question_id', 'rating', 'comment',
                'is_redacted', 'sub_id', 'course_id', 'submitted_at', 'course_code',
                'course_name', 'course_department', 'faculty_id', 'faculty_name',
                'question_text', 'question_category', 'question_type'
            ])

        data = [r._asdict() for r in rows]
        df = pd.DataFrame(data)
        
        # Ensure correct data types
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        df['submitted_at'] = pd.to_datetime(df['submitted_at'])
        return df

    @classmethod
    def calculate_numeric_summary(cls, series: Optional[pd.Series]) -> Dict[str, Any]:
        """Compute statistical summary for a numeric rating series.
        
        Strictly excludes NaN values. Returns nulls when no valid ratings exist.
        """
        if series is None or series.empty:
            return {
                'count': 0,
                'mean': None,
                'median': None,
                'std_dev': None,
                'min': None,
                'max': None
            }

        valid_ratings = series.dropna()
        count = int(len(valid_ratings))

        if count == 0:
            return {
                'count': 0,
                'mean': None,
                'median': None,
                'std_dev': None,
                'min': None,
                'max': None
            }

        mean_val = float(valid_ratings.mean())
        median_val = float(valid_ratings.median())
        min_val = int(valid_ratings.min())
        max_val = int(valid_ratings.max())
        std_val = float(valid_ratings.std(ddof=1)) if count > 1 else 0.0

        return {
            'count': count,
            'mean': round(mean_val, 2),
            'median': round(median_val, 2),
            'std_dev': round(std_val, 2),
            'min': min_val,
            'max': max_val
        }

    @classmethod
    def calculate_rating_distribution(cls, series: Optional[pd.Series]) -> Dict[str, Any]:
        """Compute count and percentage distribution for discrete ratings 1 through 5."""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        percentages = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
        labels = {
            1: '1 - Poor',
            2: '2 - Below Average',
            3: '3 - Average',
            4: '4 - Good',
            5: '5 - Excellent'
        }

        if series is None or series.empty:
            return {
                'total_valid': 0,
                'counts': distribution,
                'percentages': percentages,
                'labels': labels
            }

        valid_ratings = series.dropna()
        total_valid = len(valid_ratings)

        if total_valid > 0:
            counts = valid_ratings.value_counts()
            for score in range(1, 6):
                count_score = int(counts.get(score, 0))
                distribution[score] = count_score
                percentages[score] = round((count_score / total_valid) * 100.0, 1)

        return {
            'total_valid': total_valid,
            'counts': distribution,
            'percentages': percentages,
            'labels': labels
        }

    @classmethod
    def get_dashboard_kpis(
        cls,
        course_id: Optional[int] = None,
        faculty_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Calculate high-level Key Performance Indicators (KPIs) based on real database records."""
        # 1. Total active courses
        total_active_courses = Course.query.filter_by(is_active=True).count()

        # 2. Submissions query
        sub_query = db.session.query(FeedbackSubmission.id, FeedbackSubmission.course_id)
        if course_id:
            sub_query = sub_query.filter(FeedbackSubmission.course_id == course_id)
        if start_date:
            sub_query = sub_query.filter(FeedbackSubmission.submitted_at >= start_date)
        if end_date:
            sub_query = sub_query.filter(FeedbackSubmission.submitted_at <= end_date)

        submissions = sub_query.all()
        total_submissions = len(submissions)
        courses_with_feedback = len(set(s.course_id for s in submissions))

        # 3. Overall average rating from DataFrame
        df = cls.get_filtered_responses_dataframe(
            course_id=course_id,
            faculty_id=faculty_id,
            start_date=start_date,
            end_date=end_date
        )

        overall_stats = cls.calculate_numeric_summary(df['rating'] if not df.empty else pd.Series(dtype=float))

        return {
            'total_submissions': total_submissions,
            'overall_average': overall_stats['mean'],
            'total_active_courses': total_active_courses,
            'courses_with_feedback': courses_with_feedback,
            'valid_ratings_count': overall_stats['count']
        }

    @classmethod
    def get_course_analytics(
        cls,
        course_id: Optional[int] = None,
        faculty_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Compute course-level averages, response counts, and distributions."""
        df = cls.get_filtered_responses_dataframe(
            course_id=course_id,
            faculty_id=faculty_id,
            start_date=start_date,
            end_date=end_date
        )

        courses_query = Course.query
        if course_id:
            courses_query = courses_query.filter_by(id=course_id)
        if faculty_id:
            courses_query = courses_query.filter_by(faculty_id=faculty_id)

        all_courses = courses_query.all()
        results = []

        for c in all_courses:
            if not df.empty:
                c_df = df[df['course_id'] == c.id]
            else:
                c_df = pd.DataFrame()

            if not c_df.empty:
                summary = cls.calculate_numeric_summary(c_df['rating'])
                distribution = cls.calculate_rating_distribution(c_df['rating'])
                submission_count = int(c_df['submission_id'].nunique())
            else:
                summary = {
                    'count': 0, 'mean': None, 'median': None,
                    'std_dev': None, 'min': None, 'max': None
                }
                distribution = cls.calculate_rating_distribution(pd.Series(dtype=float))
                submission_count = 0

            faculty_name = c.faculty.faculty_name if c.faculty else 'Not Assigned'
            results.append({
                'course_id': c.id,
                'course_code': c.course_code,
                'course_name': c.course_name,
                'department': c.department,
                'faculty_name': faculty_name,
                'is_active': c.is_active,
                'submission_count': submission_count,
                'valid_responses': summary['count'],
                'mean_rating': summary['mean'],
                'median_rating': summary['median'],
                'std_dev': summary['std_dev'],
                'distribution': distribution['counts'],
                'percentages': distribution['percentages'],
                'is_reliable': summary['count'] >= 5
            })

        # Sort courses with ratings descending, courses with no ratings at bottom
        results.sort(
            key=lambda x: (x['mean_rating'] is not None, x['mean_rating'] or 0, x['valid_responses']),
            reverse=True
        )
        return results

    @classmethod
    def get_question_analytics(
        cls,
        course_id: Optional[int] = None,
        faculty_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Compute question-level averages and response counts across courses."""
        df = cls.get_filtered_responses_dataframe(
            course_id=course_id,
            faculty_id=faculty_id,
            start_date=start_date,
            end_date=end_date
        )

        all_questions = FeedbackQuestion.query.order_by(FeedbackQuestion.display_order).all()
        results = []

        for q in all_questions:
            if not df.empty:
                q_df = df[df['question_id'] == q.id]
            else:
                q_df = pd.DataFrame()

            if not q_df.empty and q.question_type == 'rating':
                summary = cls.calculate_numeric_summary(q_df['rating'])
                distribution = cls.calculate_rating_distribution(q_df['rating'])
            else:
                summary = {
                    'count': 0 if q_df.empty else len(q_df),
                    'mean': None, 'median': None, 'std_dev': None, 'min': None, 'max': None
                }
                distribution = cls.calculate_rating_distribution(pd.Series(dtype=float))

            results.append({
                'question_id': q.id,
                'question_text': q.question_text,
                'category': q.category,
                'question_type': q.question_type,
                'is_required': q.is_required,
                'is_active': q.is_active,
                'valid_responses': summary['count'],
                'mean_rating': summary['mean'],
                'median_rating': summary['median'],
                'distribution': distribution['counts'],
                'percentages': distribution['percentages']
            })

        return results

    @classmethod
    def get_submission_trends(
        cls,
        course_id: Optional[int] = None,
        faculty_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = 'day'
    ) -> Dict[str, Any]:
        """Aggregate submissions over chronological intervals (day/week/month)."""
        df = cls.get_filtered_responses_dataframe(
            course_id=course_id,
            faculty_id=faculty_id,
            start_date=start_date,
            end_date=end_date
        )

        if df.empty:
            return {'labels': [], 'counts': [], 'averages': []}

        # Deduplicate to submission level
        sub_df = df[['submission_id', 'submitted_at']].drop_duplicates()
        sub_df['date'] = pd.to_datetime(sub_df['submitted_at']).dt.date

        # Group submissions by date
        grouped = sub_df.groupby('date').size().reset_index(name='submission_count')
        grouped = grouped.sort_values('date')

        # Compute average rating per date
        rating_df = df.dropna(subset=['rating']).copy()
        rating_df['date'] = pd.to_datetime(rating_df['submitted_at']).dt.date
        rating_grouped = rating_df.groupby('date')['rating'].mean().reset_index(name='avg_rating')

        merged = pd.merge(grouped, rating_grouped, on='date', how='left')
        merged = merged.sort_values('date')

        labels = [d.strftime('%Y-%m-%d') for d in merged['date']]
        counts = [int(c) for c in merged['submission_count']]
        averages = [round(float(a), 2) if not pd.isna(a) else None for a in merged['avg_rating']]

        return {
            'labels': labels,
            'counts': counts,
            'averages': averages
        }

    @classmethod
    def generate_deterministic_insights(
        cls,
        course_analytics: List[Dict[str, Any]],
        question_analytics: List[Dict[str, Any]],
        overall_distribution: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate deterministic, explainable observations based on calculated statistics.
        
        Strictly rule-based: no AI hallucinations or manufactured trends.
        """
        insights = []

        # 1. Sufficient responses courses filter (>= 3 responses for consideration)
        rated_courses = [c for c in course_analytics if c['mean_rating'] is not None and c['valid_responses'] >= 3]

        if rated_courses:
            top_course = max(rated_courses, key=lambda x: x['mean_rating'])
            insights.append({
                'type': 'positive',
                'title': 'Highest-Rated Course',
                'description': f"{top_course['course_code']} ({top_course['course_name']}) holds the highest average rating at {top_course['mean_rating']:.2f}/5.00 across {top_course['valid_responses']} valid evaluation points."
            })

            lowest_course = min(rated_courses, key=lambda x: x['mean_rating'])
            if lowest_course['course_id'] != top_course['course_id']:
                insights.append({
                    'type': 'warning',
                    'title': 'Course Requiring Review',
                    'description': f"{lowest_course['course_code']} recorded the lowest average rating at {lowest_course['mean_rating']:.2f}/5.00 ({lowest_course['valid_responses']} evaluations). Recommended for curriculum and instructional support review."
                })
        else:
            insights.append({
                'type': 'info',
                'title': 'Sample Size Notice',
                'description': 'Insufficient evaluations have been recorded to benchmark course averages reliably (minimum 3 responses required).'
            })

        # 2. Most frequent rating category (mode)
        counts = overall_distribution.get('counts', {})
        if sum(counts.values()) > 0:
            mode_rating = max(counts.items(), key=lambda kv: kv[1])[0]
            mode_count = counts[mode_rating]
            mode_pct = overall_distribution['percentages'].get(mode_rating, 0.0)
            rating_label = overall_distribution['labels'].get(mode_rating, f"Rating {mode_rating}")
            insights.append({
                'type': 'neutral',
                'title': 'Predominant Rating Score',
                'description': f"Rating '{rating_label}' is the most frequently submitted evaluation, representing {mode_pct}% ({mode_count} responses) of all numeric feedback."
            })

        # 3. Question strengths and development areas
        rating_questions = [q for q in question_analytics if q['mean_rating'] is not None and q['valid_responses'] >= 3]
        if rating_questions:
            top_q = max(rating_questions, key=lambda x: x['mean_rating'])
            insights.append({
                'type': 'positive',
                'title': 'Top Scoring Feedback Area',
                'description': f"Category '{top_q['category']}' achieved the strongest feedback with '{top_q['question_text']}' averaging {top_q['mean_rating']:.2f}/5.00."
            })

            low_q = min(rating_questions, key=lambda x: x['mean_rating'])
            if low_q['question_id'] != top_q['question_id']:
                insights.append({
                    'type': 'warning',
                    'title': 'Priority Development Opportunity',
                    'description': f"Area for improvement: '{low_q['question_text']}' in category '{low_q['category']}' averaged {low_q['mean_rating']:.2f}/5.00 across student responses."
                })

        # 4. Low sample size alert
        low_sample_courses = [c for c in course_analytics if 0 < c['valid_responses'] < 5]
        if low_sample_courses:
            code_list = ", ".join([c['course_code'] for c in low_sample_courses[:3]])
            insights.append({
                'type': 'info',
                'title': 'Statistical Reliability Note',
                'description': f"Courses including {code_list} have fewer than 5 feedback responses. Differences in average scores should be interpreted with caution."
            })

        return insights
