# 📊 Automating Dividend Tracking in Poland with Python 3 and NBP Exchange Rates

## 1. Overview

This project automates the parsing of broker CSV reports, fetching exchange rates from the NBP API, and converting amounts to PLN.  
It helps investors manage dividend and tax records efficiently and store them in a detailed JSON format.
The peculiarity of this project lies in the fact that all the code was generated using LLM GPT-5. Errors encountered during the code execution process were also resolved through queries to the LLM.

**Features:**
- Multiple currencies in a single report (USD, CAD, etc.)
- Automatic PLN conversion (`amountPln`)
- Merging exchange rates across multiple months in the same year (`merge_rates`)
- Extraction and accumulation of monthly summaries (`monthly_dividends`, `monthly_taxes`)
- Duplicate protection for monthly summaries
- Full unit and integration test coverage

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
```text
project_root/
├── main.py                             # Entry point script
├── broker_report_processor.py          # Main pipeline: CSV → JSON + monthly summaries
├── logger_module.py                    # Centralized logging
├── date_parser.py                       # Extract report date range (year/from/to)
├── exchange_rate.py                     # Fetch rates from NBP API for currencies/date range
├── dividend_parser.py                   # Parse dividend rows and calculate amountPln
├── dividend_adder.py                    # Add new dividends to year JSON
├── tax_parser.py                        # Parse tax rows and calculate amountPln
├── tax_adder.py                         # Add new taxes to year JSON
├── monthly_summary_dividends.py         # Calculate monthly totals for dividends
├── monthly_summary_taxes.py             # Calculate monthly totals for taxes
├── reports/                             # Archived original CSVs
├── tax_reports/                         # Generated JSONs and skipped tax lines
└── tests/                               # Unit and integration tests
```

## 4. Usage
Download your broker report in CSV format: (MTM Summary → Period → Custom → Select Month → Download CSV).

Place the CSV file in the same directory as main.py or pass the file path as an argument.

Run:

Run main script:
```bash
python main.py <report_filename.csv>
```

Example:
```bash
python main.py broker_report.csv
```

The script will:

- Parse dates and currencies from CSV.
- Fetch rates from NBP API for all currencies in that month.
- Build/update `tax_reports/divs_YEAR.json` with `dividends`, `taxes`, `fees`, and `rates`.
- Calculate `amountPln` (amount * mid).
- Merge exchange rates across months in the same year.
- Append `monthly_dividends` and `monthly_taxes` summaries for that month.
- Save a copy of the CSV to `reports/div_fromDate_toDate.csv`.

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

Monthly Summaries
Example JSON snippet after processing March 2025:
```json
{
  "year": "2025",
  "monthly_dividends": [
    {
      "month": "march",
      "amountMonth": 4.40,
      "amountPlnMonth": 18.128
    }
  ],
  "monthly_taxes": [
    {
      "month": "march",
      "amountMonth": -2.12,
      "amountPlnMonth": -8.798
    }
  ]
}
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

Test coverage:

- Unit Tests:
  - `date_parser`, `dividend_parser`, `tax_parser`, `monthly_summary_dividends`, `monthly_summary_taxes`.
- Integration Tests:
  - Full CSV → JSON pipeline (ёbroker_report_processorё)
  - Merge of exchange rates from multiple months
  - Adding monthly summaries once per month
  - Accumulation over multiple months in one year

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

## 📌 Notes
- Reprocessing the same month will not duplicate monthly summaries — logs will show `"already exists - skipping"`.
- Exchange rates and transactions accumulate across months in each year.
- Tax lines from a different year are saved to `tax_reports/tax_skipped_YEAR.csv`.

## 📞 Support
If you encounter an issue:

- Open a GitHub issue.
- Provide example CSV lines.
- Attach logs from process.log for faster debugging.
