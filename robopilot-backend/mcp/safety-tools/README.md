# Safety Tools MCP Server

This MCP server provides comprehensive safety monitoring and emergency control capabilities for the RoboPilot system. It exposes critical safety functions through the Model Context Protocol, ensuring safe operation of robotic systems through continuous monitoring and emergency response mechanisms.

## Overview

The Safety Tools server implements essential safety functions including:
- Real-time safety monitoring and alerts
- Emergency stop and shutdown procedures
- Collision detection and avoidance
- Environmental hazard monitoring
- Safety zone enforcement
- Risk assessment and reporting
- Compliance verification and logging

## Installation

1. Install dependencies:
```bash
pip install "beeai-framework[mcp]"
pip install numpy
pip install scipy
pip install -r requirements.txt
```

2. Configure safety parameters and thresholds in `config.py`

3. Start the MCP server:
```bash
python server.py
```

The server will start on port 8003 by default using SSE transport.

## Available Tools

### emergency_stop_tool
- **Description**: Immediately halt all robot operations and engage safety systems
- **Input**: 
  - `stop_type` (str) - Type of stop ("immediate", "controlled", "power_off")
  - `reason` (str) - Reason for emergency stop
- **Output**: Emergency stop execution status and system state

### safety_zone_monitor_tool
- **Description**: Monitor and enforce predefined safety zones around the robot
- **Input**:
  - `zone_id` (str) - Safety zone identifier
  - `action` (str) - Action to take ("check", "enable", "disable")
  - `boundaries` (dict) - Zone boundary coordinates (optional)
- **Output**: Safety zone status and violation alerts

### collision_detection_tool
- **Description**: Detect potential collisions using sensors and predictive analysis
- **Input**:
  - `sensor_data` (dict) - Current sensor readings
  - `trajectory` (list) - Planned robot trajectory
  - `sensitivity` (float, 0.0-1.0) - Detection sensitivity level
- **Output**: Collision risk assessment and avoidance recommendations

### environmental_monitor_tool
- **Description**: Monitor environmental conditions for safety hazards
- **Input**:
  - `sensors` (list) - Sensors to monitor ("temperature", "pressure", "gas", "vibration")
  - `thresholds` (dict) - Safety threshold values
  - `duration` (int) - Monitoring duration in seconds
- **Output**: Environmental safety status and hazard alerts

### safety_assessment_tool
- **Description**: Perform comprehensive safety risk assessment
- **Input**:
  - `operation_type` (str) - Type of operation to assess
  - `environment` (dict) - Environmental conditions
  - `personnel_present` (bool) - Human presence indicator
- **Output**: Safety risk score and recommended precautions

### compliance_check_tool
- **Description**: Verify compliance with safety standards and regulations
- **Input**:
  - `standard` (str) - Safety standard to check ("ISO12100", "ANSI/RIA", "IEC61508")
  - `operation_log` (dict) - Operation history data
  - `configuration` (dict) - Current system configuration
- **Output**: Compliance status and required corrections

### safety_audit_tool
- **Description**: Generate comprehensive safety audit reports
- **Input**:
  - `time_period` (str) - Audit period ("daily", "weekly", "monthly")
  - `include_logs` (bool) - Include detailed operation logs
  - `format` (str) - Report format ("json", "pdf", "csv")
- **Output**: Detailed safety audit report

### force_torque_monitor_tool
- **Description**: Monitor robot force and torque for safety limit enforcement
- **Input**:
  - `joint_id` (int) - Joint to monitor (or -1 for all)
  - `limits` (dict) - Force/torque limit values
  - `action_on_exceed` (str) - Action when limits exceeded
- **Output**: Force/torque status and limit violation alerts

## Configuration

Server configuration is managed through environment variables and `config.py`:

```python
# Server settings
MCP_SERVER_PORT = 8003
MCP_SERVER_TRANSPORT = "sse"
MCP_SERVER_NAME = "Safety Tools"

# Safety limits
MAX_JOINT_VELOCITY = 1.0  # rad/s
MAX_JOINT_ACCELERATION = 2.0  # rad/s²
MAX_END_EFFECTOR_FORCE = 150.0  # N
MAX_JOINT_TORQUE = 100.0  # Nm

# Environmental thresholds
MAX_TEMPERATURE = 45.0  # °C
MIN_TEMPERATURE = 5.0   # °C
MAX_HUMIDITY = 85.0     # %
PRESSURE_RANGE = (950.0, 1050.0)  # hPa

# Safety zones
SAFETY_ZONES = {
    "human_zone": {
        "type": "exclusion",
        "boundaries": [[0, 0, 0], [2, 2, 2]],  # 3D coordinates
        "action": "immediate_stop"
    },
    "work_zone": {
        "type": "restricted",
        "boundaries": [[-1, -1, -1], [3, 3, 3]],
        "action": "slow_down"
    }
}

# Emergency settings
EMERGENCY_STOP_TIMEOUT = 5.0  # seconds
SAFETY_SYSTEM_CHECK_INTERVAL = 0.1  # seconds
LOG_RETENTION_DAYS = 90
```

## Safety Features

- **Triple Redundancy**: Critical safety functions have multiple backup systems
- **Fail-Safe Design**: System defaults to safe state on any failure
- **Real-Time Monitoring**: Continuous monitoring of all safety parameters
- **Immediate Response**: Sub-100ms response time for emergency situations
- **Comprehensive Logging**: All safety events are logged with timestamps
- **Regulatory Compliance**: Adherence to international safety standards

## Development

