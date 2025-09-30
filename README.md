# 📊 Automating Dividend Tracking in Poland with Python 3 and NBP Exchange Rates

## 1. Overview

This project automates the parsing of broker CSV reports, fetching exchange rates from the NBP API, and converting amounts to PLN.  
It helps investors manage dividend and tax records efficiently and store them in a detailed JSON format.
The peculiarity of this project lies in the fact that all the code was generated using LLM GPT-5. Errors encountered during the code execution process were also resolved through queries to the LLM.

**Features:**
- Automatically fetch exchange rates for all currencies present in the report.
- Calculate PLN amounts (`amountPln`) for dividends and taxes.
- Accumulate exchange rates across months using `merge_rates`.
- Support tickers with spaces before ISIN (e.g., `MGA (CA...)`).
- Skip and store year-mismatched tax lines in `tax_skipped_YEAR.csv`.
- Prevent duplicate entries.
- Modular architecture with full test coverage.

---

## 2. Requirements

**Language:** Python 3.8+  

**Dependencies:**
- requests>=2.31.0 # HTTP requests to NBP API 
- certifi>=2023.7.22 # SSL certificates for HTTPS
- pytest>=7.4.2 # Testing framework
- pytest-cov>=4.1.0 # Test coverage reporting

Install all dependencies:
```bash
pip install -r requirements.txt
```

## 3. Project Structure
```bash
project_root/
├── broker_report_processor.py     # Main CSV processing logic
├── date_parser.py                 # Extracts year/fromDate/toDate from Statement line
├── exchange_rate.py                # Fetches rates from NBP API
├── dividend_parser.py              # Parses dividend lines
├── dividend_adder.py               # Adds dividend entries to JSON
├── tax_parser.py                   # Parses tax lines
├── tax_adder.py                    # Adds tax entries to JSON
├── logger_module.py                # Logging
├── reports/                        # Archived CSV reports
├── tax_reports/                    # JSON files + skipped tax lines
├── tests/                          # All unit and integration tests
└── README.md                       # Project description and usage instructions
```

## 4. Usage
Run main script:
```bash
python main.py <report_filename.csv>
```

Example:
```bash
python main.py broker_report.csv
```

Where `broker_report.csv` is a file exported from the broker portal and located in the same directory as `main.py`.

## 5. Example Output
Input CSV:
```
Statement,Data,Period,"March 1, 2025 - March 31, 2025"
Dividends,Header,Currency
Dividends,Data,USD,2025-03-05,MGA (CA5592224011) Cash Dividend USD 0.40 per Share (Ordinary Dividend),4.4
Withholding Tax,Header,Currency,Date
Withholding Tax,Data,CAD,2025-03-06,MGA (CA5592224011) Cash Dividend USD 0.94 per Share - US Tax,-2.12
Withholding Tax,Data,USD,2024-12-30,BBB (US0000000000) Cash Dividend USD 0.50 per Share - Foreign Tax,-1.00
```

Rates block (`rates` in JSON):
```json
[
  {"currency": "USD", "rate": [{"effectiveDate": "2025-03-05", "mid": 4.1200}]},
  {"currency": "CAD", "rate": [{"effectiveDate": "2025-03-06", "mid": 3.2500}]}
]
```

Skipped taxes (`tax_skipped_2025.csv`):
```
Withholding Tax,Data,USD,2024-12-30,BBB (US0000000000) Cash Dividend USD 0.50 per Share - Foreign Tax,-1.00
```

## 6. Tests
Run all tests:
```bash
pytest -v
```

Run with coverage report:
```bash
pytest --cov=. --cov-report=term-missing --cov-report=html
```

## 7. CI/CD with GitHub Actions
Automated tests for all branches except `main` with coverage report (`.github/workflows/run-tests.yml`):
```yaml
name: Run Pytest with Coverage

on:
  push:
    branches-ignore:
      - main
  pull_request:
    branches-ignore:
      - main

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests with coverage
        run: |
          pytest --cov=. --cov-report=term-missing --cov-report=html --disable-warnings -v

      - name: Upload HTML coverage report
        uses: actions/upload-artifact@v3
        with:
          name: html-coverage-report
          path: htmlcov/
```
