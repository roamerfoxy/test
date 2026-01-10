"""
This module provides a logging setup utility for creating and managing loggers.

It includes functions to set up loggers with both file and stream handlers,
as well as a convenience function to retrieve loggers by name.

The module creates a 'logs' directory if it doesn't exist and uses RotatingFileHandler
to manage log file sizes and backups.

Functions:
    setup_logger: Creates and configures a logger with file and stream handlers.
    get_logger: Retrieves a logger by name or returns the default logger.

Variables:
    default_logger: A pre-configured default logger instance.
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(name, log_file, level=logging.DEBUG):
    """Function to setup as many loggers as you want"""

    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, log_file), maxBytes=2000000, backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.ERROR)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


# Create a default logger
default_logger = setup_logger("default", "default.log")


def get_logger(name=None):
    """Get a logger by name, or return the default logger if no name is provided"""
    if name:
        return setup_logger(name, f"{name}.log")
    return default_logger
