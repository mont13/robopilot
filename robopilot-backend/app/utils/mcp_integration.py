"""
MCP (Model Context Protocol) Integration for RoboPilot.

This module provides integration with MCP servers using BeeAI framework's MCPTool.
"""

import asyncio
import logging
import os
from typing import Any, List

from beeai_framework.tools.mcp import MCPTool

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPIntegrationService:
    """Service for managing MCP server connections and tools using BeeAI framework."""

    def __init__(self):
        """Initialize the MCP integration service."""
        self._available_tools: list[Any] = []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize MCP connections and discover available tools."""
        if self._initialized:
            return

        logger.info("Initializing MCP integration service...")

        try:
            # Connect to memory server
            await self._connect_to_memory_server()
            self._initialized = True
            logger.info(
                f"MCP integration service initialized with {len(self._available_tools)} tools"
            )

        except Exception as e:
            logger.error(f"Failed to initialize MCP integration service: {e}")
            # Don't raise exception - allow system to continue without MCP tools
            self._initialized = True

    async def _connect_to_memory_server(self) -> None:
        """Connect to the memory MCP server."""
        try:
            # Create server parameters for memory server
            server_params = StdioServerParameters(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-memory"],
                env={
                    "PATH": os.getenv("PATH", ""),
                },
            )

            # Connect to the server and get tools
            try:
                async with stdio_client(server_params) as client:
                    logger.info("Connected to memory MCP server")

                    # Get tools from memory server
                    tools = await MCPTool.from_client(client)
                    self._available_tools.extend(tools)

                    logger.info(f"Retrieved {len(tools)} tools from memory server")

                    # Log tool names for debugging
                    for tool in tools:
                        tool_name = getattr(tool, "name", "unknown")
                        logger.debug(f"Available MCP tool: {tool_name}")

            except Exception as e:
                logger.error(f"Failed to connect to memory server: {e}")

        except Exception as e:
            logger.error(f"Error setting up memory server connection: {e}")

    async def get_mcp_tools(self) -> list[Any]:
        """
        Get all available tools from connected MCP servers.

        Returns:
            List of MCPTool instances available through MCP connections
        """
        if not self._initialized:
            await self.initialize()

        return self._available_tools.copy()

    def get_connection_status(self) -> dict[str, Any]:
        """Get status information about MCP connections."""
        return {
            "initialized": self._initialized,
            "total_tools": len(self._available_tools),
        }


# Global MCP integration service instance
_mcp_service: MCPIntegrationService | None = None


def get_mcp_service() -> MCPIntegrationService:
    """Get the global MCP integration service instance."""
    global _mcp_service
    if _mcp_service is None:
        _mcp_service = MCPIntegrationService()
    return _mcp_service


async def get_mcp_tools() -> list[Any]:
    """
    Get all available MCP tools.

    Returns:
        List of MCPTool instances available through MCP connections
    """
    mcp_service = get_mcp_service()
    return await mcp_service.get_mcp_tools()


async def initialize_mcp_integration() -> None:
    """Initialize the MCP integration system."""
    mcp_service = get_mcp_service()
    await mcp_service.initialize()


async def configure_mcp_servers() -> None:
    """Configure and connect to MCP servers based on configuration."""
    logger.info("Configuring MCP servers...")

    mcp_service = get_mcp_service()
    if not mcp_service._initialized:
        await mcp_service.initialize()

    # Log final status
    status = mcp_service.get_connection_status()
    total_tools = status.get("total_tools", 0)

    logger.info("MCP configuration complete:")
    logger.info(f"  - Available tools: {total_tools}")
