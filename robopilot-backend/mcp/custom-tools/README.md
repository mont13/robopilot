# Custom Tools MCP Server Directory

This directory is reserved for custom user-defined MCP servers and tools. Users can create their own specialized MCP servers here to extend RoboPilot's capabilities with domain-specific functionality.

## Overview

The Custom Tools directory provides a space for:
- User-specific tool implementations
- Experimental and prototype tools
- Domain-specific integrations
- Third-party tool adaptations
- Custom workflow automation tools

## Creating Your Custom MCP Server

### Quick Start

1. **Create your server directory**:
```bash
mkdir mcp/custom-tools/my-custom-server
cd mcp/custom-tools/my-custom-server
```

2. **Create the basic server structure**:
```
my-custom-server/
├── README.md          # Server documentation
├── server.py         # Main MCP server implementation
├── requirements.txt  # Python dependencies
├── config.py        # Configuration settings
└── tools/           # Your custom tools
    ├── __init__.py
    └── my_tools.py
```

3. **Implement your server** (`server.py`):
```python
from beeai_framework.adapters.mcp.serve.server import MCPServer, MCPServerConfig, MCPSettings
from beeai_framework.tools import tool
from beeai_framework.tools.types import StringToolOutput
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    """Input schema for your custom tool."""
    parameter: str = Field(description="Tool parameter description")
    value: float = Field(default=1.0, description="Numeric value")

@tool
def my_custom_tool(input_data: MyToolInput) -> StringToolOutput:
    """
    Your custom tool implementation.
    
    This tool does something specific to your use case.
    """
    try:
        # Your custom logic here
        result = f"Processed {input_data.parameter} with value {input_data.value}"
        return StringToolOutput(result=result)
    except Exception as e:
        return StringToolOutput(result=f"Error: {str(e)}")

def main():
    # Configure your server
    server = MCPServer(
        config=MCPServerConfig(
            transport="sse",
            name="My Custom Tools Server",
            settings=MCPSettings(port=8004)  # Use port 8004+ for custom servers
        )
    )
    
    # Register your tools
    server.register(my_custom_tool)
    
    # Start serving
    server.serve()

if __name__ == "__main__":
    main()
```

4. **Create requirements.txt**:
```
beeai-framework[mcp]>=0.1.0
pydantic>=2.0.0
# Add your specific dependencies here
```

5. **Update RoboPilot configuration** in `app/utils/mcp_integration.py`:
```python
MCP_SERVER_CONFIG = {
    "my_custom_server": {
        "url": "http://localhost:8004",
        "transport": "sse",
        "enabled": True,
        "description": "My custom tools for specific workflows",
    }
}
```

6. **Test your server**:
```bash
cd mcp/custom-tools/my-custom-server
python server.py
```

## Port Assignment Guidelines

Use these port ranges for custom servers to avoid conflicts:
- **8004-8099**: Custom user tools
- **8100-8199**: Experimental tools
- **8200-8299**: Integration tools
- **8300-8399**: Workflow automation tools

## Common Use Cases

### Data Processing Tools
```python
@tool
def data_analysis_tool(input_data: DataInput) -> StringToolOutput:
    """Analyze data with custom algorithms."""
    # Your data processing logic
    return StringToolOutput(result="Analysis complete")
```

### External System Integration
```python
@tool
def external_api_tool(input_data: APIInput) -> StringToolOutput:
    """Integrate with external APIs or services."""
    # API calls and integration logic
    return StringToolOutput(result="API call successful")
```

### Workflow Automation
```python
@tool
def workflow_automation_tool(input_data: WorkflowInput) -> StringToolOutput:
    """Automate complex multi-step workflows."""
    # Workflow orchestration logic
    return StringToolOutput(result="Workflow completed")
```

### Custom Hardware Control
```python
@tool
def hardware_control_tool(input_data: HardwareInput) -> StringToolOutput:
    """Control custom hardware devices."""
    # Hardware communication logic
    return StringToolOutput(result="Hardware operation complete")
```

## Best Practices

