import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from broker_report_processor import process_broker_csv

def test_broker_processor_creates_monthly_fields(tmp_path):
    """
    Integration test for broker_report_processor:
    After processing example CSV, JSON should contain monthly_dividends and monthly_taxes
    with correct amountMonth and amountPlnMonth.
    """

    # Prepare fake CSV in temp dir
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        'Statement,Data,Period,"March 1, 2025 - March 31, 2025"\n'
        'Dividends,Header,Currency\n'
        'Dividends,Data,USD,2025-03-05,TST (US0000000001) Cash Dividend USD 0.40 per Share,4.4\n'
        'Withholding Tax,Header,Currency,Date\n'
        'Withholding Tax,Data,USD,2025-03-06,TST (US0000000001) Cash Dividend USD 0.94 per Share - US Tax,-2.12\n',
        encoding="utf-8"
    )

    # Fake rates for March
    fake_rates = [
        {"currency": "USD", "rate": [
            {"effectiveDate": "2025-03-05", "mid": 4.1200},
            {"effectiveDate": "2025-03-06", "mid": 4.1500}
        ]}
    ]

    # Patch get_rates_for_period to return fake rates
    import broker_report_processor
    broker_report_processor.get_rates_for_period = lambda _: fake_rates

    cwd = os.getcwd()
    os.chdir(tmp_path)

    # Process CSV
    process_broker_csv("sample.csv")

    # Load generated JSON
    json_file = tmp_path / "tax_reports" / "divs_2025.json"
    assert json_file.exists(), "JSON file should be created"
    data = json.loads(json_file.read_text(encoding="utf-8"))

    year_entry = data["years"][0]

    # Check monthly_dividends
    assert "monthly_dividends" in year_entry, "monthly_dividends field missing"
    assert len(year_entry["monthly_dividends"]) == 1
    monthly_div = year_entry["monthly_dividends"][0]
    assert monthly_div["month"] == "march"
    # 4.4 USD at mid=4.1200
    assert round(monthly_div["amountMonth"], 4) == 4.4
    assert round(monthly_div["amountPlnMonth"], 4) == round(4.4 * 4.1200, 4)

    # Check monthly_taxes
    assert "monthly_taxes" in year_entry, "monthly_taxes field missing"
    assert len(year_entry["monthly_taxes"]) == 1
    monthly_tax = year_entry["monthly_taxes"][0]
    assert monthly_tax["month"] == "march"
    # -2.12 USD at mid=4.1500
    assert round(monthly_tax["amountMonth"], 4) == -2.12
    assert round(monthly_tax["amountPlnMonth"], 4) == round(-2.12 * 4.1500, 4)

    os.chdir(cwd)
