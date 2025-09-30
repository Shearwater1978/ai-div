import os
import json
import shutil
from logger_module import log_module_call, log_file_action, log_event
from date_parser import parse_date_line
from exchange_rate import get_rates_for_period
from dividend_parser import parse_dividend_line
from dividend_adder import add_dividend
from tax_parser import parse_tax_line
from tax_adder import add_tax
from monthly_summary_dividends import monthly_summary_dividends
from monthly_summary_taxes import monthly_summary_taxes

def merge_rates(existing_rates, new_rates):
    """
    Merge list of new_rates into existing_rates.
    For each currency, append any new {effectiveDate, mid} not already present.
    """
    for new_rate_entry in new_rates:
        currency = new_rate_entry["currency"]
        new_rate_list = new_rate_entry["rate"]

        existing_entry = next((r for r in existing_rates if r["currency"] == currency), None)
        if existing_entry:
            existing_dates = {r["effectiveDate"] for r in existing_entry["rate"]}
            for rate_item in new_rate_list:
                if rate_item["effectiveDate"] not in existing_dates:
                    existing_entry["rate"].append(rate_item)
        else:
            existing_rates.append({
                "currency": currency,
                "rate": new_rate_list.copy()
            })

    return existing_rates


def process_broker_csv(reportFileName: str):
    """
    Full processing of broker CSV report.
    """
    log_module_call("broker_report_processor")

    if not os.path.exists(reportFileName):
        log_event(f"File {reportFileName} not found. Exiting.")
        return

    log_file_action("Reading", reportFileName)

    year = None
    fromDate = None
    toDate = None
    CURRENCIES_AND_DATES = {
        "fromDate": "",
        "toDate": "",
        "currencies": []
    }
    currencies_found = set()

    # First pass — extract date range and all currencies
    with open(reportFileName, "r", encoding="utf-8") as f:
        for line in f:
            if "Statement,Data,Period," in line:
                year, fromDate, toDate = parse_date_line(line)
                CURRENCIES_AND_DATES["fromDate"] = fromDate
                CURRENCIES_AND_DATES["toDate"] = toDate

            if ",Data," in line and not "Total" in line:
                parts = line.strip().split(",")
                if len(parts) >= 3:
                    currency = parts[2].strip()
                    if len(currency) == 3 and currency.isalpha():
                        currencies_found.add(currency)

    CURRENCIES_AND_DATES["currencies"] = sorted(list(currencies_found))
    log_event(f"CURRENCIES_AND_DATES collected: {CURRENCIES_AND_DATES}")

    # Get rates from API
    RATES = get_rates_for_period(CURRENCIES_AND_DATES)
    log_event(f"RATES fetched: {len(RATES)} currencies")

    # Load or create JSON
    tax_dir = "tax_reports"
    os.makedirs(tax_dir, exist_ok=True)
    json_path = os.path.join(tax_dir, f"divs_{year}.json")

    if os.path.exists(json_path):
        log_file_action("Opening", json_path)
        with open(json_path, "r", encoding="utf-8") as jf:
            DIV_RAW_REPORT = json.load(jf)
        for ydata in DIV_RAW_REPORT.get("years", []):
            if ydata["year"] == year:
                ydata["rates"] = merge_rates(ydata.get("rates", []), RATES)
    else:
        DIV_RAW_REPORT = {
            "years": [
                {
                    "year": year,
                    "rates": RATES.copy(),
                    "dividends": [],
                    "taxes": [],
                    "fees": []
                }
            ]
        }

    # Second pass — process dividends and taxes
    with open(reportFileName, "r", encoding="utf-8") as f:
        for line in f:
            if "Dividends,Header,Currency" in line or line.startswith("Dividends,Data,Total"):
                continue
            if "Dividends,Data" in line:
                DIV_NEW = parse_dividend_line(line, DIV_RAW_REPORT, year, RATES)
                DIV_RAW_REPORT = add_dividend(DIV_RAW_REPORT, DIV_NEW, year)
                continue

            if "Withholding Tax,Header,Currency,Date" in line or line.startswith("Withholding Tax,Data,Total"):
                continue
            if "Withholding Tax,Data" in line:
                TAX_NEW = parse_tax_line(line, DIV_RAW_REPORT, year, RATES)
                DIV_RAW_REPORT = add_tax(DIV_RAW_REPORT, TAX_NEW, year)
                continue

    # === New integration: calculate monthly summaries ===
    log_event("Calculating monthly summaries for dividends and taxes")
    DIV_RAW_REPORT = monthly_summary_dividends(fromDate, toDate, DIV_RAW_REPORT, year)
    DIV_RAW_REPORT = monthly_summary_taxes(fromDate, toDate, DIV_RAW_REPORT, year)

    # Save JSON
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(DIV_RAW_REPORT, jf, ensure_ascii=False, indent=2)
    log_file_action("Writing", json_path)

    # Archive original CSV
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    copy_name = f"div_{fromDate}_{toDate}.csv"
    shutil.copy(reportFileName, os.path.join(reports_dir, copy_name))
    log_event(f"Copied original CSV to {copy_name} in reports/")
