"""
Logging configuration for QnA Support Application.

This module sets up Loguru for both development and production use.
Logs are written to console (colorized) and files (rotated daily).
"""

import sys
from pathlib import Path
from loguru import logger

from src.core.config import get_settings


def setup_logger():
    """
    Configure application-wide logging.
    
    This function:
    1. Removes default logger (we want custom config)
    2. Adds console logging (colorized, formatted)
    3. Adds file logging (rotated, retained based on settings)
    4. Sets log level from configuration
    
    Call this ONCE at application startup.
    """
    
    settings = get_settings()
    
    # Remove default handler (Loguru adds one by default)
    logger.remove()
    
    # ============================================================================
    # CONSOLE LOGGING (for development, colorized)
    # ============================================================================
    
    logger.add(
        sink=sys.stdout,  # Print to console
        
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level> | "
            "{extra}"
        ),
        
        level=settings.log_level,  # From .env (INFO, DEBUG, etc.)
        
        colorize=True,  # Pretty colors in terminal
        
        backtrace=True,  # Show full traceback on errors
        
        diagnose=True,   # Show variable values in traceback
    )
    
    # ============================================================================
    # FILE LOGGING (for production, persisted)
    # ============================================================================
    
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)  # Create if doesn't exist
    
    logger.add(
        sink=log_dir / "app_{time:YYYY-MM-DD}.log",  # New file each day
        
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message} | "
            "{extra}"
        ),
        
        level=settings.log_level,
        
        rotation="00:00",  # Rotate at midnight
        
        retention=f"{settings.log_retention_days} days",  # Keep N days
        
        compression="zip",  # Compress old logs to save space
        
        encoding="utf-8",  # Support special characters
        
        backtrace=True,
        diagnose=True,
    )
    
    # ============================================================================
    # ERROR FILE (separate file for errors only)
    # ============================================================================
    
    logger.add(
        sink=log_dir / "errors_{time:YYYY-MM-DD}.log",
        
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message} | "
            "{extra}"
        ),
        
        level="ERROR",  # Only ERROR and CRITICAL
        
        rotation="00:00",
        retention=f"{settings.log_retention_days * 2} days",  # Keep errors longer
        compression="zip",
        backtrace=True,
        diagnose=True,
    )
    
    logger.info(
        "Logger initialized",
        log_level=settings.log_level,
        retention_days=settings.log_retention_days,
        log_directory=str(log_dir.absolute())
    )
    
    return logger


# ============================================================================
# CONVENIENCE: Pre-configured logger instance
# ============================================================================

def get_logger():
    """
    Get configured logger instance.
    
    Returns:
        Logger: Configured loguru logger
        
    Note:
        Call setup_logger() once at app startup before using this.
    """
    return logger