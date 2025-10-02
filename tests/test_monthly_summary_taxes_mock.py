import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from monthly_summary_taxes import monthly_summary_taxes

def test_monthly_summary_taxes_two_currencies():
    """
    Test monthly_summary_taxes with synthetic RAW_MONTHLY_TAX_LINES in USD and CAD.
    """

    # Synthetic JSON structure with rates for two currencies
    DIV_RAW_REPORT = {
        "years": [
            {
                "year": "2025",
                "rates": [
                    {
                        "currency": "USD",
                        "rate": [
                            {"effectiveDate": "2025-03-03", "mid": 4.10},
                            {"effectiveDate": "2025-03-10", "mid": 4.12}
                        ]
                    },
                    {
                        "currency": "CAD",
                        "rate": [
                            {"effectiveDate": "2025-03-19", "mid": 3.20}
                        ]
                    }
                ],
                "monthly_taxes": []
            }
        ]
    }

    # Synthetic RAW_MONTHLY_TAX_LINES — mimics lines captured from CSV
    RAW_MONTHLY_TAX_LINES = [
        "Withholding Tax,Data,CAD,2025-03-19,MFC(...),-0.33,",
        "Withholding Tax,Data,USD,2025-03-03,AFL(...),-0.87,",
        "Withholding Tax,Data,USD,2025-03-10,CVX(...),-0.51,"
    ]

    updated_report = monthly_summary_taxes(
        "2025-03-01", "2025-03-31", DIV_RAW_REPORT, "2025", RAW_MONTHLY_TAX_LINES
    )

    # Extract March monthly_taxes
    march_tax = updated_report["years"][0]["monthly_taxes"][0]
    assert round(march_tax["amountMonth"], 4) == round(-0.33 - 0.87 - 0.51, 4)
    # CAD in PLN: -0.33 * 3.20 = -1.056
    # USD in PLN:
    #   -0.87 * 4.10 = -3.567
    #   -0.51 * 4.12 = -2.1012
    expected_pln = -1.056 + (-3.567) + (-2.1012)
    assert round(march_tax["amountPlnMonth"], 4) == round(expected_pln, 4)
