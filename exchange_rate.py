import requests
from logger_module import log_module_call, log_event

def get_rates_for_period(currencies_and_dates: dict):
    """
    currencies_and_dates: {
        "fromDate": "...",
        "toDate": "...",
        "currencies": ["USD", "CAD"]
    }
    Returns list RATES with all effectiveDate/mid for each currency.
    """
    log_module_call("exchange_rate")

    from_date = currencies_and_dates['fromDate']
    to_date = currencies_and_dates['toDate']
    currencies = currencies_and_dates['currencies']

    rates_list = []

    for currency in currencies:
        url = f"https://api.nbp.pl/api/exchangerates/rates/a/{currency}/{from_date}/{to_date}?format=json"
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                data = resp.json()
                code = data['code']
                rate_entries = [{"effectiveDate": r['effectiveDate'], "mid": r['mid']} for r in data['rates']]
                rates_list.append({"currency": code, "rate": rate_entries})
                log_event(f"Fetched {len(rate_entries)} rates for {currency}")
            else:
                log_event(f"Failed to fetch rates for {currency}: HTTP {resp.status_code}")
        except Exception as e:
            log_event(f"Error fetching rates: {e}")

    return rates_list
