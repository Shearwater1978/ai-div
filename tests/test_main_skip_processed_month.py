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
    """
    Проверка:
    - main.py пропускает обработку CSV за месяц, если в JSON этого года уже есть monthly_dividends и monthly_taxes за этот месяц.
    """

    # Подменим рабочий каталог на tmp_path
    cwd = os.getcwd()
    os.chdir(tmp_path)

    # 1. Создаём фиктивный CSV за март 2025
    csv_filename = "U123456_202503_202503.csv"
    statement_line = 'Statement,Data,Period,"March 1, 2025 - March 31, 2025"'
    create_test_csv(tmp_path, csv_filename, statement_line)

    # 2. Создаём JSON, в котором март 2025 уже обработан
    create_test_json(tmp_path, "2025", "march")

    # 3. Подменим process_broker_csv на заглушку, которая упадёт если вызовется
    def fake_process_broker_csv(file):
        raise AssertionError(f"process_broker_csv was called for {file}, but should have been skipped")

    monkeypatch.setattr(main, "process_broker_csv", fake_process_broker_csv)

    # 4. Запускаем main.py как при вызове all
    sys.argv = ["main.py", "all"]

    # Подменим glob.glob, чтобы вернуть наш тестовый CSV
    monkeypatch.setattr(os, "getcwd", lambda: str(tmp_path))
    monkeypatch.setattr(main.glob, "glob", lambda pattern: [csv_filename])

    # Запустим main.py
    main.__main__.__globals__["__name__"] = "__main__"  # Убеждаемся, что код в main запустится
    main.main()

    # Возвращаем рабочий каталог
    os.chdir(cwd)
