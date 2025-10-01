import logging

def setup_logger():
    """
    Configure logger to output to file and console.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("process.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()

def log_module_call(module_name: str):
    logger.info(f"Module called: {module_name}")

def log_file_action(action: str, file_path: str):
    logger.info(f"{action} file: {file_path}")

def log_event(message: str):
    logger.info(message)
