import sys
import os
import glob
import json
import calendar
from broker_report_processor import process_broker_csv
from date_parser import parse_date_line
from logger_module import log_module_call, log_event

def get_month_name_from_csv(csv_file):
    """Extracts year, fromDate, toDate, and month name from broker CSV file."""
    with open(csv_file, "r", encoding="utf-8") as f:
        for line in f:
            if "Statement,Data,Period," in line:
                year, fromDate, toDate = parse_date_line(line)
                month_name = calendar.month_name[int(fromDate.split("-")[1])].lower()
                return year, fromDate, toDate, month_name
    return None, None, None, None

def month_already_processed(year, month_name):
    """Checks if monthly_dividends and monthly_taxes in JSON for the year already contain this month."""
    json_path = os.path.join("tax_reports", f"divs_{year}.json")
    if not os.path.exists(json_path):
        return False

    try:
        with open(json_path, "r", encoding="utf-8") as jf:
            data = json.load(jf)
    except Exception as e:
        log_event(f"Error reading JSON file {json_path}: {e}")
        return False

    # Сравнение по строкам, независимо от регистра
    year_entry = next((y for y in data.get("years", []) if str(y["year"]) == str(year)), None)
    if not year_entry:
        return False

    monthly_divs = year_entry.get("monthly_dividends", [])
    monthly_tax = year_entry.get("monthly_taxes", [])

    # Месяц считается обработанным, если он есть и в monthly_dividends, и в monthly_taxes
    if any(m.get("month", "").lower() == month_name.lower() for m in monthly_divs) and \
       any(m.get("month", "").lower() == month_name.lower() for m in monthly_tax):
        return True

    return False

def run_main(argv=None):
    """Main entry point of the script (supports test calls)."""
    log_module_call("main")
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("Usage: python main.py <CSV filename or 'all'>")
        return

    arg = argv[0]

    if arg.lower() == "all":
        pattern = "U*_*.csv"   # matches U12345678_202507_202507.csv type files
        report_files = glob.glob(pattern)

        if not report_files:
            log_event("No broker CSV reports matching pattern found.")
            print("No broker CSV reports found.")
            return

        processed_count = 0
        skipped_count = 0

        for file in sorted(report_files):
            log_event(f"Checking broker report file: {file}")

            year, fromDate, toDate, month_name = get_month_name_from_csv(file)
            if not year:
                log_event(f"Cannot extract date info from {file} - skipping")
                skipped_count += 1
                continue

            if month_already_processed(year, month_name):
                log_event(f"Report for {month_name} {year} already processed - skipping")
                skipped_count += 1
                continue

            log_event(f"Processing broker report file: {file}")
            process_broker_csv(file)
            processed_count += 1

        print(f"Processed {processed_count} reports, skipped {skipped_count} already processed months.")

    else:
        report_file = arg
        if not os.path.exists(report_file):
            log_event(f"CSV file {report_file} not found. Exiting.")
            print(f"CSV file {report_file} not found.")
            return

        year, fromDate, toDate, month_name = get_month_name_from_csv(report_file)
        if month_already_processed(year, month_name):
            log_event(f"Report for {month_name} {year} already processed - skipping")
            print(f"Report for {month_name} {year} already processed - skipping")
            return

        process_broker_csv(report_file)

if __name__ == "__main__":
    run_main()
