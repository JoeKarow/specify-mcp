"""
Main MCP server initialization for SpecKit.

This module sets up the FastMCP server with stdio transport for communication with Claude.
It provides centralized spec-kit functionality including feature specification, planning,
task breakdown, and project management through MCP tools and resources.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP, Resource
from pydantic import BaseModel, Field

from speckit_mcp import __version__

# Configure logging
def setup_logging() -> logging.Logger:
    """
    Set up structured logging for the MCP server.

    Logs are written to ~/.specify-mcp/logs/ with rotation and debug levels.

    Returns:
        Configured logger instance
    """
    # Create logs directory
    log_dir = Path.home() / ".specify-mcp" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"speckit_mcp_{timestamp}.log"

    # Configure logger
    logger = logging.getLogger("speckit_mcp")
    logger.setLevel(logging.DEBUG)

    # File handler for debug logging
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler for warnings and errors only (to avoid stdio interference)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter(
        '%(levelname)s - %(name)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Initialize logger
logger = setup_logging()


def create_server() -> FastMCP:
    """
    Create and configure the FastMCP server instance.

    Returns:
        Configured FastMCP server ready for stdio communication
    """
    logger.info(f"Initializing SpecKit MCP server v{__version__}")

    # Create FastMCP server with metadata
    mcp = FastMCP(
        name="speckit-mcp",
        version=__version__,
        instructions="Centralized MCP server for spec-kit functionality including feature specification, planning, and task breakdown"
    )

    # Log server metadata
    logger.debug(f"Server metadata: name=speckit-mcp, version={__version__}")

    # Register tools
    logger.debug("Registering MCP tools...")

    # Import and register all MCP tools
    from speckit_mcp.tools import (
        specify,
        plan,
        tasks,
        initialize_project,
        get_context
    )

    # Register each tool with the MCP server
    # T031 - Specify tool for creating feature specifications
    mcp.tool(specify)
    logger.debug("Registered tool: specify")

    # T032 - Plan tool for generating implementation plans
    mcp.tool(plan)
    logger.debug("Registered tool: plan")

    # T033 - Tasks tool for creating task breakdowns
    mcp.tool(tasks)
    logger.debug("Registered tool: tasks")

    # T034 - Initialize tool for project setup
    mcp.tool(initialize_project)
    logger.debug("Registered tool: initialize_project")

    # T035 - Context tool for phase-specific documentation
    mcp.tool(get_context)
    logger.debug("Registered tool: get_context")

    # Register resources (T036-T039)
    logger.debug("Registering MCP resources...")

    # Import resource handlers
    from speckit_mcp.resources.templates import serve_template, list_template_resources
    from speckit_mcp.resources.documentation import serve_documentation, list_documentation_resources
    from speckit_mcp.resources.configuration import serve_configuration, list_configuration_resources
    from speckit_mcp.resources.workflows import serve_workflow, list_workflow_resources

    # T036 - Register template resources
    @mcp.resource("mcp://speckit/templates/{template_type}")
    async def get_template(uri: str) -> Resource:
        """Serve template resources."""
        return await serve_template(uri)
    logger.debug("Registered resource: templates")

    # T037 - Register documentation resources
    @mcp.resource("mcp://speckit/docs/{category}/{name}")
    async def get_documentation(uri: str) -> Resource:
        """Serve documentation resources."""
        return await serve_documentation(uri)
    logger.debug("Registered resource: documentation")

    # T038 - Register configuration resources
    @mcp.resource("mcp://speckit/config/{type}/{name}")
    async def get_configuration(uri: str) -> Resource:
        """Serve configuration resources."""
        return await serve_configuration(uri)
    logger.debug("Registered resource: configuration")

    # T039 - Register workflow resources
    @mcp.resource("mcp://speckit/workflows/{workflow_name}")
    async def get_workflow(uri: str) -> Resource:
        """Serve workflow resources."""
        return await serve_workflow(uri)
    logger.debug("Registered resource: workflows")

    logger.info("Server initialization complete")
    return mcp


def run_server() -> None:
    """
    Run the MCP server with stdio transport.

    This function sets up the server and runs it directly.
    FastMCP manages its own event loop internally.
    """
    logger.info("Starting SpecKit MCP server...")

    try:
        # Create server instance
        server = create_server()

        # Run with stdio transport (default for FastMCP)
        # FastMCP.run() handles its own event loop
        logger.info("Starting stdio transport...")
        server.run()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down gracefully...")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise
    finally:
        logger.info("Server shutdown complete")


def main() -> None:
    """
    Main entry point for the MCP server.

    This function runs the server directly without creating a separate event loop,
    as FastMCP manages its own asyncio event loop internally.
    """
    logger.info("=== SpecKit MCP Server Starting ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Server version: {__version__}")
    logger.info(f"Log location: {Path.home() / '.specify-mcp' / 'logs'}")

    try:
        # Run the server directly (FastMCP handles event loop)
        run_server()
    except KeyboardInterrupt:
        # Handle graceful shutdown
        logger.info("Server interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()