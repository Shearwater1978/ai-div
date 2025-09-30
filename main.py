import sys
from broker_report_processor import process_broker_csv
from logger_module import log_module_call

if __name__ == "__main__":
    log_module_call("main")

    if len(sys.argv) < 2:
        print("Usage: python main.py <CSV_FILENAME>")
        sys.exit(1)

    reportFileName = sys.argv[1]
    process_broker_csv(reportFileName)
