import sys
import os
from io import StringIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from broker_report_processor import process_broker_csv

def test_raw_monthly_tax_lines_collection(tmp_path, monkeypatch):
    """
    Test that RAW_MONTHLY_TAX_LINES collects all data lines from multiple currencies.
    """

    # Create synthetic CSV content
    csv_content = """Statement,Data,Period,"March 1, 2025 - March 31, 2025"
Withholding Tax,Header,Currency,Date,Description,Amount,Code
Withholding Tax,Data,CAD,2025-03-19,MFC(...),-0.33,
Withholding Tax,Data,Total,,,-0.33,
Withholding Tax,Data,Total in USD,,,-0.2303763,
Withholding Tax,Header,Currency,Date,Description,Amount,Code
Withholding Tax,Data,USD,2025-03-03,AFL(...),-0.87,
Withholding Tax,Data,USD,2025-03-10,CVX(...),-0.51,
Withholding Tax,Data,Total,,,-14.28,
Withholding Tax,Data,Total Withholding Tax in USD,,,-14.5103763,
"""

    csv_file = tmp_path / "march.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    # Monkeypatch dependencies (skip actual logic - we just check line collection)
    monkeypatch.setattr("broker_report_processor.get_rates_for_period", lambda _: [])
    monkeypatch.setattr("broker_report_processor.parse_date_line", lambda _: ("2025", "2025-03-01", "2025-03-31"))
    monkeypatch.setattr("broker_report_processor.parse_dividend_line", lambda *a, **k: {})
    monkeypatch.setattr("broker_report_processor.add_dividend", lambda *a, **k: a[0])
    monkeypatch.setattr("broker_report_processor.parse_tax_line", lambda *a, **k: {})
    monkeypatch.setattr("broker_report_processor.add_tax", lambda *a, **k: a[0])
    monkeypatch.setattr("broker_report_processor.monthly_summary_dividends", lambda *a, **k: a[2])
    collected_lines = []
    def fake_monthly_summary_taxes(fromDate, toDate, report, year, raw_lines):
        collected_lines.extend(raw_lines)
        return report
    monkeypatch.setattr("broker_report_processor.monthly_summary_taxes", fake_monthly_summary_taxes)

    # Run processor
    process_broker_csv(str(csv_file))

    # Check the collected RAW_MONTHLY_TAX_LINES — should include CAD and USD lines
    assert len(collected_lines) == 3
    assert any("CAD" in line for line in collected_lines)
    assert any("USD" in line for line in collected_lines)
