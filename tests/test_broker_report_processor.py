import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from broker_report_processor import process_broker_csv

def test_broker_report_full_pipeline(tmp_path):
    # Prepare test CSV
    csv_file = tmp_path / "report.csv"
    csv_file.write_text(
        'Statement,Data,Period,"March 1, 2025 - March 31, 2025"\n'
        'Dividends,Header,Currency\n'
        'Dividends,Data,USD,2025-03-05,MGA (CA5592224011) Cash Dividend USD 0.40 per Share (Ordinary Dividend),4.4\n'
        'Withholding Tax,Header,Currency,Date\n'
        'Withholding Tax,Data,CAD,2025-03-06,MGA (CA5592224011) Cash Dividend USD 0.94 per Share - US Tax,-2.12\n'
        'Withholding Tax,Data,USD,2024-12-30,BBB (US0000000000) Cash Dividend USD 0.50 per Share - Foreign Tax,-1.00\n',
        encoding="utf-8"
    )

    fake_rates = [
        {"currency": "USD", "rate": [{"effectiveDate": "2025-03-05", "mid": 4.1200}]},
        {"currency": "CAD", "rate": [{"effectiveDate": "2025-03-06", "mid": 3.2500}]}
    ]

    import broker_report_processor
    broker_report_processor.get_rates_for_period = lambda _: fake_rates

    cwd = os.getcwd()
    os.chdir(tmp_path)

    process_broker_csv("report.csv")

    json_file = tmp_path / "tax_reports" / "divs_2025.json"
    assert json_file.exists()
    json_data = json.loads(json_file.read_text(encoding="utf-8"))

    rates_block = json_data["years"][0]["rates"]
    assert any(r["currency"] == "USD" for r in rates_block)
    assert any(r["currency"] == "CAD" for r in rates_block)

    dividends = json_data["years"][0]["dividends"]
    div_entry = dividends[0]["dividend"][0]
    assert round(div_entry["amountPln"], 4) == round(4.4 * 4.1200, 4)

    taxes = json_data["years"][0]["taxes"]
    tax_entry = taxes[0]["tax"][0]
    assert round(tax_entry["amountPln"], 4) == round(-2.12 * 3.2500, 4)

    skipped_file = tmp_path / "tax_reports" / "tax_skipped_2025.csv"
    assert skipped_file.exists()
    skipped_content = skipped_file.read_text(encoding="utf-8")
    assert "2024-12-30" in skipped_content

    os.chdir(cwd)
