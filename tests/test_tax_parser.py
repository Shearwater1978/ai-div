import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tax_parser import parse_tax_line

def test_tax_parser_with_exact_rate(tmp_path):
    DIV_RAW_REPORT = {"years": [{"year": "2025", "taxes": []}]}
    RATES = [
        {"currency": "USD", "rate": [
            {"effectiveDate": "2025-01-07", "mid": 4.1234}
        ]}
    ]
    line = "Withholding Tax,Data,USD,2025-01-07,MGA (CA5592224011) Cash Dividend USD 0.94 per Share - US Tax,-2.12"
    result = parse_tax_line(line, DIV_RAW_REPORT, "2025", RATES)
    tax = result["tax"][0]
    assert result["ticker"] == "MGA"
    assert tax["exchangeRate"] == 4.1234
    assert tax["effectiveDate"] == "2025-01-07"
    assert round(tax["amountPln"], 4) == round(-2.12 * 4.1234, 4)

def test_tax_parser_with_previous_rate(tmp_path):
    DIV_RAW_REPORT = {"years": [{"year": "2025", "taxes": []}]}
    RATES = [
        {"currency": "USD", "rate": [
            {"effectiveDate": "2025-01-06", "mid": 4.1200}
        ]}
    ]
    line = "Withholding Tax,Data,USD,2025-01-07,MGA (CA5592224011),-2.12"
    result = parse_tax_line(line, DIV_RAW_REPORT, "2025", RATES)
    tax = result["tax"][0]
    assert tax["effectiveDate"] == "2025-01-06"
    assert tax["exchangeRate"] == 4.1200
    assert round(tax["amountPln"], 4) == round(-2.12 * 4.1200, 4)

def test_tax_parser_duplicate():
    DIV_RAW_REPORT = {
        "years": [{"year": "2025", "taxes": [
            {"ticker": "MGA", "tax": [{"date": "2025-01-07"}]}
        ]}]
    }
    RATES = []
    line = "Withholding Tax,Data,USD,2025-01-07,MGA (CA5592224011),-2.12"
    res = parse_tax_line(line, DIV_RAW_REPORT, "2025", RATES)
    assert res == {}

def test_tax_parser_year_mismatch(tmp_path):
    DIV_RAW_REPORT = {"years": [{"year": "2025", "taxes": []}]}
    RATES = []
    line = "Withholding Tax,Data,USD,2024-01-07,MGA (CA5592224011),-2.12"

    os.chdir(tmp_path)
    res = parse_tax_line(line, DIV_RAW_REPORT, "2025", RATES)
    assert res == {}

    skipped_file = tmp_path / "tax_reports" / "tax_skipped_2025.csv"
    assert skipped_file.exists()
    text = skipped_file.read_text(encoding="utf-8")
    assert line in text

    # Check no duplicate write
    res2 = parse_tax_line(line, DIV_RAW_REPORT, "2025", RATES)
    text2 = skipped_file.read_text(encoding="utf-8")
    assert text == text2
