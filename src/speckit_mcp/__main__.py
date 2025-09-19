"""
Entry point for running the SpecKit MCP server as a module.

This module enables execution via: python -m speckit_mcp

It provides proper command-line argument handling and graceful shutdown on interruption.
FastMCP manages its own asyncio event loop internally.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from speckit_mcp import __version__
from speckit_mcp.server import main as server_main, setup_logging

# Set up module-level logger
logger = setup_logging()


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for the MCP server.

    Returns:
        Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        prog="speckit-mcp",
        description="SpecKit MCP Server - Centralized spec-kit functionality via Model Context Protocol",
        epilog="For more information, see: https://github.com/spec-kit/specify-mcp"
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program version and exit"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)"
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Path to custom server configuration file (optional)"
    )

    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode (for development and debugging)"
    )

    return parser.parse_args()


def configure_logging(level: str) -> None:
    """
    Configure the logging level for the application.

    Args:
        level: Logging level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Update root logger level
    root_logger = logging.getLogger("speckit_mcp")
    root_logger.setLevel(numeric_level)

    # Update all handlers
    for handler in root_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            # File handler always gets DEBUG for comprehensive logs
            handler.setLevel(logging.DEBUG)
        elif isinstance(handler, logging.StreamHandler):
            # Console handler respects the requested level
            handler.setLevel(numeric_level)

    logger.info(f"Logging level set to: {level}")


def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Custom exception handler for uncaught exceptions.

    Args:
        exc_type: Exception type
        exc_value: Exception value
        exc_traceback: Exception traceback
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # Handle Ctrl+C gracefully
        logger.info("Received keyboard interrupt, shutting down...")
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )


def main() -> None:
    """
    Main entry point for the module execution.

    This function handles argument parsing, logging configuration,
    and server startup with proper error handling.
    """
    # Set custom exception handler
    sys.excepthook = handle_exception

    # Parse command-line arguments
    args = parse_arguments()

    # Configure logging based on arguments
    configure_logging(args.log_level)

    # Log startup information
    logger.info("=" * 60)
    logger.info("SpecKit MCP Server Starting")
    logger.info(f"Version: {__version__}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Log Level: {args.log_level}")

    if args.config:
        logger.info(f"Config File: {args.config}")

    if args.test_mode:
        logger.info("Running in TEST MODE")

    logger.info("=" * 60)

    try:
        # Store config path for server to use (if provided)
        if args.config:
            import os
            os.environ["SPECKIT_CONFIG_PATH"] = str(args.config.absolute())

        # Store test mode flag
        if args.test_mode:
            import os
            os.environ["SPECKIT_TEST_MODE"] = "1"

        # Run the server
        server_main()

    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        sys.exit(0)
    except SystemExit as e:
        # Propagate system exit
        logger.info(f"System exit with code: {e.code}")
        raise
    except Exception as e:
        logger.critical(f"Fatal error during server execution: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Server process terminated")


if __name__ == "__main__":
    main()