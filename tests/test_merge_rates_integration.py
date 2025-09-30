import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from broker_report_processor import process_broker_csv

def test_merge_rates_amountpln_accumulates_data(tmp_path):
    """
    Integration test:
    - Process two monthly reports (January, March)
    - Check that merge_rates keeps old rates while adding new ones
    - Verify amountPln calculation for dividends and taxes in each month
    """

    # ==== 1) Fake January CSV ====
    jan_csv = tmp_path / "january.csv"
    jan_csv.write_text(
        'Statement,Data,Period,"January 1, 2025 - January 31, 2025"\n'
        'Dividends,Header,Currency\n'
        'Dividends,Data,USD,2025-01-02,MGA (CA5592224011) Cash Dividend USD 0.40 per Share (Ordinary Dividend),4.4\n'
        'Withholding Tax,Header,Currency,Date\n'
        'Withholding Tax,Data,USD,2025-01-03,MGA (CA5592224011) Cash Dividend USD 0.94 per Share - US Tax,-2.00\n',
        encoding="utf-8"
    )

    # ==== 2) Fake March CSV ====
    mar_csv = tmp_path / "march.csv"
    mar_csv.write_text(
        'Statement,Data,Period,"March 1, 2025 - March 31, 2025"\n'
        'Dividends,Header,Currency\n'
        'Dividends,Data,USD,2025-03-05,MGA (CA5592224011) Cash Dividend USD 0.40 per Share (Ordinary Dividend),5.0\n'
        'Dividends,Data,CAD,2025-03-06,MGA (CA5592224011) Cash Dividend CAD 0.20 per Share (Ordinary Dividend),2.0\n'
        'Withholding Tax,Header,Currency,Date\n'
        'Withholding Tax,Data,CAD,2025-03-06,MGA (CA5592224011) Cash Dividend USD 0.94 per Share - US Tax,-1.50\n',
        encoding="utf-8"
    )

    # ==== Fake RATES for each processing ====
    fake_rates_jan = [
        {"currency": "USD", "rate": [
            {"effectiveDate": "2025-01-02", "mid": 4.10},
            {"effectiveDate": "2025-01-03", "mid": 4.15}
        ]}
    ]
    fake_rates_mar = [
        {"currency": "USD", "rate": [{"effectiveDate": "2025-03-05", "mid": 4.20}]},
        {"currency": "CAD", "rate": [{"effectiveDate": "2025-03-06", "mid": 3.25}]}
    ]

    import broker_report_processor
    cwd = os.getcwd()
    os.chdir(tmp_path)

    # Process January
    broker_report_processor.get_rates_for_period = lambda _: fake_rates_jan
    process_broker_csv("january.csv")

    # Process March
    broker_report_processor.get_rates_for_period = lambda _: fake_rates_mar
    process_broker_csv("march.csv")

    # ==== Load JSON and check ====
    json_file = tmp_path / "tax_reports" / "divs_2025.json"
    assert json_file.exists(), "JSON file should exist after processing two months"
    data = json.loads(json_file.read_text(encoding="utf-8"))

    rates = data["years"][0]["rates"]

    # USD should have both January and March dates
    usd_entry = next((r for r in rates if r["currency"] == "USD"), None)
    assert usd_entry is not None
    usd_dates = {r["effectiveDate"] for r in usd_entry["rate"]}
    assert "2025-01-02" in usd_dates
    assert "2025-01-03" in usd_dates
    assert "2025-03-05" in usd_dates

    # CAD should only be from March
    cad_entry = next((r for r in rates if r["currency"] == "CAD"), None)
    assert cad_entry is not None
    cad_dates = {r["effectiveDate"] for r in cad_entry["rate"]}
    assert "2025-03-06" in cad_dates

    # ==== Check amountPln for January dividend ====
    jan_div = next((d for d in data["years"][0]["dividends"][0]["dividend"] if d["date"] == "2025-01-02"), None)
    expected_jan_div_amountpln = round(float(jan_div["amount"]) * 4.10, 4)
    assert round(jan_div["amountPln"], 4) == expected_jan_div_amountpln

    # ==== Check amountPln for January tax ====
    jan_tax = next((t for t in data["years"][0]["taxes"][0]["tax"] if t["date"] == "2025-01-03"), None)
    expected_jan_tax_amountpln = round(float(jan_tax["amount"]) * 4.15, 4)
    assert round(jan_tax["amountPln"], 4) == expected_jan_tax_amountpln

    # ==== Check amountPln for March USD dividend ====
    mar_usd_div = next((d for d in data["years"][0]["dividends"][0]["dividend"] if d["date"] == "2025-03-05"), None)
    expected_mar_usd_amountpln = round(float(mar_usd_div["amount"]) * 4.20, 4)
    assert round(mar_usd_div["amountPln"], 4) == expected_mar_usd_amountpln

    # ==== Check amountPln for March CAD dividend ====
    mar_cad_div = None
    for div_entry in data["years"][0]["dividends"]:
        if div_entry["ticker"] == "MGA":
            for d in div_entry["dividend"]:
                if d["date"] == "2025-03-06":
                    mar_cad_div = d
                    break
    expected_mar_cad_amountpln = round(float(mar_cad_div["amount"]) * 3.25, 4)
    assert round(mar_cad_div["amountPln"], 4) == expected_mar_cad_amountpln

    # ==== Check amountPln for March CAD tax ====
    mar_cad_tax = next((t for t in data["years"][0]["taxes"][0]["tax"] if t["date"] == "2025-03-06"), None)
    expected_mar_cad_tax_amountpln = round(float(mar_cad_tax["amount"]) * 3.25, 4)
    assert round(mar_cad_tax["amountPln"], 4) == expected_mar_cad_tax_amountpln

    os.chdir(cwd)
