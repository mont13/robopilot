# RoboPilot Tools MCP Server

This MCP server provides core robot control tools for the RoboPilot system. It exposes robot manipulation capabilities through the Model Context Protocol, allowing external systems to control robotic operations safely and efficiently.

## Overview

The RoboPilot Tools server implements essential robot control functions including:
- Robot positioning and movement
- Gripper control operations
- LED status indicators
- Pick and place automation
- Safety and home positioning

## Installation

1. Install dependencies:
```bash
pip install "beeai-framework[mcp]"
pip install -r requirements.txt
```

2. Configure robot connection settings in `config.py`

3. Start the MCP server:
```bash
python server.py
```

The server will start on port 8001 by default using SSE transport.

## Available Tools

### robot_move_home_tool
- **Description**: Move robot arm to safe home position
- **Input**: `confirm_action` (bool) - Confirmation required
- **Output**: Status message with success/failure indication

### robot_pick_and_place_cycle_tool
- **Description**: Execute automated pick and place cycles
- **Input**: 
  - `cycles` (int, 1-10) - Number of cycles to perform
  - `confirm_action` (bool) - Confirmation required
- **Output**: Detailed cycle execution report

### robot_control_gripper_tool
- **Description**: Control robot gripper operations
- **Input**:
  - `operation` (str) - 'open', 'close', or 'stop'
  - `force` (float, 0-100) - Gripper force percentage
  - `confirm_action` (bool) - Confirmation required
- **Output**: Gripper operation status

### robot_gripper_led_control_tool
- **Description**: Control gripper LED indicators
- **Input**:
  - `operation` (str) - 'on', 'off', or 'blink'
  - `color` (str) - LED color selection
  - `intensity` (float, 0-100) - Light intensity percentage
- **Output**: LED control status

### robot_move_to_position_tool
- **Description**: Move robot to predefined named positions
- **Input**:
  - `position_name` (str) - Target position name
  - `movement_type` (str) - 'joint' or 'linear' movement
  - `speed` (float, 1-100) - Movement speed percentage
- **Output**: Movement execution status

## Configuration

Server configuration is managed through environment variables and `config.py`:

```python
# Server settings
MCP_SERVER_PORT = 8001
MCP_SERVER_TRANSPORT = "sse"
MCP_SERVER_NAME = "RoboPilot Tools"

# Robot connection
ROBOT_IP = "192.168.1.100"
ROBOT_PORT = 30002
GRIPPER_IP = "192.168.1.101"
GRIPPER_PORT = 63352

# Safety settings
ENABLE_SAFETY_LIMITS = True
MAX_FORCE_LIMIT = 80.0
MOVEMENT_SPEED_LIMIT = 75.0
```

## Safety Features

- **Confirmation Required**: All potentially dangerous operations require explicit confirmation
- **Force Limiting**: Gripper force is capped at safe levels
- **Speed Limiting**: Movement speeds are restricted to safe ranges
- **Error Recovery**: Automatic error handling and recovery procedures
- **Emergency Stop**: Quick stop capabilities for all operations

## Development

### Project Structure
```
robopilot-tools/
├── README.md           # This file
├── server.py          # Main MCP server implementation
├── requirements.txt   # Python dependencies
├── config.py         # Configuration settings
├── tools/            # Individual tool implementations
│   ├── __init__.py
│   ├── movement.py   # Movement control tools
│   ├── gripper.py    # Gripper control tools
│   └── safety.py     # Safety and monitoring tools
└── tests/            # Test suite
    ├── test_server.py
    ├── test_tools.py
    └── test_safety.py
```

### Running Tests
```bash
python -m pytest tests/
```

### Adding New Tools

1. Create tool implementation in `tools/` directory
2. Register tool in `server.py`
3. Add tests for new functionality
4. Update this README with tool documentation

## Integration with RoboPilot

To integrate this server with RoboPilot:

1. Update `app/utils/mcp_integration.py`:
```python
MCP_SERVER_CONFIG = {
    "robopilot_tools": {
        "url": "http://localhost:8001",
        "transport": "sse",
        "enabled": True,
        "description": "RoboPilot robot control tools",
    }
}
```

2. Start this MCP server:
```bash
cd mcp/robopilot-tools
python server.py
```

3. Start RoboPilot backend - it will automatically connect to this server

## API Documentation

The server exposes the following MCP protocol endpoints:

- `POST /tools` - List available tools
- `POST /tools/call` - Execute tool functions
- `GET /health` - Server health status
- `GET /info` - Server information and capabilities

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Verify server is running: `curl http://localhost:8001/health`
   - Check port availability
   - Verify firewall settings

2. **Robot Not Responding**
   - Check robot IP address in configuration
   - Verify network connectivity to robot
   - Ensure robot is in remote control mode

3. **Permission Errors**
   - Verify user has robot control permissions
   - Check safety system status
   - Ensure emergency stop is not engaged

### Debug Mode

Run the server in debug mode for detailed logging:
```bash
PYTHONPATH=. python server.py --debug
```

### Log Files

Logs are written to:
- `logs/server.log` - Server operation logs
- `logs/robot.log` - Robot communication logs
- `logs/safety.log` - Safety system logs

## Support

For issues and questions:
- Check the troubleshooting section above
- Review log files for error details
- Consult the main RoboPilot documentation
- Open an issue in the project repository

## License

This MCP server is part of the RoboPilot project and follows the same licensing terms.