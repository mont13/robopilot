"""
MCP Server implementation for RoboPilot tools.

This module implements an MCP (Model Context Protocol) server that exposes
robot control tools to external systems, replacing the direct BeeAI tool integration.
"""

import logging

from beeai_framework.adapters.mcp.serve.server import (
    MCPServer,
    MCPServerConfig,
    MCPSettings,
)
from beeai_framework.tools import tool
from beeai_framework.tools.types import StringToolOutput
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Tool Input Models
class RobotMoveHomeInput(BaseModel):
    """Input for robot move home tool."""

    confirm_action: bool = Field(
        default=True,
        description="Confirmation that user wants to move robot to home position",
    )


class RobotPickAndPlaceInput(BaseModel):
    """Input for robot pick and place cycle tool."""

    cycles: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Number of pick and place cycles to perform (1-10)",
    )
    confirm_action: bool = Field(
        default=True,
        description="Confirmation that user wants to run pick and place cycles",
    )


class RobotGripperControlInput(BaseModel):
    """Input for robot gripper control tool."""

    operation: str = Field(description="Gripper operation: 'open', 'close', 'stop'")
    force: float = Field(
        default=50.0, ge=0.0, le=100.0, description="Gripper force percentage (0-100)"
    )
    confirm_action: bool = Field(
        default=True, description="Confirmation that user wants to control gripper"
    )


class RobotGripperLEDInput(BaseModel):
    """Input for robot gripper LED control tool."""

    operation: str = Field(description="LED operation: 'on', 'off', 'blink'")
    color: str = Field(
        default="blue",
        description="LED color: 'red', 'green', 'blue', 'yellow', 'purple', 'cyan', 'white'",
    )
    intensity: float = Field(
        default=50.0, ge=0.0, le=100.0, description="LED intensity percentage (0-100)"
    )


class RobotMoveToPositionInput(BaseModel):
    """Input for robot move to position tool."""

    position_name: str = Field(
        description="Named position to move to: 'home', 'pick', 'place', 'safe', 'maintenance'"
    )
    movement_type: str = Field(
        default="joint", description="Movement type: 'joint' or 'linear'"
    )
    speed: float = Field(
        default=50.0, ge=1.0, le=100.0, description="Movement speed percentage (1-100)"
    )


# MCP Tool Implementations
@tool
def robot_move_home_tool(input_data: RobotMoveHomeInput) -> StringToolOutput:
    """
    Move robot to home position safely.

    This tool moves the robot arm to its predefined home position,
    which is a safe, known configuration.
    """
    try:
        logger.info("MCP Tool: Moving robot to home position")

        if not input_data.confirm_action:
            return StringToolOutput(
                result="❌ Action cancelled: User confirmation required"
            )

        # Simulate robot movement (replace with actual robot control)
        result = "🏠 Robot successfully moved to home position"
        logger.info("Robot moved to home position successfully")

        return StringToolOutput(result=result)

    except Exception as e:
        error_msg = f"❌ Failed to move robot home: {str(e)}"
        logger.error(error_msg)
        return StringToolOutput(result=error_msg)


@tool
def robot_pick_and_place_cycle_tool(
    input_data: RobotPickAndPlaceInput,
) -> StringToolOutput:
    """
    Execute pick and place cycles with the robot.

    This tool performs automated pick and place operations,
    moving objects from pick location to place location.
    """
    try:
        logger.info(f"MCP Tool: Running {input_data.cycles} pick and place cycles")

        if not input_data.confirm_action:
            return StringToolOutput(
                result="❌ Action cancelled: User confirmation required"
            )

        # Simulate pick and place cycles
        results = []
        for cycle in range(input_data.cycles):
            cycle_result = f"Cycle {cycle + 1}: Pick → Place ✅"
            results.append(cycle_result)
            logger.info(f"Completed pick and place cycle {cycle + 1}")

        result = (
            f"🔄 Completed {input_data.cycles} pick and place cycles:\n"
            + "\n".join(results)
        )
        return StringToolOutput(result=result)

    except Exception as e:
        error_msg = f"❌ Failed to execute pick and place cycles: {str(e)}"
        logger.error(error_msg)
        return StringToolOutput(result=error_msg)


@tool
def robot_control_gripper_tool(
    input_data: RobotGripperControlInput,
) -> StringToolOutput:
    """
    Control robot gripper operations.

    This tool controls the robot's gripper to open, close, or stop,
    with configurable force settings.
    """
    try:
        logger.info(
            f"MCP Tool: Controlling gripper - {input_data.operation} at {input_data.force}% force"
        )

        if not input_data.confirm_action:
            return StringToolOutput(
                result="❌ Action cancelled: User confirmation required"
            )

        valid_operations = ["open", "close", "stop"]
        if input_data.operation.lower() not in valid_operations:
            return StringToolOutput(
                result=f"❌ Invalid operation. Use: {', '.join(valid_operations)}"
            )

        # Simulate gripper control
        operation_emoji = {"open": "👐", "close": "👊", "stop": "✋"}
        emoji = operation_emoji.get(input_data.operation.lower(), "🤖")

        result = f"{emoji} Gripper {input_data.operation} at {input_data.force}% force - Success"
        logger.info(f"Gripper {input_data.operation} completed successfully")

        return StringToolOutput(result=result)

    except Exception as e:
        error_msg = f"❌ Failed to control gripper: {str(e)}"
        logger.error(error_msg)
        return StringToolOutput(result=error_msg)


