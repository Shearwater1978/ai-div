import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from date_parser import parse_date_line

def test_parse_date_line_with_quotes():
    line = 'Statement,Data,Period,"January 1, 2025 - January 31, 2025"'
    year, fromDate, toDate = parse_date_line(line)
    assert year == "2025"
    assert fromDate == "2025-01-01"
    assert toDate == "2025-01-31"

def test_parse_date_line_without_quotes():
    line = 'Statement,Data,Period,January 1, 2025 - January 31, 2025'
    year, fromDate, toDate = parse_date_line(line)
    assert year == "2025"
    assert fromDate == "2025-01-01"
    assert toDate == "2025-01-31"
