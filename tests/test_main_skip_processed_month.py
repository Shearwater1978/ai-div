import sys
import os
import json
import main  # импортируем основной модуль

def test_main_skips_processed_month(monkeypatch, tmp_path):
    """
    Проверка:
    main.py пропускает обработку CSV за месяц,
    если в JSON этого года уже есть monthly_dividends и monthly_taxes за этот месяц.
    """

    # Переносим рабочий каталог в tmp_path, чтобы tax_reports искался именно здесь
    cwd = os.getcwd()
    os.chdir(tmp_path)

    # 1. Создаём фиктивный CSV с обезличенным идентификатором клиента
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

    # 2. Создаём JSON, в котором март 2025 уже обработан
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

    # 3. Подменяем glob.glob, чтобы вернуть только наш CSV
    monkeypatch.setattr(main.glob, "glob", lambda pattern: [str(csv_file)])

    # 4. Подменяем process_broker_csv на заглушку, которая упадёт если вызовется
    monkeypatch.setattr(main, "process_broker_csv", lambda file: (_ for _ in ()).throw(
        AssertionError("process_broker_csv should not be called")
    ))

    # 5. Запускаем run_main в режиме "all"
    main.run_main(["all"])

    # Возвращаемся в изначальную рабочую директорию
    os.chdir(cwd)
