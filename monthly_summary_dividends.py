import calendar
from datetime import datetime
from logger_module import log_module_call, log_event

def monthly_summary_dividends(fromDate: str, toDate: str, DIV_RAW_REPORT: dict, year: str):
    log_module_call("monthly_summary_dividends")
    
    try:
        from_dt = datetime.strptime(fromDate, "%Y-%m-%d")
        to_dt = datetime.strptime(toDate, "%Y-%m-%d")
    except Exception as e:
        log_event(f"Error parsing dates: {e}")
        return DIV_RAW_REPORT

    # Month consistency check
    if from_dt.month != to_dt.month or from_dt.year != to_dt.year:
        log_event(f"Month mismatch in fromDate ({fromDate}) and toDate ({toDate}) - aborting monthly summary")
        return DIV_RAW_REPORT

    month_name = calendar.month_name[from_dt.month].lower()
    year_entry = next((y for y in DIV_RAW_REPORT.get("years", []) if y["year"] == year), None)
    if not year_entry:
        log_event(f"Year {year} not found in JSON structure")
        return DIV_RAW_REPORT

    if "monthly_dividends" not in year_entry:
        year_entry["monthly_dividends"] = []

    if any(m["month"] == month_name for m in year_entry["monthly_dividends"]):
        log_event(f"Monthly dividends for {month_name} already exists - skipping")
        return DIV_RAW_REPORT

    total_amount_usd = 0.0
    total_amount_pln = 0.0

    rates = year_entry.get("rates", [])

    for div in year_entry.get("dividends", []):
        for record in div.get("dividend", []):
            try:
                rec_date = datetime.strptime(record["date"], "%Y-%m-%d")
                if rec_date.month == from_dt.month and rec_date.year == from_dt.year:

                    currency = record.get("currency", "").upper()
                    amount = float(record["amount"])

                    if currency == "USD":
                        total_amount_usd += amount
                    else:
                        # Convert to USD using rate[effectiveDate] → mid
                        rate_entry = next((r for r in rates if r["currency"] == currency), None)
                        if rate_entry:
                            # try exact date
                            rate_match = next((rr for rr in rate_entry["rate"]
                                               if rr["effectiveDate"] == record.get("effectiveDate", record["date"])), None)
                            if not rate_match:
                                # fallback to any past date
                                past_rates = sorted(rate_entry["rate"], key=lambda x: x["effectiveDate"], reverse=True)
                                for rr in past_rates:
                                    if rr["effectiveDate"] < record["date"]:
                                        rate_match = rr
                                        break
                            if rate_match:
                                # Convert amount in other currency → USD
                                converted = amount / rate_match["mid"]
                                total_amount_usd += converted
                                log_event(f"Converted {amount} {currency} to {converted} USD for {div['ticker']}")
                            else:
                                log_event(f"No rate found for {currency} on {record['date']} to convert to USD")

                    # amountPlnMonth includes all currencies
                    if record.get("amountPln") not in ("", None):
                        total_amount_pln += float(record["amountPln"])

            except Exception as e:
                log_event(f"Error processing dividend record: {e}")

    year_entry["monthly_dividends"].append({
        "month": month_name,
        "amountMonth": round(total_amount_usd, 6),
        "amountPlnMonth": round(total_amount_pln, 4)
    })

    log_event(f"Monthly dividends summary for {month_name}: USD total={total_amount_usd}, PLN total={total_amount_pln}")
    return DIV_RAW_REPORT