### Tool Design
- Use descriptive tool names and clear documentation
- Implement proper input validation with Pydantic models
- Include comprehensive error handling
- Return meaningful success/failure messages
- Keep tools focused on single responsibilities

### Configuration Management
- Use environment variables for sensitive data
- Provide sensible defaults in config files
- Document all configuration options
- Include validation for configuration values

### Error Handling
```python
@tool
def robust_tool(input_data: MyInput) -> StringToolOutput:
    """Example of robust error handling."""
    try:
        # Validate inputs
        if not input_data.parameter:
            return StringToolOutput(result="Error: Parameter cannot be empty")
        
        # Your tool logic
        result = process_data(input_data.parameter)
        
        # Return success
        return StringToolOutput(result=f"Success: {result}")
        
    except ValueError as e:
        return StringToolOutput(result=f"Validation Error: {str(e)}")
    except ConnectionError as e:
        return StringToolOutput(result=f"Connection Error: {str(e)}")
    except Exception as e:
        return StringToolOutput(result=f"Unexpected Error: {str(e)}")
```

### Testing
- Create unit tests for each tool
- Test with various input scenarios
- Verify error handling paths
- Performance test with expected loads

### Security
- Sanitize all inputs
- Avoid executing arbitrary code
- Use secure communication protocols
- Log security-relevant events

## Directory Examples

### Example Structure for Different Tool Types

```
custom-tools/
├── data-processing/          # Data analysis and processing tools
│   ├── server.py
│   ├── tools/
│   │   ├── statistics.py
│   │   ├── visualization.py
│   │   └── export.py
│   └── README.md
├── iot-integration/          # IoT device integration
│   ├── server.py
│   ├── devices/
│   │   ├── sensors.py
│   │   └── actuators.py
│   └── README.md
├── workflow-automation/      # Business process automation
│   ├── server.py
│   ├── workflows/
│   │   ├── manufacturing.py
│   │   └── quality_control.py
│   └── README.md
└── experimental/            # Prototype and test tools
    ├── server.py
    ├── prototypes/
    └── README.md
```

## Integration Guidelines

### With RoboPilot Core
- Follow the same patterns as core servers
- Use consistent naming conventions
- Provide comprehensive documentation
- Include health check endpoints

### With Other MCP Servers
- Avoid tool name conflicts
- Consider tool dependencies
- Plan for tool composition
- Document inter-tool relationships

## Deployment Considerations

### Development
- Use debug logging during development
- Test thoroughly before deployment
- Version your tools appropriately
- Maintain backward compatibility when possible

### Production
- Use production-grade logging
- Implement proper monitoring
- Set up health checks
- Plan for graceful shutdown

### Maintenance
- Monitor server performance
- Update dependencies regularly
- Review and rotate logs
- Backup configuration and data

## Support and Community

### Getting Help
- Check existing examples in this directory
- Review the main RoboPilot documentation
- Consult MCP protocol specifications
- Ask questions in project discussions

### Contributing Back
- Consider contributing useful tools to the main project
- Share examples and templates
- Document interesting use cases
- Help other users in forums

### Best Practices Sharing
- Document your successful patterns
- Share configuration examples
- Contribute to this README with improvements
- Create tutorials for complex integrations

## Troubleshooting

### Common Issues
1. **Port conflicts**: Ensure unique ports for each server
2. **Import errors**: Check Python path and dependencies
3. **Tool registration**: Verify tools are properly decorated and registered
4. **Configuration errors**: Validate all configuration values

### Debug Mode
```bash
PYTHONPATH=. python server.py --debug
```

### Log Analysis
Check server logs for detailed error information:
- Server startup issues
- Tool execution errors
- Configuration problems
- Network connectivity issues

## License and Legal

- Follow the same license as the main RoboPilot project
- Respect third-party licenses for any dependencies
- Document any licensing requirements for your tools
- Consider intellectual property implications

## Examples and Templates

See the `examples/` subdirectory (when available) for:
- Complete server implementations
- Common tool patterns
- Integration examples
- Configuration templates

---

*This directory is part of the RoboPilot MCP integration system. For more information, see the main MCP integration documentation.*