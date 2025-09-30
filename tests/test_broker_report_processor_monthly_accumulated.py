import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from broker_report_processor import process_broker_csv

def test_monthly_summaries_accumulate_for_two_months(tmp_path):
    """
    Integration test for broker_report_processor:
    Process reports for March and April in one year.
    Check that monthly_dividends and monthly_taxes contain results for both months
    """

    # === Prepare CSV for March ===
    march_csv = tmp_path / "march.csv"
    march_csv.write_text(
        'Statement,Data,Period,"March 1, 2025 - March 31, 2025"\n'
        'Dividends,Header,Currency\n'
        'Dividends,Data,USD,2025-03-05,TST (US0000000001) Cash Dividend USD 0.40 per Share,4.4\n'
        'Withholding Tax,Header,Currency,Date\n'
        'Withholding Tax,Data,USD,2025-03-06,TST (US0000000001) Cash Dividend USD 0.94 per Share - US Tax,-2.12\n',
        encoding="utf-8"
    )

    # === Prepare CSV for April ===
    april_csv = tmp_path / "april.csv"
    april_csv.write_text(
        'Statement,Data,Period,"April 1, 2025 - April 30, 2025"\n'
        'Dividends,Header,Currency\n'
        'Dividends,Data,USD,2025-04-10,TST (US0000000001) Cash Dividend USD 0.50 per Share,5.0\n'
        'Withholding Tax,Header,Currency,Date\n'
        'Withholding Tax,Data,USD,2025-04-11,TST (US0000000001) Cash Dividend USD 0.94 per Share - US Tax,-3.00\n',
        encoding="utf-8"
    )

    # Fake RATES for March and April
    fake_rates_march = [
        {"currency": "USD", "rate": [
            {"effectiveDate": "2025-03-05", "mid": 4.1200},
            {"effectiveDate": "2025-03-06", "mid": 4.1500}
        ]}
    ]
    fake_rates_april = [
        {"currency": "USD", "rate": [
            {"effectiveDate": "2025-04-10", "mid": 4.5000},
            {"effectiveDate": "2025-04-11", "mid": 4.5500}
        ]}
    ]

    import broker_report_processor
    cwd = os.getcwd()
    os.chdir(tmp_path)

    # === First run (March) ===
    broker_report_processor.get_rates_for_period = lambda _: fake_rates_march
    process_broker_csv("march.csv")

    # === Second run (April) ===
    broker_report_processor.get_rates_for_period = lambda _: fake_rates_april
    process_broker_csv("april.csv")

    # Load JSON and check
    json_file = tmp_path / "tax_reports" / "divs_2025.json"
    assert json_file.exists(), "JSON file should exist after processing"
    data = json.loads(json_file.read_text(encoding="utf-8"))
    year_entry = data["years"][0]

    # Check monthly_dividends
    assert "monthly_dividends" in year_entry
    assert len(year_entry["monthly_dividends"]) == 2, "Should have two months in monthly_dividends"
    months_div = {m["month"] for m in year_entry["monthly_dividends"]}
    assert "march" in months_div
    assert "april" in months_div

    # Validate March dividend amountPln
    march_div = next(m for m in year_entry["monthly_dividends"] if m["month"] == "march")
    assert round(march_div["amountPlnMonth"], 4) == round(4.4 * 4.1200, 4)

    # Validate April dividend amountPln
    april_div = next(m for m in year_entry["monthly_dividends"] if m["month"] == "april")
    assert round(april_div["amountPlnMonth"], 4) == round(5.0 * 4.5000, 4)

    # Check monthly_taxes
    assert "monthly_taxes" in year_entry
    assert len(year_entry["monthly_taxes"]) == 2, "Should have two months in monthly_taxes"
    months_tax = {m["month"] for m in year_entry["monthly_taxes"]}
    assert "march" in months_tax
    assert "april" in months_tax

    # Validate March tax amountPln
    march_tax = next(m for m in year_entry["monthly_taxes"] if m["month"] == "march")
    assert round(march_tax["amountPlnMonth"], 4) == round(-2.12 * 4.1500, 4)

    # Validate April tax amountPln
    april_tax = next(m for m in year_entry["monthly_taxes"] if m["month"] == "april")
    assert round(april_tax["amountPlnMonth"], 4) == round(-3.00 * 4.5500, 4)

    os.chdir(cwd)
