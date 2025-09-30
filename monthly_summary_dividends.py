import calendar
from datetime import datetime
from logger_module import log_module_call, log_event

def monthly_summary_dividends(fromDate: str, toDate: str, DIV_RAW_REPORT: dict, year: str):
    """
    Calculate monthly summary for dividends.
    """
    log_module_call("monthly_summary_dividends")

    # Parse dates
    try:
        from_dt = datetime.strptime(fromDate, "%Y-%m-%d")
        to_dt = datetime.strptime(toDate, "%Y-%m-%d")
    except Exception as e:
        log_event(f"Error parsing dates: {e}")
        return DIV_RAW_REPORT

    # Verify same month/year
    if from_dt.month != to_dt.month or from_dt.year != to_dt.year:
        log_event(f"Month mismatch in fromDate ({fromDate}) and toDate ({toDate}) - aborting summary")
        return DIV_RAW_REPORT

    month_name = calendar.month_name[from_dt.month].lower()

    year_entry = next((y for y in DIV_RAW_REPORT.get("years", []) if y["year"] == year), None)
    if not year_entry:
        log_event(f"Year {year} not found in report JSON")
        return DIV_RAW_REPORT

    # Ensure monthly_dividends list exists
    if "monthly_dividends" not in year_entry:
        year_entry["monthly_dividends"] = []

    # Prevent duplicates
    if any(m["month"] == month_name for m in year_entry["monthly_dividends"]):
        log_event(f"Monthly dividend summary for {month_name} already exists - skipping")
        return DIV_RAW_REPORT

    # Sum amounts
    total_amount = 0.0
    total_amount_pln = 0.0

    for div in year_entry.get("dividends", []):
        for record in div.get("dividend", []):
            try:
                rec_date = datetime.strptime(record["date"], "%Y-%m-%d")
                if rec_date.month == from_dt.month and rec_date.year == from_dt.year:
                    total_amount += float(record["amount"])
                    if record.get("amountPln") not in ("", None, ""):
                        total_amount_pln += float(record["amountPln"])
            except Exception as e:
                log_event(f"Error processing dividend record: {e}")

    year_entry["monthly_dividends"].append({
        "month": month_name,
        "amountMonth": round(total_amount, 4),
        "amountPlnMonth": round(total_amount_pln, 4)
    })

    log_event(f"Monthly dividend summary for {month_name} added: amount={total_amount}, amountPln={total_amount_pln}")
    return DIV_RAW_REPORT
