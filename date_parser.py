import re
from datetime import datetime
from logger_module import log_module_call, log_event

def parse_date_line(line: str):
    """
    Extract year, fromDate, toDate from line like:
    Statement,Data,Period, January 1, 2025 - January 31, 2025
    """
    log_module_call("date_parser")

    # extract after Statement,Data,Period,
    parts = line.split("Statement,Data,Period,")
    if len(parts) < 2:
        log_event("No date found in Statement line")
        return None, None, None

    date_range = parts[1].strip().strip('"')
    from_str, to_str = [s.strip() for s in date_range.split(" - ")]

    from_dt = datetime.strptime(from_str, "%B %d, %Y")
    to_dt = datetime.strptime(to_str, "%B %d, %Y")

    year = str(from_dt.year)
    from_date = from_dt.strftime("%Y-%m-%d")
    to_date = to_dt.strftime("%Y-%m-%d")

    return year, from_date, to_date
