# utils/logging/config.py

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
from datetime import datetime

def setup_logging(log_dir: Path, debug: bool = False) -> Path:
    """
    Set up application-wide logging configuration.
    
    Args:
        log_dir: Directory to store log files
        debug: Whether to enable debug logging
        
    Returns:
        Path to current log file
    """
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"app_{timestamp}.log"
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Remove any existing handlers and add new ones
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log startup information
    root_logger.info("Logging initialized")
    root_logger.info(f"Log file: {log_file}")
    root_logger.info(f"Python version: {sys.version}")
    
    return log_file