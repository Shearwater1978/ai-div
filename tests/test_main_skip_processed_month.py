import sys
import os
import json
import builtins
import types

# Чтобы тесты видели наши модули
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main


def create_test_csv(tmp_path, filename, statement_line):
    """Создаёт тестовый CSV отчёт с первой строкой Statement и фиктивными данными"""
    csv_file = tmp_path / filename
    csv_file.write_text(
        f"{statement_line}\n"
        "Dividends,Header,Currency\n"
        "Dividends,Data,USD,2025-03-05,TST (US0000000001) Cash Dividend USD 0.40 per Share,4.4\n"
        "Withholding Tax,Header,Currency,Date\n"
        "Withholding Tax,Data,USD,2025-03-06,TST (US0000000001),-2.12\n",
        encoding="utf-8"
    )
    return csv_file


def create_test_json(tmp_path, year, month_name):
    """Создаёт JSON с готовыми monthly_dividends и monthly_taxes для указанного месяца"""
    tax_reports_dir = tmp_path / "tax_reports"
    tax_reports_dir.mkdir(exist_ok=True)
    json_file = tax_reports_dir / f"divs_{year}.json"
    data = {
        "years": [
            {
                "year": year,
                "monthly_dividends": [{"month": month_name, "amountMonth": 10.0, "amountPlnMonth": 40.0}],
                "monthly_taxes": [{"month": month_name, "amountMonth": -5.0, "amountPlnMonth": -20.0}],
                "dividends": [],
                "taxes": [],
                "fees": []
            }
        ]
    }
    json_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return json_file


def test_main_skips_processed_month(monkeypatch, tmp_path):
    # Создаём тестовые файлы
    csv_filename = "U12345678_202503_202503.csv"
    csv_file = tmp_path / csv_filename
    csv_file.write_text(
        'Statement,Data,Period,"March 1, 2025 - March 31, 2025"\n'
        "Dividends,Header,Currency\n"
        "Dividends,Data,USD,2025-03-05,TST (US0000000001) Cash Dividend USD 0.40 per Share,4.4\n"
        "Withholding Tax,Header,Currency,Date\n"
        "Withholding Tax,Data,USD,2025-03-06,TST (US0000000001),-2.12\n",
        encoding="utf-8"
    )

    tax_reports_dir = tmp_path / "tax_reports"
    tax_reports_dir.mkdir(exist_ok=True)
    json_file = tax_reports_dir / "divs_2025.json"
    json_data = {
        "years": [
            {
                "year": "2025",
                "monthly_dividends": [{"month": "march", "amountMonth": 10.0, "amountPlnMonth": 40.0}],
                "monthly_taxes": [{"month": "march", "amountMonth": -5.0, "amountPlnMonth": -20.0}],
                "dividends": [],
                "taxes": [],
                "fees": []
            }
        ]
    }
    json_file.write_text(json.dumps(json_data), encoding="utf-8")

    # Подменяем process_broker_csv на заглушку
    monkeypatch.setattr(main, "process_broker_csv", lambda file: (_ for _ in ()).throw(
        AssertionError("process_broker_csv should not be called")
    ))

    # Подменяем glob.glob чтобы вернуть только наш CSV
    monkeypatch.setattr(main.glob, "glob", lambda pattern: [str(csv_file)])

    # Запускаем run_main в режиме all
    main.run_main(["all"])
