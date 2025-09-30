from logger_module import log_module_call, log_event

def add_dividend(DIV_RAW_REPORT: dict, DIV_NEW: dict, year: str):
    log_module_call("dividend_adder")

    if not DIV_NEW:
        return DIV_RAW_REPORT

    for ydata in DIV_RAW_REPORT["years"]:
        if ydata["year"] == year:
            # add to existing ticker if found
            for div_item in ydata["dividends"]:
                if div_item["ticker"] == DIV_NEW["ticker"]:
                    div_item["dividend"].extend(DIV_NEW["dividend"])
                    log_event(f"Dividend added for {DIV_NEW['ticker']} in {year}")
                    return DIV_RAW_REPORT
            # new ticker
            ydata["dividends"].append(DIV_NEW)
            log_event(f"New ticker {DIV_NEW['ticker']} created and dividend added in {year}")
            return DIV_RAW_REPORT

    return DIV_RAW_REPORT
