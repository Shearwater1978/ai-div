# 📊 Automating Dividend Tracking in Poland with Python 3 and NBP Exchange Rates

## 1. The Problem to Solve

Investors working with international brokers frequently download monthly reports in CSV format that contain:

- Dividend operations
- Withholding taxes
- Fees

Manual processing of these reports is time-consuming and prone to errors. Additionally, when income is specified in foreign currencies (USD, CAD, etc.), it must be converted to PLN using the correct exchange rate for the transaction date.

**Goal of the project:**
- Read the broker's CSV report
- Parse dividends and taxes
- Automatically fetch exchange rates from the official NBP API
- Calculate the PLN amounts (`amountPln`)
- Save the results in a structured JSON format

---

## 2. Output JSON Format

The result is stored in: tax_reports/divs_YEAR.json

Example structure:

```json
{
  "years": [
    {
      "year": "2025",
      "rates": [
        {
          "currency": "USD",
          "rate": [
            { "effectiveDate": "2025-03-01", "mid": 4.1219 },
            { "effectiveDate": "2025-03-02", "mid": 4.1512 }
          ]
        },
        {
          "currency": "CAD",
          "rate": [
            { "effectiveDate": "2025-03-01", "mid": 3.2500 }
          ]
        }
      ],
      "dividends": [
        {
          "ticker": "MGA",
          "dividend": [
            {
              "amount": "4.4",
              "currency": "USD",
              "date": "2025-03-05",
              "exchangeRate": 4.1200,
              "effectiveDate": "2025-03-05",
              "amountPln": 18.128
            }
          ]
        }
      ],
      "taxes": [
        {
          "ticker": "MGA",
          "tax": [
            {
              "amount": "-2.12",
              "currency": "CAD",
              "date": "2025-03-06",
              "code": "",
              "exchangeRate": 3.2500,
              "effectiveDate": "2025-03-06",
              "amountPln": -6.89
            }
          ]
        }
      ],
      "fees": []
    }
  ]
}
```

## 3. Processing Logic
### Step 1: Reading CSV and Collecting Base Data
- Extract date range (`Statement,Data,Period`) using `date_parser`:
  - `year` – report year
  - `fromDate` / `toDate` – period range
- Collect all currencies from the 3rd column of `Dividends,Data` and `Withholding Tax,Data` lines.
- Build `CURRENCIES_AND_DATES`:
```json
{
  "fromDate": "2025-03-01",
  "toDate": "2025-03-31",
  "currencies": ["USD", "CAD"]
}
```
### Step 2: Fetching Exchange Rates (`exchange_rate.p`y)
For each currency:
```
https://api.nbp.pl/api/exchangerates/rates/a/{currency}/{fromDate}/{toDate}?format=json
```
From response:
  - `"code"` – currency code
  - `"rates"` – list of entries with effectiveDate and mid

Stored in JSON under `rates`:
```json
{
  "currency": "USD",
  "rate": [
    {"effectiveDate": "2025-03-05", "mid": 4.1200}
  ]
}
```
### Step 3: Loading or Creating JSON (`broker_report_processor`)
  - If `divs_YEAR.json` exists → load and merge new rates using `merge_rates` (preserve past months).
  - If not → create new JSON structure with `rates`, `dividends`, `taxes`, `fees.`
### Step 4: Processing Dividends (`dividend_parser`)
  - Skip lines: `Dividends,Header,Currency` and `Dividends,Data,Total`.
  - Extract `ticker` (supports formats with spaces: `MGA (CA...))`.
  - Find in `rates` the `mid` for the date; if missing → use closest previous date.
  - Calculate:
    - `exchangeRate` – the rate used
    - `effectiveDate` – rate date
    - `amountPln` – float(amount) * mid
  - Check for duplicates (`ticker` + `date`) → skip if duplicate.
  - Add via `dividend_adder`.
### Step 5: Processing Taxes (`tax_parser`)
  - Skip lines: `Withholding Tax,Header,Currency,Date` and `Withholding Tax,Data,Total`.
  - If tax year ≠ report year:
    - Log entry
    - Save to tax_skipped_YEAR.csv (no duplicates)
    - Skip adding to JSON
- Extract `ticker` (supports format with spaces).
- Get rate and effective date via `rates`, calculate `amountPln`.
- Duplicate check → skip if exists.
- Add via `tax_adder`.
### Step 6: Saving Results
- Save updated JSON to `tax_reports/divs_YEAR.json`
- Archive CSV:
```
reports/div_fromDate_toDate.csv
```
## 4. Special Features and Advantages
- Multi-currency support: USD, CAD, and any other currencies found in the report.
- NBP API integration: automatic loading of rates for the report date range.
- PLN conversion: `amountPln` calculated directly in JSON.
- Ticker parsing with spaces: correctly handles `MGA (CA...)`.
- Duplicate protection: prevents duplicate entries for dividends and taxes.
- Year mismatch isolation: saves unrelated-year tax records separately to `tax_skipped_YEAR.csv`.
- Modular architecture: each component (`date_parser`, `dividend_parser`, `tax_parser`, `exchange_rate`, `*_adder`) is individually testable.
- *merge_rates*: accumulates rates across months, keeping historical data.
## 5. Example Workflow on Real CSV
Input CSV:
```csv
Statement,Data,Period,"March 1, 2025 - March 31, 2025"
Dividends,Header,Currency
Dividends,Data,USD,2025-03-05,MGA (CA5592224011) Cash Dividend USD 0.40 per Share (Ordinary Dividend),4.4
Withholding Tax,Header,Currency,Date
Withholding Tax,Data,CAD,2025-03-06,MGA (CA5592224011) Cash Dividend USD 0.94 per Share - US Tax,-2.12
Withholding Tax,Data,USD,2024-12-30,BBB (US0000000000) Cash Dividend USD 0.50 per Share - Foreign Tax,-1.00
```
Rates:
```json
[
  {"currency": "USD", "rate": [{"effectiveDate": "2025-03-05", "mid": 4.1200}]},
  {"currency": "CAD", "rate": [{"effectiveDate": "2025-03-06", "mid": 3.2500}]}
]
```
Result JSON: (see section 2)

Skipped Taxes (tax_skipped_2025.csv):
```csv
Withholding Tax,Data,USD,2024-12-30,BBB (US0000000000) Cash Dividend USD 0.50 per Share - Foreign Tax,-1.00
```
## 6. Tech Stack and Requirements
Language: Python 3.8+
Dependencies (`requirements.txt`):
```
requests>=2.31.0       # HTTP requests to NBP API
certifi>=2023.7.22     # SSL certificates for HTTPS
pytest>=7.4.2          # Testing
pytest-cov>=4.1.0      # Test coverage
```
Install with:
```bash
pip install -r requirements.txt
```
## 7. CI/CD with GitHub Actions
Automated tests run for all branches except main with coverage report:
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


