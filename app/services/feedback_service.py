from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from app.extensions import db
from app.models import Course, FeedbackQuestion, CourseQuestion, FeedbackSubmission, FeedbackResponse, ApplicationSetting


class FeedbackService:
    """Service managing anonymous student feedback submissions and validation."""

    @classmethod
    def get_course_active_questions(cls, course_id: int):
        """Retrieve active questions assigned to a course, falling back to global active questions."""
        # Check if course has specific assigned questions
        cq_query = CourseQuestion.query.filter_by(
            course_id=course_id,
            is_active=True
        ).order_by(CourseQuestion.display_order)
        
        assigned_cqs = cq_query.all()
        if assigned_cqs:
            question_ids = [cq.question_id for cq in assigned_cqs]
            questions = FeedbackQuestion.query.filter(
                FeedbackQuestion.id.in_(question_ids),
                FeedbackQuestion.is_active.is_(True)
            ).all()
            # Order questions as specified by course question ordering
            order_map = {cq.question_id: cq.display_order for cq in assigned_cqs}
            questions.sort(key=lambda q: order_map.get(q.id, q.display_order))
            return questions

        # Fallback to all global active questions ordered by display_order
        return FeedbackQuestion.query.filter_by(is_active=True).order_by(FeedbackQuestion.display_order).all()

    @classmethod
    def submit_feedback(
        cls,
        course_id: int,
        answers: Dict[int, Dict[str, Any]],
        survey_version: int = 1
    ) -> Tuple[bool, str, Optional[int]]:
        """Validate and commit a complete student feedback submission transactionally.
        
        Parameters:
            course_id: ID of the evaluated course
            answers: Dict of question_id -> {'rating': int or None, 'comment': str or None}
            survey_version: version context for survey format
            
        Returns:
            (success: bool, message: str, submission_id: Optional[int])
        """
        # 1. Verify global survey availability setting
        survey_open = ApplicationSetting.get_value('survey_enabled', 'true').lower() == 'true'
        if not survey_open:
            return False, 'Feedback collection is currently closed by administration.', None

        # 2. Verify course exists and is active
        course = Course.query.filter_by(id=course_id, is_active=True).first()
        if not course:
            return False, 'The selected course does not exist or is currently inactive.', None

        # 3. Retrieve valid active questions
        active_questions = cls.get_course_active_questions(course_id)
        if not active_questions:
            return False, 'There are currently no active feedback questions available for this course.', None

        active_q_map = {q.id: q for q in active_questions}

        # 4. Validate submitted answers against questions
        responses_to_save = []
        for q_id, q in active_q_map.items():
            ans = answers.get(q_id, {})
            raw_rating = ans.get('rating')
            raw_comment = ans.get('comment', '').strip() if ans.get('comment') else None

            # Handle comment length limit
            if raw_comment and len(raw_comment) > 2000:
                return False, f"Comment for question #{q_id} exceeds maximum permitted length of 2,000 characters.", None

            # Rating validation
            parsed_rating = None
            if raw_rating is not None and str(raw_rating).strip() != '':
                try:
                    parsed_rating = int(raw_rating)
                    if parsed_rating < 1 or parsed_rating > 5:
                        return False, f"Rating for question '{q.question_text[:30]}...' must be an integer between 1 and 5.", None
                except (ValueError, TypeError):
                    return False, f"Invalid rating format submitted for question #{q_id}.", None

            # Required field check
            if q.is_required:
                if q.question_type == 'rating' and parsed_rating is None:
                    return False, f"Please provide a rating for the required question: '{q.question_text}'.", None
                if q.question_type == 'comment' and not raw_comment:
                    return False, f"Please provide comments for the required question: '{q.question_text}'.", None

            # If user provided either a rating or a comment, prepare response
            if parsed_rating is not None or raw_comment:
                responses_to_save.append({
                    'question_id': q_id,
                    'rating': parsed_rating,
                    'comment': raw_comment
                })

        if not responses_to_save:
            return False, 'Submission cannot be empty. Please answer the survey questions.', None

        # 5. Transactional commit
        try:
            # Create anonymous submission envelope (NO IP, NO user identity)
            submission = FeedbackSubmission(
                course_id=course_id,
                submitted_at=datetime.now(timezone.utc),
                survey_version=survey_version
            )
            db.session.add(submission)
            db.session.flush()  # Obtain submission.id

            for item in responses_to_save:
                resp = FeedbackResponse(
                    submission_id=submission.id,
                    question_id=item['question_id'],
                    rating=item['rating'],
                    comment=item['comment'],
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(resp)

            db.session.commit()
            return True, 'Your feedback has been submitted successfully and anonymously.', submission.id

        except Exception as e:
            db.session.rollback()
            return False, f"A database error occurred while saving your feedback: {str(e)}", None