### Project Structure
```
safety-tools/
├── README.md              # This file
├── server.py             # Main MCP server implementation
├── requirements.txt      # Python dependencies
├── config.py            # Configuration settings
├── tools/               # Individual tool implementations
│   ├── __init__.py
│   ├── emergency.py     # Emergency stop and shutdown tools
│   ├── monitoring.py    # Continuous monitoring tools
│   ├── zones.py         # Safety zone management tools
│   ├── assessment.py    # Risk assessment tools
│   ├── compliance.py    # Compliance checking tools
│   └── audit.py         # Audit and reporting tools
├── standards/           # Safety standard definitions
│   ├── iso12100.json
│   ├── ansi_ria.json
│   └── iec61508.json
├── logs/                # Safety logs and audit trails
└── tests/               # Test suite
    ├── test_server.py
    ├── test_emergency.py
    ├── test_monitoring.py
    └── test_compliance.py
```

### Running Tests
```bash
python -m pytest tests/
python tests/test_emergency_stop.py  # Critical safety tests
python tests/test_safety_limits.py   # Safety limit validation
```

### Safety Testing Protocol
All safety tools undergo rigorous testing:
1. Unit tests for individual components
2. Integration tests with robot hardware
3. Emergency response simulation
4. Compliance validation tests
5. Performance benchmarking under load

## Integration with RoboPilot

To integrate this server with RoboPilot:

1. Update `app/utils/mcp_integration.py`:
```python
MCP_SERVER_CONFIG = {
    "safety_tools": {
        "url": "http://localhost:8003",
        "transport": "sse",
        "enabled": True,
        "description": "Safety monitoring and emergency control tools",
    }
}
```

2. Start this MCP server:
```bash
cd mcp/safety-tools
python server.py
```

3. Start RoboPilot backend - it will automatically connect to this server

## API Documentation

The server exposes the following MCP protocol endpoints:

- `POST /tools` - List available safety tools
- `POST /tools/call` - Execute safety functions
- `GET /health` - Server health and safety system status
- `GET /emergency` - Emergency system status
- `GET /zones` - Safety zone configuration and status
- `GET /compliance` - Current compliance status

## Emergency Procedures

### Emergency Stop Sequence
1. **Signal Received**: Emergency stop signal detected
2. **Immediate Action**: All motion commands cancelled within 50ms
3. **Power Control**: Motor power reduced or cut based on stop type
4. **System Lock**: All operations locked until manual reset
5. **Notification**: Alerts sent to all connected systems
6. **Logging**: Emergency event logged with full context

### Recovery Procedures
1. **Safety Check**: Comprehensive system safety verification
2. **Manual Inspection**: Physical inspection of robot and environment
3. **System Reset**: Authorized personnel reset safety system
4. **Calibration**: Re-calibrate sensors and safety systems
5. **Test Mode**: Limited functionality test before full operation
6. **Full Operation**: Return to normal operation after all checks pass

## Monitoring and Alerting

### Real-Time Monitoring
- Joint positions, velocities, and accelerations
- Force and torque measurements
- Environmental sensors (temperature, pressure, humidity)
- Safety zone violations
- System health indicators

### Alert Levels
- **INFO**: Normal operational status
- **WARNING**: Approaching safety limits
- **ERROR**: Safety limit exceeded, corrective action taken
- **CRITICAL**: Emergency situation, immediate stop required
- **FATAL**: System failure, manual intervention required

### Notification Methods
- MCP protocol messages to connected systems
- Local audio/visual alarms
- Email notifications to safety personnel
- SMS alerts for critical emergencies
- Integration with building safety systems

## Troubleshooting

### Common Issues

1. **False Emergency Stops**
   - Check sensor calibration and cleanliness
   - Verify environmental conditions within normal ranges
   - Review safety zone boundaries for accuracy

2. **Sensor Communication Errors**
   - Check sensor connections and power supply
   - Verify communication protocols and settings
   - Test individual sensors with diagnostic tools

3. **Safety System Not Responding**
   - Check safety system power and connections
   - Verify emergency stop circuit continuity
   - Test safety relays and contactors

4. **Compliance Violations**
   - Review operation parameters against standards
   - Update safety configurations as needed
   - Provide additional training to operators

### Debug Mode

Run the server in debug mode for detailed logging:
```bash
PYTHONPATH=. python server.py --debug --safety-test-mode
```

### Log Files

Logs are written to:
- `logs/safety_server.log` - Server operation logs
- `logs/emergency_events.log` - Emergency stop and critical events
- `logs/monitoring.log` - Continuous monitoring data
- `logs/compliance.log` - Compliance checking results
- `logs/audit_trail.log` - Complete audit trail for investigations

## Regulatory Compliance

### Supported Standards
- **ISO 12100**: Safety of machinery - General principles for design
- **ANSI/RIA R15.06**: Industrial robots and robot systems - Safety requirements
- **IEC 61508**: Functional safety of safety-related systems
- **ISO 13849**: Safety of machinery - Safety-related parts of control systems
- **IEC 62061**: Safety of machinery - Functional safety of safety-related control systems

### Compliance Features
- Automatic compliance checking against selected standards
- Detailed compliance reports and documentation
- Traceability of all safety-related decisions and actions
- Regular compliance audits and reviews

## Support

For issues and questions:
- Check the troubleshooting section above
- Review safety logs for detailed error information
- Contact safety personnel immediately for critical issues
- Consult the main RoboPilot documentation
- Open an issue in the project repository (for non-urgent matters)

## Emergency Contact Information

For safety emergencies:
- **Emergency Stop**: Physical emergency stop button locations
- **Safety Personnel**: [Contact information to be configured]
- **Technical Support**: [Contact information to be configured]
- **Emergency Services**: Local emergency services number

## License

This MCP server is part of the RoboPilot project and follows the same licensing terms. All safety-related code undergoes additional review and validation processes.