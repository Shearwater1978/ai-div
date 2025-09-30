import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from exchange_rate import get_rates_for_period

def test_get_rates_for_period(monkeypatch):
    def fake_get(url):
        class FakeResp:
            status_code = 200
            def json(self):
                return {
                    "code": "USD",
                    "rates": [
                        {"effectiveDate": "2025-03-01", "mid": 4.1000},
                        {"effectiveDate": "2025-03-02", "mid": 4.1200}
                    ]
                }
        return FakeResp()

    monkeypatch.setattr("requests.get", fake_get)

    currencies_and_dates = {
        "fromDate": "2025-03-01",
        "toDate": "2025-03-31",
        "currencies": ["USD"]
    }

    rates = get_rates_for_period(currencies_and_dates)
    assert rates[0]["currency"] == "USD"
    assert len(rates[0]["rate"]) == 2
