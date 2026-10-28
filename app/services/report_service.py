import io
import csv
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import matplotlib
matplotlib.use('Agg')  # Headless backend for web server
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from app.services.analytics_service import AnalyticsService


def sanitize_csv_cell(val: Any) -> str:
    """Prevent CSV formula injection by prepending single quote if value begins with dangerous characters."""
    if val is None:
        return ""
    text = str(val).strip()
    if text and text[0] in ('=', '+', '-', '@', '\t', '\r'):
        return f"'{text}"
    return text


class ReportService:
    """Service generating downloadable CSV and PDF reports."""

    @classmethod
    def generate_csv_summary(
        cls,
        course_id: Optional[int] = None,
        faculty_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """Generate safe, RFC-4180 compliant CSV export containing course and question analytics."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header metadata
        gen_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        writer.writerow(["Student Feedback Analysis System - Aggregate Statistical Report"])
        writer.writerow(["Generated At", sanitize_csv_cell(gen_time)])
        writer.writerow(["Course Filter", sanitize_csv_cell(f"Course ID {course_id}" if course_id else "All Courses")])
        writer.writerow(["Faculty Filter", sanitize_csv_cell(f"Faculty ID {faculty_id}" if faculty_id else "All Faculty")])
        writer.writerow(["Start Date", sanitize_csv_cell(start_date.strftime('%Y-%m-%d') if start_date else "Beginning of Records")])
        writer.writerow(["End Date", sanitize_csv_cell(end_date.strftime('%Y-%m-%d') if end_date else "Present")])
        writer.writerow([])

        # KPIs
        kpis = AnalyticsService.get_dashboard_kpis(course_id, faculty_id, start_date, end_date)
        writer.writerow(["--- HIGH-LEVEL KEY PERFORMANCE INDICATORS ---"])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Submissions", kpis['total_submissions']])
        writer.writerow(["Overall Average Rating", kpis['overall_average'] or "N/A"])
        writer.writerow(["Total Active Courses", kpis['total_active_courses']])
        writer.writerow(["Courses With Feedback", kpis['courses_with_feedback']])
        writer.writerow(["Total Valid Ratings Analyzed", kpis['valid_ratings_count']])
        writer.writerow([])

        # Course Summary Table
        courses = AnalyticsService.get_course_analytics(course_id, faculty_id, start_date, end_date)
        writer.writerow(["--- COURSE EVALUATION SUMMARY ---"])
        writer.writerow([
            "Course Code", "Course Name", "Department", "Faculty", "Submissions",
            "Valid Evaluations", "Mean Rating (1-5)", "Median Rating", "Std Dev",
            "Score 1 (Poor)", "Score 2", "Score 3", "Score 4", "Score 5 (Excellent)", "Reliability Flag"
        ])

        if courses:
            for c in courses:
                dist = c['distribution']
                writer.writerow([
                    sanitize_csv_cell(c['course_code']),
                    sanitize_csv_cell(c['course_name']),
                    sanitize_csv_cell(c['department']),
                    sanitize_csv_cell(c['faculty_name']),
                    c['submission_count'],
                    c['valid_responses'],
                    c['mean_rating'] if c['mean_rating'] is not None else "N/A",
                    c['median_rating'] if c['median_rating'] is not None else "N/A",
                    c['std_dev'] if c['std_dev'] is not None else "N/A",
                    dist.get(1, 0),
                    dist.get(2, 0),
                    dist.get(3, 0),
                    dist.get(4, 0),
                    dist.get(5, 0),
                    "Sufficient (>=5)" if c['is_reliable'] else "Low Sample Size (<5)"
                ])
        else:
            writer.writerow(["No courses found matching selected filters."])
        writer.writerow([])

        # Question Summary Table
        questions = AnalyticsService.get_question_analytics(course_id, faculty_id, start_date, end_date)
        writer.writerow(["--- QUESTION-WISE EVALUATION SUMMARY ---"])
        writer.writerow([
            "Question ID", "Question Text", "Category", "Type", "Valid Responses",
            "Mean Rating (1-5)", "Median Rating",
            "Score 1 (Poor)", "Score 2", "Score 3", "Score 4", "Score 5 (Excellent)"
        ])

        if questions:
            for q in questions:
                dist = q['distribution']
                writer.writerow([
                    q['question_id'],
                    sanitize_csv_cell(q['question_text']),
                    sanitize_csv_cell(q['category']),
                    sanitize_csv_cell(q['question_type']),
                    q['valid_responses'],
                    q['mean_rating'] if q['mean_rating'] is not None else "N/A",
                    q['median_rating'] if q['median_rating'] is not None else "N/A",
                    dist.get(1, 0),
                    dist.get(2, 0),
                    dist.get(3, 0),
                    dist.get(4, 0),
                    dist.get(5, 0)
                ])
        else:
            writer.writerow(["No feedback questions found."])

        return output.getvalue()

    @classmethod
    def generate_matplotlib_chart_image(cls, distribution_counts: Dict[int, int]) -> io.BytesIO:
        """Create a server-generated rating distribution chart image using Matplotlib."""
        fig, ax = plt.subplots(figsize=(6.5, 2.8), dpi=150)
        
        categories = ['1 - Poor', '2 - Below Avg', '3 - Average', '4 - Good', '5 - Excellent']
        counts = [distribution_counts.get(i, 0) for i in range(1, 6)]
        colors_list = ['#EF4444', '#F97316', '#FBBF24', '#3B82F6', '#10B981']

        bars = ax.bar(categories, counts, color=colors_list, width=0.55, edgecolor='#E2E8F0', linewidth=1)
        ax.set_ylabel('Response Count', fontsize=9, color='#334155', fontweight='bold')
        ax.set_title('Overall Rating Distribution (1 through 5)', fontsize=11, color='#1E293B', pad=10, fontweight='bold')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#CBD5E1')
        ax.spines['bottom'].set_color('#CBD5E1')
        ax.tick_params(colors='#475569', labelsize=8)
        ax.grid(axis='y', linestyle='--', alpha=0.5, color='#E2E8F0')

        # Add count numbers on top of bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{height}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=8, color='#1E293B', fontweight='bold')

        plt.tight_layout()
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight')
        plt.close(fig)
        img_buffer.seek(0)
        return img_buffer

    @classmethod
    def generate_pdf_report(
        cls,
        course_id: Optional[int] = None,
        faculty_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> io.BytesIO:
        """Generate a complete, professionally formatted PDF report using ReportLab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom Typography Styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#1E293B'),
            fontName='Helvetica-Bold',
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=14
        )
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#4F46E5'),
            fontName='Helvetica-Bold',
            spaceBefore=12,
            spaceAfter=6
        )
        cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#1E293B')
        )
        cell_bold = ParagraphStyle(
            'TableCellBold',
            parent=cell_style,
            fontName='Helvetica-Bold'
        )
        note_style = ParagraphStyle(
            'NoteStyle',
            parent=styles['Normal'],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#475569')
        )

        elements = []

        # 1. Header & Metadata
        elements.append(Paragraph("Student Feedback Analysis System", title_style))
        gen_str = datetime.now(timezone.utc).strftime('%B %d, %Y - %H:%M:%S UTC')
        filter_str = f"Filters: Course: {'All Courses' if not course_id else f'ID {course_id}'} | Faculty: {'All Faculty' if not faculty_id else f'ID {faculty_id}'}"
        elements.append(Paragraph(f"Official Institutional Feedback Evaluation Report &bull; Generated: {gen_str}<br/>{filter_str}", subtitle_style))
        elements.append(Spacer(1, 8))

        # 2. Executive KPI Summary
        kpis = AnalyticsService.get_dashboard_kpis(course_id, faculty_id, start_date, end_date)
        elements.append(Paragraph("Executive Performance Summary", heading_style))
        
        kpi_data = [
            [
                Paragraph("<b>Total Submissions</b>", cell_style),
                Paragraph(str(kpis['total_submissions']), cell_bold),
                Paragraph("<b>Overall Mean Rating</b>", cell_style),
                Paragraph(f"{kpis['overall_average']:.2f} / 5.00" if kpis['overall_average'] else "N/A", cell_bold)
            ],
            [
                Paragraph("<b>Active Courses</b>", cell_style),
                Paragraph(str(kpis['total_active_courses']), cell_bold),
                Paragraph("<b>Evaluated Courses</b>", cell_style),
                Paragraph(str(kpis['courses_with_feedback']), cell_bold)
            ]
        ]
        kpi_table = Table(kpi_data, colWidths=[120, 150, 130, 140])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 12))

        # 3. Matplotlib Distribution Chart
        df = AnalyticsService.get_filtered_responses_dataframe(course_id, faculty_id, start_date=start_date, end_date=end_date)
        dist = AnalyticsService.calculate_rating_distribution(df['rating'] if not df.empty else None)
        chart_buffer = cls.generate_matplotlib_chart_image(dist['counts'])
        elements.append(Image(chart_buffer, width=6.5 * inch, height=2.8 * inch))
        elements.append(Spacer(1, 10))

        # 4. Course Analytics Table
        elements.append(Paragraph("Course-Wise Evaluation Breakdown", heading_style))
        courses = AnalyticsService.get_course_analytics(course_id, faculty_id, start_date, end_date)

        course_table_data = [[
            Paragraph("<b>Code</b>", cell_bold),
            Paragraph("<b>Course Name</b>", cell_bold),
            Paragraph("<b>Faculty</b>", cell_bold),
            Paragraph("<b>Count</b>", cell_bold),
            Paragraph("<b>Mean (1-5)</b>", cell_bold),
            Paragraph("<b>Std Dev</b>", cell_bold),
            Paragraph("<b>Reliability</b>", cell_bold),
        ]]

        if courses:
            for c in courses[:20]:  # Up to top 20 courses
                course_table_data.append([
                    Paragraph(c['course_code'], cell_style),
                    Paragraph(c['course_name'][:28], cell_style),
                    Paragraph(c['faculty_name'][:20], cell_style),
                    Paragraph(str(c['valid_responses']), cell_style),
                    Paragraph(f"{c['mean_rating']:.2f}" if c['mean_rating'] else "N/A", cell_bold),
                    Paragraph(f"{c['std_dev']:.2f}" if c['std_dev'] else "N/A", cell_style),
                    Paragraph("Reliable" if c['is_reliable'] else "Low Sample", cell_style),
                ])
        else:
            course_table_data.append([Paragraph("No course feedback records available.", cell_style)] * 7)

        c_table = Table(course_table_data, colWidths=[55, 175, 110, 45, 55, 45, 55])
        c_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEF2FF')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(c_table)
        elements.append(Spacer(1, 14))

        # 5. Question Analytics Table
        elements.append(Paragraph("Question-Level Performance Breakdown", heading_style))
        questions = AnalyticsService.get_question_analytics(course_id, faculty_id, start_date, end_date)

        q_table_data = [[
            Paragraph("<b>ID</b>", cell_bold),
            Paragraph("<b>Feedback Question Text</b>", cell_bold),
            Paragraph("<b>Category</b>", cell_bold),
            Paragraph("<b>Responses</b>", cell_bold),
            Paragraph("<b>Average (1-5)</b>", cell_bold),
        ]]

        if questions:
            for q in questions:
                q_table_data.append([
                    Paragraph(str(q['question_id']), cell_style),
                    Paragraph(q['question_text'][:55], cell_style),
                    Paragraph(q['category'], cell_style),
                    Paragraph(str(q['valid_responses']), cell_style),
                    Paragraph(f"{q['mean_rating']:.2f}" if q['mean_rating'] else "N/A", cell_bold),
                ])
        else:
            q_table_data.append([Paragraph("No questions recorded.", cell_style)] * 5)

        q_table = Table(q_table_data, colWidths=[30, 275, 100, 65, 70])
        q_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEF2FF')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(q_table)
        elements.append(Spacer(1, 14))

        # 6. Methodological and Privacy Disclaimers
        elements.append(Paragraph("<b>Confidentiality & Interpretation Notes:</b>", heading_style))
        disclaimer = (
            "1. Student evaluations are conducted with strict anonymity. Individual respondent identities and IP addresses are not recorded.<br/>"
            "2. Sample sizes with fewer than 5 valid evaluations are flagged as 'Low Sample' and should be interpreted cautiously.<br/>"
            "3. Rating scores reflect student subjective perceptions on a 1 (Poor) to 5 (Excellent) numeric scale."
        )
        elements.append(Paragraph(disclaimer, note_style))

        # Build document
        doc.build(elements)
        buffer.seek(0)
        return buffer
