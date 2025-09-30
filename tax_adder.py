from logger_module import log_module_call, log_event

def add_tax(DIV_RAW_REPORT: dict, TAX_NEW: dict, year: str):
    log_module_call("tax_adder")

    if not TAX_NEW:
        return DIV_RAW_REPORT

    for ydata in DIV_RAW_REPORT["years"]:
        if ydata["year"] == year:
            for tax_item in ydata["taxes"]:
                if tax_item["ticker"] == TAX_NEW["ticker"]:
                    tax_item["tax"].extend(TAX_NEW["tax"])
                    log_event(f"Tax added for {TAX_NEW['ticker']} in {year}")
                    return DIV_RAW_REPORT
            ydata["taxes"].append(TAX_NEW)
            log_event(f"New ticker {TAX_NEW['ticker']} created and tax added in {year}")
            return DIV_RAW_REPORT

    return DIV_RAW_REPORT
