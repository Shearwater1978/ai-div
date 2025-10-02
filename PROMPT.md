Учёт дивидендов и налогов в Польше

Привет, я хочу написать код на Python 3, который будет соответствовать требованиям:

Общие требования:
Язык: Python, версия 3.
На вход данные загружаются из CSV-файлов, выгружаемых вручную из портала Брокера:
MTM Summary → Period (Custom...) → Select Month → CSV → Download.
Код должен поддерживать пакетную обработку нескольких отчётов сразу.
Имя файла отчёта соответствует шаблону: U<номер_счёта>_<ГГГГММ>_<ГГГГММ>.csv
Обработанные данные сохраняются в JSON (tax_reports/divs_YEAR.json).

Формат JSON (пример):
```json
{
  "years": [
    {
      "year": "YEAR",
      "rates": [
        {
          "currency": "USD",
          "rate": [
            {
              "date": "EFFECTIVEDATE",
              "mid": "CURRENCY_EXCHANGE_RATE"
            }
          ]
        },
        {
          "currency": "CAD",
          "rate": [
            {
              "date": "EFFECTIVEDATE",
              "mid": "CURRENCY_EXCHANGE_RATE"
            }
          ]
        }
      ],
      "dividends": [
        {
          "ticker": "TICKER_NAME",
          "dividend": [
            {
              "amount": "TICKER_DIV_AMOUNT",
              "currency": "TICKER_DIV_CURRENCY",
              "date": "TICKER_DIV_DATE",
              "exchangeRate": "TICKER_DIV_CURRENCY_EXCHANGE_RATE",
              "effectiveDate": "TICKER_DIV_CURRENCY_EXCHANGE_DATE",
              "amountPln": "TICKER_DIV_AMOUNT_PLN"
            }
          ]
        }
      ],
      "taxes": [
        {
          "ticker": "TICKER_NAME",
          "tax": [
            {
              "amount": "TICKER_TAX_AMOUNT",
              "currency": "TICKER_TAX_CURRENCY",
              "date": "TICKER_TAX_DATE",
              "code": "TICKER_TAX_CODE",
              "exchangeRate": "TICKER_TAX_CURRENCY_EXCHANGE_RATE",
              "effectiveDate": "TICKER_TAX_CURRENCY_EXCHANGE_DATE",
              "amountPln": "TICKER_TAX_AMOUNT_PLN"
            }
          ]
        }
      ],
      "fees": [],
      "monthly_dividends": [],
      "monthly_taxes": []
    }
  ]
}
```

Модули проекта:

1. Модуль логгирования

- Логирует запуск каждого модуля.
- Логирует чтение и запись файлов.
- Логирует ключевые события (дубли, пропуски, ошибки парсинга, конвертации валют).

2. Модуль "Обработка даты"

- Получает строку Statement,Data,Period,"January 1, 2025 - January 31, 2025".
- Возвращает year = "2025", fromDate = "2025-01-01", toDate = "2025-01-31".

3. Модуль "Курс обмена"

- Получает словарь:
```json
{
  "fromDate": "YYYY-MM-DD",
  "toDate": "YYYY-MM-DD",
  "currencies": ["USD","CAD", ...]
}
```
- Для каждой валюты делает запрос:
```txt
https://api.nbp.pl/api/exchangerates/rates/a/{currency}/{fromDate}/{toDate}?format=json
```
- Возвращает структуру rates со всеми effectiveDate и mid.

4. Модуль "Обработка дивиденда"
- Принимает строку Dividends,Data,...
- Поддерживает тикеры с пробелом перед скобкой (MGA (CA...)).
- Из RATES берёт mid и effectiveDate для валюты и даты:
  - Если точной даты нет — берёт ближайший предыдущий день.
- Считает amountPln = amount * mid.
- Проверка дубля: уникальность по (ticker, date, amount, currency).

5. Модуль "Добавление дивиденда"
- Добавляет DIV_NEW в JSON (в год → dividends).
- Если тикер уже есть → добавляет запись в его список.
- Если тикера нет → создаёт новый объект.

6. Модуль "Обработка налога"
- Принимает строку Withholding Tax,Data,...
- Поддерживает тикеры с пробелом.
- Проверка года:
  - Если tax_year не равно YEAR — сохранить налоговую строку в tax_reports/tax_skipped_YEAR.csv (без добавления в taxes).
  - Если tax_year равно YEAR — добавлять налог в JSON, независимо от того, входит ли дата налога в диапазон fromDate–toDate.
- Если год совпадает — добавляет налог, даже если дата вне диапазона fromDate/toDate.
- Считает amountPln по курсу.

7. Модуль "Добавление налога"
- Добавляет в JSON аналогично дивидендам.

8. Модуль "Месячный итог — dividends"
- Считает:
  - amountMonth в USD, конвертируя выплаты из других валют в USD по курсу (mid).
  - amountPlnMonth для всех валют в PLN.
- Если месяц уже есть в monthly_dividends, пропускает добавление.

9. Модуль "Месячный итог — taxes"
- Считает аналогично дивидендам.
- Суммирует только налоги месяца (fromDate/toDate), даже если JSON содержит налоги с другими датами.

10. Основной скрипт (main.py)
- Может обработать один файл или все файлы в текущей папке (python main.py all).
- При пакетной обработке проверяет в JSON за год наличие monthly_* за этот месяц — если есть → пропускает файл.
- После обработки копирует CSV в reports/div_fromDate_toDate.csv.
