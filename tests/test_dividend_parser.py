import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dividend_parser import parse_dividend_line

def test_dividend_parser_with_exact_rate():
    DIV_RAW_REPORT = {"years": [{"year": "2025", "dividends": []}]}
    RATES = [
        {"currency": "USD", "rate": [
            {"effectiveDate": "2025-01-02", "mid": 4.1219}
        ]}
    ]
    line = "Dividends,Data,USD,2025-01-02,MGA (CA5592224011) Cash Dividend USD 0.40 per Share (Ordinary Dividend),4.4"
    result = parse_dividend_line(line, DIV_RAW_REPORT, "2025", RATES)
    div = result["dividend"][0]
    assert result["ticker"] == "MGA"
    assert div["exchangeRate"] == 4.1219
    assert div["effectiveDate"] == "2025-01-02"
    assert round(div["amountPln"], 4) == round(4.4 * 4.1219, 4)

def test_dividend_parser_with_previous_rate():
    DIV_RAW_REPORT = {"years": [{"year": "2025", "dividends": []}]}
    RATES = [
        {"currency": "USD", "rate": [
            {"effectiveDate": "2025-01-01", "mid": 4.1000}
        ]}
    ]
    line = "Dividends,Data,USD,2025-01-02,MGA (CA5592224011),4.4"
    result = parse_dividend_line(line, DIV_RAW_REPORT, "2025", RATES)
    div = result["dividend"][0]
    assert div["effectiveDate"] == "2025-01-01"
    assert div["exchangeRate"] == 4.1000
    assert round(div["amountPln"], 4) == round(4.4 * 4.1000, 4)

def test_dividend_parser_duplicate():
    DIV_RAW_REPORT = {
        "years": [{"year": "2025", "dividends": [
            {"ticker": "MGA", "dividend": [{"date": "2025-01-02"}]}
        ]}]
    }
    RATES = []
    line = "Dividends,Data,USD,2025-01-02,MGA (CA5592224011),4.4"
    res = parse_dividend_line(line, DIV_RAW_REPORT, "2025", RATES)
    assert res == {}