@tool
def robot_gripper_led_control_tool(
    input_data: RobotGripperLEDInput,
) -> StringToolOutput:
    """
    Control robot gripper LED indicators.

    This tool controls the LED lights on the robot gripper for
    visual feedback and status indication.
    """
    try:
        logger.info(
            f"MCP Tool: Controlling gripper LED - {input_data.operation} {input_data.color} at {input_data.intensity}%"
        )

        valid_operations = ["on", "off", "blink"]
        valid_colors = ["red", "green", "blue", "yellow", "purple", "cyan", "white"]

        if input_data.operation.lower() not in valid_operations:
            return StringToolOutput(
                result=f"❌ Invalid operation. Use: {', '.join(valid_operations)}"
            )

        if input_data.color.lower() not in valid_colors:
            return StringToolOutput(
                result=f"❌ Invalid color. Use: {', '.join(valid_colors)}"
            )

        # Simulate LED control
        color_emoji = {
            "red": "🔴",
            "green": "🟢",
            "blue": "🔵",
            "yellow": "🟡",
            "purple": "🟣",
            "cyan": "🔵",
            "white": "⚪",
        }
        emoji = color_emoji.get(input_data.color.lower(), "💡")

        if input_data.operation.lower() == "off":
            result = "⚫ Gripper LED turned OFF"
        elif input_data.operation.lower() == "blink":
            result = f"✨ Gripper LED blinking {input_data.color} at {input_data.intensity}% intensity"
        else:
            result = f"{emoji} Gripper LED {input_data.color} ON at {input_data.intensity}% intensity"

        logger.info(f"Gripper LED {input_data.operation} completed successfully")
        return StringToolOutput(result=result)

    except Exception as e:
        error_msg = f"❌ Failed to control gripper LED: {str(e)}"
        logger.error(error_msg)
        return StringToolOutput(result=error_msg)


@tool
def robot_move_to_position_tool(
    input_data: RobotMoveToPositionInput,
) -> StringToolOutput:
    """
    Move robot to a named position.

    This tool moves the robot to predefined named positions
    using either joint or linear movement.
    """
    try:
        logger.info(
            f"MCP Tool: Moving robot to {input_data.position_name} position via {input_data.movement_type} movement at {input_data.speed}% speed"
        )

        valid_positions = ["home", "pick", "place", "safe", "maintenance"]
        valid_movements = ["joint", "linear"]

        if input_data.position_name.lower() not in valid_positions:
            return StringToolOutput(
                result=f"❌ Invalid position. Use: {', '.join(valid_positions)}"
            )

        if input_data.movement_type.lower() not in valid_movements:
            return StringToolOutput(
                result=f"❌ Invalid movement type. Use: {', '.join(valid_movements)}"
            )

        # Simulate robot movement
        position_emoji = {
            "home": "🏠",
            "pick": "📦",
            "place": "📍",
            "safe": "🛡️",
            "maintenance": "🔧",
        }
        emoji = position_emoji.get(input_data.position_name.lower(), "🤖")

        result = f"{emoji} Robot moved to {input_data.position_name} position using {input_data.movement_type} movement at {input_data.speed}% speed"
        logger.info(f"Robot moved to {input_data.position_name} position successfully")

        return StringToolOutput(result=result)

    except Exception as e:
        error_msg = f"❌ Failed to move robot to position: {str(e)}"
        logger.error(error_msg)
        return StringToolOutput(result=error_msg)


class RoboPilotMCPServer:
    """
    MCP Server for RoboPilot robot control tools.
    """

    def __init__(self, port: int = 8001, transport: str = "sse"):
        """
        Initialize the RoboPilot MCP Server.

        Args:
            port: Port number for the server
            transport: Transport protocol ('sse' or 'stdio')
        """
        self.port = port
        self.transport = transport
        self.server = None

    def create_server(self) -> MCPServer:
        """Create and configure the MCP server with robot tools."""
        config = MCPServerConfig(
            transport=self.transport,
            name="RoboPilot MCP Server",
            instructions="This server provides robot control tools for automated manipulation tasks.",
            settings=MCPSettings(port=self.port),
        )

        server = MCPServer(config=config)

        # Register all robot tools
        robot_tools = [
            robot_move_home_tool,
            robot_pick_and_place_cycle_tool,
            robot_control_gripper_tool,
            robot_gripper_led_control_tool,
            robot_move_to_position_tool,
        ]

        server.register_many(robot_tools)
        logger.info(f"Registered {len(robot_tools)} robot tools to MCP server")

        self.server = server
        return server

    def serve(self):
        """Start the MCP server."""
        if not self.server:
            self.create_server()

        logger.info(
            f"Starting RoboPilot MCP Server on port {self.port} using {self.transport} transport"
        )
        self.server.serve()

    async def serve_async(self):
        """Start the MCP server asynchronously."""
        if not self.server:
            self.create_server()

        logger.info(
            f"Starting RoboPilot MCP Server (async) on port {self.port} using {self.transport} transport"
        )
        await self.server.serve_async()


def create_mcp_server(port: int = 8001, transport: str = "sse") -> RoboPilotMCPServer:
    """
    Create a configured RoboPilot MCP server.

    Args:
        port: Port number for the server
        transport: Transport protocol ('sse' or 'stdio')

    Returns:
        Configured RoboPilotMCPServer instance
    """
    return RoboPilotMCPServer(port=port, transport=transport)


def main():
    """Main function to run the MCP server."""
    logging.basicConfig(level=logging.INFO)

    server = create_mcp_server()
    try:
        server.serve()
    except KeyboardInterrupt:
        logger.info("MCP Server stopped by user")
    except Exception as e:
        logger.error(f"MCP Server error: {e}")


if __name__ == "__main__":
    main()
