"""
Logging utility module for the agent.

This module provides simple wrappers around the standard logging library
to configure and use logging throughout the application.
"""
import logging

def setup_logging(log_file='agent.log'):
    """Configures the global logging settings.

    Args:
        log_file: The name of the file where logs will be stored.
    """
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def log_info(message):
    """Logs an informational message.

    Args:
        message: The message string to log.
    """
    logging.info(message)

def log_warning(message):
    """Logs a warning message.

    Args:
        message: The message string to log.
    """
    logging.warning(message)

def log_error(message):
    """Logs an error message.

    Args:
        message: The message string to log.
    """
    logging.error(message)

def log_debug(message):
    """Logs a debug message.

    Args:
        message: The message string to log.
    """
    logging.debug(message)