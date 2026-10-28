from app.services.report_service import ReportService, sanitize_csv_cell


def test_csv_formula_injection_sanitization():
    """Verify cells starting with dangerous spreadsheet operators are escaped."""
    assert sanitize_csv_cell("=SUM(A1:B10)") == "'=SUM(A1:B10)"
    assert sanitize_csv_cell("+12345") == "'+12345"
    assert sanitize_csv_cell("-12345") == "'-12345"
    assert sanitize_csv_cell("@username") == "'@username"
    assert sanitize_csv_cell("Standard Text") == "Standard Text"
    assert sanitize_csv_cell(None) == ""


def test_csv_summary_generation(app):
    """Test CSV generation with real analytics metrics."""
    with app.app_context():
        csv_text = ReportService.generate_csv_summary()
        assert "Student Feedback Analysis System - Aggregate Statistical Report" in csv_text
        assert "COURSE EVALUATION SUMMARY" in csv_text
        assert "QUESTION-WISE EVALUATION SUMMARY" in csv_text
        assert "TEST-101" in csv_text


def test_pdf_report_generation(app):
    """Test PDF report generation using ReportLab and embedded Matplotlib chart."""
    with app.app_context():
        pdf_buffer = ReportService.generate_pdf_report()
        assert pdf_buffer is not None
        pdf_bytes = pdf_buffer.getvalue()
        # PDF magic header
        assert pdf_bytes.startswith(b'%PDF-')
        assert len(pdf_bytes) > 1000


def test_reports_endpoints_csv_and_pdf(auth_client):
    """Verify HTTP endpoints for downloading CSV and PDF reports."""
    csv_resp = auth_client.get('/admin/reports/summary.csv')
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.content_type
    assert b"Student Feedback Analysis System" in csv_resp.data

    pdf_resp = auth_client.get('/admin/reports/summary.pdf')
    assert pdf_resp.status_code == 200
    assert "application/pdf" in pdf_resp.content_type
    assert pdf_resp.data.startswith(b'%PDF-')
