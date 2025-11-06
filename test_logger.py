"""
Test script to verify logging configuration.
"""

from src.utils.loggger import setup_logger, get_logger

# Initialize logging (do this ONCE at app startup)
setup_logger()

# Get logger instance
logger = get_logger()

# Test different log levels
def test_log_levels():
    """Test all log levels."""
    logger.debug("This is a DEBUG message - only in development")
    logger.info("This is an INFO message - normal operation")
    logger.warning("This is a WARNING - something unexpected")
    logger.error("This is an ERROR - something failed")
    logger.critical("This is CRITICAL - system-level failure!")


def test_structured_logging():
    """Test structured data in logs."""
    logger.info(
        "User query classified",
        user_id="user123",
        query="My payment failed",
        category="Billing",
        confidence=0.92,
        method="rule-based"
    )


def test_exception_logging():
    """Test exception capturing."""
    try:
        # Intentional error
        result = 10 / 0
    except ZeroDivisionError:
        logger.exception("Division by zero occurred")  # Logs full traceback


def test_context_logging():
    """Test adding context to logs."""
    # Bind context that appears in all subsequent logs
    context_logger = logger.bind(request_id="req-456", user="alice")
    
    context_logger.info("Processing request")
    context_logger.info("Request complete")
    # Both logs will include request_id and user automatically!


if __name__ == "__main__":
    print("=== Testing Log Levels ===")
    test_log_levels()
    
    print("\n=== Testing Structured Logging ===")
    test_structured_logging()
    
    print("\n=== Testing Exception Logging ===")
    test_exception_logging()
    
    print("\n=== Testing Context Logging ===")
    test_context_logging()
    
    print("\n✓ Check data/logs/ for log files!")