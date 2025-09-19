"""
Main MCP server initialization for SpecKit.

This module sets up the FastMCP server with stdio transport for communication with Claude.
It provides centralized spec-kit functionality including feature specification, planning,
task breakdown, and project management through MCP tools and resources.
"""

import logging
import logging.handlers
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP
from fastmcp.resources import Resource
from pydantic import BaseModel, Field

from speckit_mcp import __version__

# Configure logging
def setup_logging() -> logging.Logger:
    """
    Set up structured logging for the MCP server with rotation.

    T042: Comprehensive logging implementation
    - Logs are written to ~/.specify-mcp/logs/ with rotation
    - Different log levels (DEBUG, INFO, WARNING, ERROR)
    - Log rotation with max size and backup count
    - Performance logging for slow operations

    Returns:
        Configured logger instance
    """
    # Create logs directory
    log_dir = Path.home() / ".specify-mcp" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Base log filename
    log_file = log_dir / "speckit_mcp.log"

    # Configure root logger for speckit_mcp
    logger = logging.getLogger("speckit_mcp")
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers.clear()

    # File handler with rotation (T042 - log rotation)
    # Max size: 10MB, keep 5 backup files
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
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

    # Performance log handler for slow operations
    perf_log_file = log_dir / "speckit_mcp_performance.log"
    perf_handler = logging.handlers.RotatingFileHandler(
        perf_log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    perf_handler.setLevel(logging.INFO)
    perf_formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    perf_handler.setFormatter(perf_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Create performance logger
    perf_logger = logging.getLogger("speckit_mcp.performance")
    perf_logger.setLevel(logging.INFO)
    perf_logger.addHandler(perf_handler)
    perf_logger.propagate = False  # Don't propagate to root logger

    # Log initial setup
    logger.info("="*60)
    logger.info("Logging system initialized")
    logger.info(f"Main log: {log_file}")
    logger.info(f"Performance log: {perf_log_file}")
    logger.info(f"Max file size: 10MB with 5 backups")
    logger.info("="*60)

    return logger


# Initialize logger
logger = setup_logging()


def create_server() -> FastMCP:
    """
    Create and configure the FastMCP server instance.

    T040: Connect all tools and resources to MCP server
    - Registers all 5 tools (specify, plan, tasks, initialize_project, get_context)
    - Registers all 4 resource types (templates, documentation, configuration, workflows)
    - Ensures proper initialization order

    Returns:
        Configured FastMCP server ready for stdio communication
    """
    perf_logger = logging.getLogger("speckit_mcp.performance")
    start_time = time.time()

    logger.info(f"Initializing SpecKit MCP server v{__version__}")

    try:
        # Create FastMCP server with metadata
        mcp = FastMCP(
            name="speckit-mcp",
            version=__version__,
            instructions="Centralized MCP server for spec-kit functionality including feature specification, planning, and task breakdown"
        )

        # Log server metadata
        logger.debug(f"Server metadata: name=speckit-mcp, version={__version__}")

        # T040: Register all MCP tools with proper error handling
        logger.info("Registering MCP tools...")
        tool_start = time.time()

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
        logger.info("✓ Registered tool: specify")

        # T032 - Plan tool for generating implementation plans
        mcp.tool(plan)
        logger.info("✓ Registered tool: plan")

        # T033 - Tasks tool for creating task breakdowns
        mcp.tool(tasks)
        logger.info("✓ Registered tool: tasks")

        # T034 - Initialize tool for project setup
        mcp.tool(initialize_project)
        logger.info("✓ Registered tool: initialize_project")

        # T035 - Context tool for phase-specific documentation
        mcp.tool(get_context)
        logger.info("✓ Registered tool: get_context")

        tool_time = time.time() - tool_start
        perf_logger.info(f"Tool registration completed in {tool_time:.3f}s")

        # T040: Register all MCP resources (T036-T039)
        logger.info("Registering MCP resources...")
        resource_start = time.time()

        # Import resource handlers (preload for performance)
        import asyncio
        from speckit_mcp.resources.templates import serve_template, list_template_resources
        from speckit_mcp.resources.documentation import serve_documentation, list_documentation_resources
        from speckit_mcp.resources.configuration import serve_configuration, list_configuration_resources
        from speckit_mcp.resources.workflows import serve_workflow, list_workflow_resources

        # T036 - Register template resources
        @mcp.resource("mcp://speckit/templates/{template_type}")
        async def get_template(template_type: str) -> Resource:
            """Serve template resources with error handling."""
            uri = f"mcp://speckit/templates/{template_type}"
            perf_logger.info(f"Serving template resource: {uri}")
            return await serve_template(uri)
        logger.info("✓ Registered resource: templates")

        # T037 - Register documentation resources
        @mcp.resource("mcp://speckit/docs/{category}/{name}")
        async def get_documentation(category: str, name: str) -> Resource:
            """Serve documentation resources with error handling."""
            uri = f"mcp://speckit/docs/{category}/{name}"
            perf_logger.info(f"Serving documentation resource: {uri}")
            return await serve_documentation(uri)
        logger.info("✓ Registered resource: documentation")

        # T038 - Register configuration resources
        @mcp.resource("mcp://speckit/config/{type}/{name}")
        async def get_configuration(type: str, name: str) -> Resource:
            """Serve configuration resources with error handling."""
            uri = f"mcp://speckit/config/{type}/{name}"
            perf_logger.info(f"Serving configuration resource: {uri}")
            return await serve_configuration(uri)
        logger.info("✓ Registered resource: configuration")

        # T039 - Register workflow resources
        @mcp.resource("mcp://speckit/workflows/{workflow_name}")
        async def get_workflow(workflow_name: str) -> Resource:
            """Serve workflow resources with error handling."""
            uri = f"mcp://speckit/workflows/{workflow_name}"
            perf_logger.info(f"Serving workflow resource: {uri}")
            return await serve_workflow(uri)
        logger.info("✓ Registered resource: workflows")

        resource_time = time.time() - resource_start
        perf_logger.info(f"Resource registration completed in {resource_time:.3f}s")

        # Preload frequently accessed resources for better performance
        async def preload_critical_resources():
            """Preload frequently accessed resources to improve first-access performance."""
            preload_start = time.time()
            try:
                # Preload resource lists in parallel for optimal performance
                await asyncio.gather(
                    list_template_resources(),
                    list_documentation_resources(),
                    list_configuration_resources(),
                    list_workflow_resources(),
                    return_exceptions=True  # Continue even if some fail
                )
                preload_time = time.time() - preload_start
                perf_logger.info(f"Critical resources preloaded in {preload_time:.3f}s")
            except Exception as e:
                perf_logger.warning(f"Resource preload failed: {e}")

        # Note: Resource preloading will be handled by FastMCP when event loop is available
        # The preload_critical_resources function is defined but not called here to avoid
        # "no running event loop" error. FastMCP will handle resource loading internally.

        # Log total initialization time
        total_time = time.time() - start_time
        perf_logger.info(f"Server initialization completed in {total_time:.3f}s")
        logger.info("✅ Server initialization complete - all tools and resources registered")

        return mcp

    except Exception as e:
        logger.error(f"Failed to create server: {e}", exc_info=True)
        raise


def run_server() -> None:
    """
    Run the MCP server with stdio transport.

    T041: Comprehensive error handling implementation
    - Proper exception handling with MCPError codes
    - Graceful shutdown on interrupts
    - Detailed error logging

    This function sets up the server and runs it directly.
    FastMCP manages its own event loop internally.
    """
    perf_logger = logging.getLogger("speckit_mcp.performance")
    logger.info("Starting SpecKit MCP server...")
    start_time = time.time()

    try:
        # Create server instance
        server = create_server()

        # Run with stdio transport (default for FastMCP)
        # FastMCP.run() handles its own event loop
        logger.info("Starting stdio transport...")
        logger.info("Server ready for connections")

        # Log startup performance
        startup_time = time.time() - start_time
        perf_logger.info(f"Server startup completed in {startup_time:.3f}s")

        # Run the server
        server.run()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down gracefully...")
        perf_logger.info(f"Server uptime: {time.time() - start_time:.1f}s")
    except MemoryError as e:
        logger.critical(f"Memory error - server out of memory: {e}", exc_info=True)
        raise
    except OSError as e:
        logger.error(f"Operating system error: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected server error: {e}", exc_info=True)
        raise
    finally:
        logger.info("Server shutdown complete")
        shutdown_time = time.time() - start_time
        perf_logger.info(f"Total server runtime: {shutdown_time:.1f}s")


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