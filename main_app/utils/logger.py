"""
Logger Module

Comprehensive logging system for Eye Tracker Research Software.
Logs all activities with timestamps, levels, and detailed information.

Author: Kahlil Gibran Al Zulmi
NRP: 5049221015
Medical Technology Study Program - ITS
"""

import logging
import os
from datetime import datetime
from pathlib import Path


# Global logger instance
_logger = None
_log_dir = None


def init_logger(log_dir="Logs"):
    """
    Initialize the logging system.
    
    Args:
        log_dir (str): Directory to store log files
        
    Returns:
        logging.Logger: Configured logger instance
    """
    global _logger, _log_dir
    
    # Create log directory if it doesn't exist
    _log_dir = log_dir
    os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    _logger = logging.getLogger('EyeTrackerLogger')
    _logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    _logger.handlers = []
    
    # Create log filename with timestamp
    log_filename = f"eyetracker_{datetime.now().strftime('%Y%m%d')}.log"
    log_path = os.path.join(log_dir, log_filename)
    
    # File handler (all levels)
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(funcName)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    _logger.addHandler(file_handler)
    
    # Console handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    _logger.addHandler(console_handler)
    
    _logger.info("="*60)
    _logger.info("Eye Tracker Research Software - Session Started")
    _logger.info("="*60)
    
    return _logger


def get_logger():
    """
    Get the global logger instance.
    
    Returns:
        logging.Logger: Logger instance
    """
    global _logger
    if _logger is None:
        init_logger()
    return _logger


def log_info(message):
    """
    Log informational message.
    
    Args:
        message (str): Message to log
    """
    logger = get_logger()
    logger.info(message)


def log_warning(message):
    """
    Log warning message.
    
    Args:
        message (str): Warning message
    """
    logger = get_logger()
    logger.warning(message)


def log_error(message, exception=None):
    """
    Log error message with optional exception details.
    
    Args:
        message (str): Error message
        exception (Exception, optional): Exception object
    """
    logger = get_logger()
    if exception:
        logger.error(f"{message} | Exception: {str(exception)}", exc_info=True)
    else:
        logger.error(message)


def log_debug(message):
    """
    Log debug message (only in log file).
    
    Args:
        message (str): Debug message
    """
    logger = get_logger()
    logger.debug(message)


def log_session_start(feature, metadata):
    """
    Log the start of a session for a feature.
    
    Args:
        feature (str): Feature name (detection/game/stimulus)
        metadata (dict): Session metadata
    """
    logger = get_logger()
    logger.info("-"*60)
    logger.info(f"SESSION START: {feature.upper()}")
    logger.info(f"Timestamp: {metadata.get('timestamp', 'N/A')}")
    for key, value in metadata.items():
        if key != 'timestamp':
            logger.info(f"  {key}: {value}")
    logger.info("-"*60)


def log_session_end(feature, metadata):
    """
    Log the end of a session for a feature.
    
    Args:
        feature (str): Feature name (detection/game/stimulus)
        metadata (dict): Session results metadata
    """
    logger = get_logger()
    logger.info("-"*60)
    logger.info(f"SESSION END: {feature.upper()}")
    logger.info(f"Duration: {metadata.get('duration', 'N/A')}")
    logger.info(f"Status: {metadata.get('status', 'N/A')}")
    for key, value in metadata.items():
        if key not in ['duration', 'status']:
            logger.info(f"  {key}: {value}")
    logger.info("-"*60)


def get_log_history(days=7):
    """
    Get log file history for the past N days.
    
    Args:
        days (int): Number of days to look back
        
    Returns:
        list: List of tuples (date, filepath)
    """
    global _log_dir
    if _log_dir is None:
        _log_dir = "Logs"
    
    log_files = []
    log_path = Path(_log_dir)
    
    if not log_path.exists():
        return log_files
    
    for log_file in log_path.glob("eyetracker_*.log"):
        log_files.append((log_file.stem, str(log_file)))
    
    # Sort by date (newest first)
    log_files.sort(reverse=True)
    
    return log_files[:days] if days > 0 else log_files


def close_logger():
    """Close and cleanup logger handlers."""
    global _logger
    if _logger:
        _logger.info("="*60)
        _logger.info("Eye Tracker Research Software - Session Ended")
        _logger.info("="*60)
        
        handlers = _logger.handlers[:]
        for handler in handlers:
            handler.close()
            _logger.removeHandler(handler)
        _logger = None


if __name__ == "__main__":
    # Test the logger
    init_logger()
    log_info("Logger test: INFO level")
    log_warning("Logger test: WARNING level")
    log_debug("Logger test: DEBUG level")
    
    try:
        raise ValueError("Test exception")
    except Exception as e:
        log_error("Logger test: ERROR level", e)
    
    log_session_start("detection", {
        "timestamp": datetime.now().isoformat(),
        "video": "test.mp4",
        "method": "hough"
    })
    
    log_session_end("detection", {
        "duration": "10.5s",
        "status": "success",
        "frames_processed": 600
    })
    
    close_logger()
    print("Logger test complete. Check Logs/ directory.")
