import re
import os
from logger_module import log_module_call, log_event

def parse_tax_line(line: str, DIV_RAW_REPORT: dict, year: str, rates: list):
    """
    Parse Withholding Tax,Data line from broker CSV.
    Return dict with exchangeRate, effectiveDate, amountPln.
    Save year-mismatched lines to tax_skipped_YEAR.csv without duplicates.
    """
    log_module_call("tax_parser")

    parts = line.strip().split(",")
    if len(parts) < 6:
        log_event("Invalid tax line format")
        return {}

    currency = parts[2].strip()
    date = parts[3].strip()
    ticker_info = parts[4].strip()
    amount_str = parts[5].strip()
    code = parts[-1].strip() if len(parts) > 6 else ""

    # Extract ticker, allowing space before '('
    ticker_match = re.match(r"([A-Z]+)\s*\(", ticker_info)
    ticker = ticker_match.group(1) if ticker_match else ticker_info

    # Year check
    tax_year = date.split("-")[0]
    if tax_year != year:
        log_event(f"Year mismatch in tax line: {date} for report year {year}")
        tax_dir = "tax_reports"
        os.makedirs(tax_dir, exist_ok=True)
        skipped_file = os.path.join(tax_dir, f"tax_skipped_{year}.csv")
        # Avoid duplicates
        if os.path.exists(skipped_file):
            with open(skipped_file, "r", encoding="utf-8") as f:
                if line.strip() in {l.strip() for l in f}:
                    log_event("Skipped tax line already present in skipped file — ignoring duplicate")
                    return {}
        with open(skipped_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        return {}

    # Check duplicates
    for ydata in DIV_RAW_REPORT.get("years", []):
        if ydata["year"] == year:
            for tax_item in ydata["taxes"]:
                if tax_item["ticker"] == ticker:
                    if any(t['date'] == date for t in tax_item['tax']):
                        log_event(f"Duplicate tax {ticker} on {date}")
                        return {}

    # Get rate from RATES
    effective_date = date
    exchange_rate = None
    rate_entry = next((r for r in rates if r['currency'] == currency), None)
    if rate_entry:
        rate_match = next((rr for rr in rate_entry["rate"] if rr["effectiveDate"] == date), None)
        if rate_match:
            exchange_rate = rate_match["mid"]
        else:
            past_rates = sorted(rate_entry["rate"], key=lambda x: x["effectiveDate"], reverse=True)
            for rr in past_rates:
                if rr["effectiveDate"] < date:
                    exchange_rate = rr["mid"]
                    effective_date = rr["effectiveDate"]
                    break

    # Calculate amount in PLN
    amount_pln = ""
    try:
        if exchange_rate is not None:
            amount_value = float(amount_str)
            amount_pln = round(amount_value * exchange_rate, 4)
    except ValueError:
        log_event(f"Cannot convert amount '{amount_str}' to float for {ticker}")

    return {
        "ticker": ticker,
        "tax": [
            {
                "amount": amount_str,
                "currency": currency,
                "date": date,
                "code": code,
                "exchangeRate": exchange_rate if exchange_rate else "",
                "effectiveDate": effective_date if exchange_rate else "",
                "amountPln": amount_pln if amount_pln != "" else ""
            }
        ]
    }
