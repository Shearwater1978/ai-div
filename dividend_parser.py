import re
from logger_module import log_module_call, log_event

def parse_dividend_line(line: str, DIV_RAW_REPORT: dict, year: str, rates: list):
    """
    Parse Dividends,Data line (supports Ordinary and Bonus) and return dividend dict.
    """
    log_module_call("dividend_parser")
    log_event(f"Processing dividend CSV line: {line.strip()}")

    parts = line.strip().split(",")
    if len(parts) < 6:
        log_event("Invalid dividend line format - skipping")
        return {}

    currency = parts[2].strip()
    date = parts[3].strip()
    ticker_info = parts[4].strip()
    amount_str = parts[5].strip()

    # Extract ticker, allowing space before '('
    ticker_match = re.match(r"([A-Z]+)\s*\(", ticker_info)
    ticker = ticker_match.group(1) if ticker_match else ticker_info

    # Updated duplicate check: must match ticker, date, amount, currency to skip
    # Duplicate check
    for ydata in DIV_RAW_REPORT.get("years", []):
        if ydata["year"] == year:
            for div_item in ydata.get("dividends", []):
                if div_item["ticker"] == ticker:
                    for d in div_item["dividend"]:
                        if d.get("date") == date:
                            # Old-style duplicate check (no amount or currency in existing record)
                            if "amount" not in d or "currency" not in d:
                                log_event(f"Duplicate dividend for {ticker} on {date} - skipping")
                                return {}
                            # Full check if amount/currency exists
                            if (
                                str(d.get("amount", "")) == amount_str and
                                d.get("currency", "").upper() == currency.upper()
                            ):
                                log_event(
                                    f"Duplicate dividend for {ticker} on {date} with amount {amount_str} {currency} - skipping"
                                )
                                return {}

    # Get exchange rate
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

    # Calculate amountPln
    amount_pln = ""
    try:
        if exchange_rate is not None:
            amount_value = float(amount_str)
            amount_pln = round(amount_value * exchange_rate, 4)
    except ValueError:
        log_event(f"Cannot convert amount '{amount_str}' to float for {ticker}")

    return {
        "ticker": ticker,
        "dividend": [
            {
                "amount": amount_str,
                "currency": currency,
                "date": date,
                "exchangeRate": exchange_rate if exchange_rate else "",
                "effectiveDate": effective_date if exchange_rate else "",
                "amountPln": amount_pln if amount_pln != "" else ""
            }
        ]
    }
