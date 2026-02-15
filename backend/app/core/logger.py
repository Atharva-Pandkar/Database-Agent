import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        
        # Add correlation_id if available in extras
        if hasattr(record, 'correlation_id'):
            log_record['correlation_id'] = record.correlation_id
        
        # Add component if available in extras
        if hasattr(record, 'component'):
            log_record['component'] = record.component
        
        # Add extras if available
        if hasattr(record, 'extras'):
            log_record['extras'] = record.extras

class CustomLogger:
    def __init__(self, name: str = "app"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = LOGS_DIR / "app.log"
        file_handler = logging.FileHandler(log_file)
        
        # Create formatter
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
    
    def _log(self, level: int, message: str, component: str, extras: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> None:
        """Internal method to handle logging with extra parameters."""
        extra = {
            'component': component,
            'extras': extras or {},
        }
        if correlation_id:
            extra['correlation_id'] = correlation_id
            
        self.logger.log(level, message, extra=extra)
    
    def info(self, message: str, component: str, extras: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> None:
        self._log(logging.INFO, message, component, extras, correlation_id)
    
    def error(self, message: str, component: str, extras: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> None:
        self._log(logging.ERROR, message, component, extras, correlation_id)
    
    def debug(self, message: str, component: str, extras: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> None:
        self._log(logging.DEBUG, message, component, extras, correlation_id)
    
    def warning(self, message: str, component: str, extras: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None) -> None:
        self._log(logging.WARNING, message, component, extras, correlation_id)

# Create a global logger instance
logger = CustomLogger()
