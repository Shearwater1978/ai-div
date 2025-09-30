from dividend_adder import add_dividend

def test_add_dividend_new_ticker():
    report = {"years": [{"year": "2025", "dividends": []}]}
    new_div = {"ticker": "AGR", "dividend": [{"amount": "4.4", "currency": "USD", "date": "2025-01-02", "exchangeRate": ""}]}
    updated = add_dividend(report, new_div, "2025")
    assert updated["years"][0]["dividends"][0]["ticker"] == "AGR"
