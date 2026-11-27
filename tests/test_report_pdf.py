"""Weekly reports as PDF: real PDF files whose text says what the report says."""

import io
from datetime import UTC, datetime

import pypdf
import pytest
from test_preview import save_month_change, seeded_store

from pipeline.report_pdf import find_font, to_pdf
from pipeline.reports import build_report

NOW = datetime(2026, 11, 24, 21, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def report():
    store = seeded_store()
    save_month_change(store, {"PHL": 5, "IND": 3})
    return build_report(store, now=NOW)


def text_of(pdf: bytes) -> str:
    return "\n".join(page.extract_text() for page in pypdf.PdfReader(io.BytesIO(pdf)).pages)


def test_report_pdf_is_a_valid_pdf_with_the_title_and_headline(report):
    pdf = to_pdf(report)

    reader = pypdf.PdfReader(io.BytesIO(pdf))
    text = text_of(pdf)
    assert pdf.startswith(b"%PDF") and len(reader.pages) >= 1
    assert "Week 48, 2026" in text and "Philippines" in text
    assert reader.metadata.title == "WellGTM weekly report: Week 48, 2026 (23–29 Nov)"


def test_report_pdf_has_every_section(report):
    text = text_of(to_pdf(report))

    for heading in ("TOP3", "Rank changes", "Alerts", "Exports", "Forecast", "Ingredient prices", "Data and pipeline"):
        assert heading in text, heading


def test_rank_changes_list_each_mover_with_old_and_new_rank(report):
    text = text_of(to_pdf(report))

    assert "#5 → #3" in text  # the Philippines, month on month


def test_without_a_korean_font_korean_names_are_written_in_english(report):
    text = text_of(to_pdf(report, font=None))

    assert "관세청" not in text and ("Korea Customs Service" in text or "Korea Customs" in text)


def test_pages_are_numbered(report):
    text = text_of(to_pdf(report))

    assert "Page 1 of" in text


def test_font_discovery_returns_an_existing_file_or_none():
    font = find_font()

    assert font is None or font.exists()


def test_re_export_hubs_are_labelled_among_the_fastest_growing_destinations():
    report = {
        "exports": {
            "fastest_destinations": [
                {"iso3": "NLD", "name": "Netherlands", "growth": 0.379, "hub": True},
                {"iso3": "DEU", "name": "Germany", "growth": 0.343, "hub": False},
            ]
        }
    }
    from pipeline.report_pdf import destinations_line

    line = destinations_line(report["exports"]["fastest_destinations"])

    assert "Netherlands (re-export hub) +37.9%" in line and "Germany +34.3%" in line


def test_negative_changes_use_a_minus_sign(report):
    text = text_of(to_pdf(report))

    assert "−1" in text or "−2" in text
