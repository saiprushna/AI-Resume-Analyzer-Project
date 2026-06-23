import pytest

from resume_parser import extract_text


def test_extract_text_from_sample_pdf(sample_pdf_bytes):
    text = extract_text(sample_pdf_bytes, filename="resume.pdf")
    assert "Ravi Kumar" in text
    assert "Python" in text
    assert len(text) > 100


def test_extract_text_from_sample_docx(sample_docx_bytes):
    text = extract_text(sample_docx_bytes, filename="resume.docx")
    assert "Ravi Kumar" in text
    assert "Python" in text
    assert len(text) > 100


def test_extract_text_rejects_empty():
    with pytest.raises(ValueError, match="Empty"):
        extract_text(b"")


def test_extract_text_rejects_unsupported_extension():
    with pytest.raises(ValueError, match="PDF or DOCX"):
        extract_text(b"hello", filename="resume.txt")


def test_extract_text_rejects_too_short_pdf():
    minimal = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 200 200]/Parent 2 0 R/Contents 4 0 R>>endobj\n"
        b"4 0 obj<</Length 9>>stream\nBT ET\nendstream endobj\n"
        b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n0\n%%EOF"
    )
    with pytest.raises(ValueError, match="text"):
        extract_text(minimal, filename="resume.pdf")
