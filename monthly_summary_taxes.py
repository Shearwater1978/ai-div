import calendar
from datetime import datetime
from logger_module import log_module_call, log_event

def monthly_summary_taxes(fromDate: str, toDate: str, DIV_RAW_REPORT: dict, year: str, raw_tax_lines: list):
    """
    Calculate monthly summary for taxes using all raw tax lines from the broker CSV
    (matching broker's 'Withholding Tax,Data,Total') and convert each to PLN
    based on currency-specific mid rate from RATES.
    """
    log_module_call("monthly_summary_taxes")

    try:
        from_dt = datetime.strptime(fromDate, "%Y-%m-%d")
        to_dt = datetime.strptime(toDate, "%Y-%m-%d")
    except Exception as e:
        log_event(f"Error parsing dates: {e}")
        return DIV_RAW_REPORT

    if from_dt.month != to_dt.month or from_dt.year != to_dt.year:
        log_event(f"Month mismatch in fromDate ({fromDate}) and toDate ({toDate}) - aborting summary")
        return DIV_RAW_REPORT

    month_name = calendar.month_name[from_dt.month].lower()

    year_entry = next((y for y in DIV_RAW_REPORT.get("years", []) if y["year"] == year), None)
    if not year_entry:
        log_event(f"Year {year} not found in report JSON")
        return DIV_RAW_REPORT

    if "monthly_taxes" not in year_entry:
        year_entry["monthly_taxes"] = []

    if any(m["month"] == month_name for m in year_entry["monthly_taxes"]):
        log_event(f"Monthly tax summary for {month_name} already exists - skipping")
        return DIV_RAW_REPORT

    total_amount = 0.0
    total_amount_pln = 0.0
    rates_list = year_entry.get("rates", [])

    for line in raw_tax_lines:
        parts = line.split(",")
        if len(parts) >= 6:
            amt_str = parts[5].strip()
            currency = parts[2].strip()
            date_str = parts[3].strip()
            try:
                amt_value = float(amt_str)
                total_amount += amt_value

                # Convert to PLN using mid rate
                match_curr = next((r for r in rates_list if r["currency"] == currency), None)
                if match_curr:
                    match_rate = next((rr for rr in match_curr["rate"] if rr["effectiveDate"] == date_str), None)
                    if match_rate:
                        total_amount_pln += amt_value * match_rate["mid"]
                    else:
                        # nearest previous date
                        sorted_rates = sorted(match_curr["rate"], key=lambda x: x["effectiveDate"], reverse=True)
                        for rr in sorted_rates:
                            if rr["effectiveDate"] < date_str:
                                total_amount_pln += amt_value * rr["mid"]
                                break
                else:
                    log_event(f"No rates found for currency {currency}")

            except ValueError:
                log_event(f"Cannot parse amount '{amt_str}' in tax line: {line}")

    year_entry["monthly_taxes"].append({
        "month": month_name,
        "amountMonth": round(total_amount, 4),
        "amountPlnMonth": round(total_amount_pln, 4)
    })

    log_event(
        f"Monthly tax summary for {month_name} added: amountMonth={total_amount}, amountPlnMonth={total_amount_pln}"
    )

    return DIV_RAW_REPORT
