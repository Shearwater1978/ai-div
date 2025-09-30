import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logger_module import log_module_call, log_file_action, log_event

def test_logger_functions(caplog):
    # Захватываем все сообщения уровня INFO
    caplog.set_level("INFO")
    
    log_module_call("test_module")
    log_file_action("Reading", "file.txt")
    log_event("Custom event")
    
    messages = [rec.message for rec in caplog.records]
    
    # Проверяем, что в логах есть наши строки
    assert any("test_module" in msg for msg in messages)
    assert any("Reading file.txt" in msg or "Reading" in msg for msg in messages)
    assert any("Custom event" in msg for msg in messages)
