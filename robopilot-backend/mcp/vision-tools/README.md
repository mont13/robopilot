# Vision Tools MCP Server

This MCP server provides computer vision and image processing capabilities for the RoboPilot system. It exposes vision-based tools through the Model Context Protocol, enabling advanced visual perception and analysis for robotic operations.

## Overview

The Vision Tools server implements essential computer vision functions including:
- Object detection and recognition
- Image capture and processing
- Depth estimation and 3D perception
- Visual quality inspection
- Pose estimation and tracking
- Scene understanding and analysis

## Installation

1. Install dependencies:
```bash
pip install "beeai-framework[mcp]"
pip install opencv-python
pip install numpy
pip install pillow
pip install -r requirements.txt
```

2. Configure camera and vision settings in `config.py`

3. Start the MCP server:
```bash
python server.py
```

The server will start on port 8002 by default using SSE transport.

## Available Tools

### camera_capture_image_tool
- **Description**: Capture image from connected camera
- **Input**: 
  - `camera_id` (int) - Camera identifier (0, 1, 2...)
  - `resolution` (str) - Image resolution (e.g., "1920x1080")
  - `format` (str) - Output format ("jpg", "png", "bmp")
- **Output**: Base64 encoded image data and metadata

### object_detection_tool
- **Description**: Detect and classify objects in image
- **Input**:
  - `image_data` (str) - Base64 encoded image or file path
  - `confidence_threshold` (float, 0.0-1.0) - Detection confidence minimum
  - `model_type` (str) - Detection model ("yolo", "ssd", "faster_rcnn")
- **Output**: Detected objects with bounding boxes and confidence scores

### depth_estimation_tool
- **Description**: Estimate depth information from stereo or RGB-D cameras
- **Input**:
  - `left_image` (str) - Left camera image (stereo setup)
  - `right_image` (str) - Right camera image (stereo setup)
  - `calibration_data` (dict) - Camera calibration parameters
- **Output**: Depth map and point cloud data

### quality_inspection_tool
- **Description**: Visual quality inspection and defect detection
- **Input**:
  - `image_data` (str) - Image to inspect
  - `reference_image` (str) - Reference/template image
  - `tolerance` (float) - Acceptable variation threshold
  - `inspection_type` (str) - Type of inspection ("surface", "alignment", "completeness")
- **Output**: Quality assessment results and defect locations

### pose_estimation_tool
- **Description**: Estimate object pose and orientation
- **Input**:
  - `image_data` (str) - Input image
  - `object_model` (str) - 3D object model or template
  - `camera_matrix` (list) - Camera intrinsic parameters
- **Output**: 6DOF pose information (position and orientation)

### scene_analysis_tool
- **Description**: Analyze scene composition and spatial relationships
- **Input**:
  - `image_data` (str) - Scene image
  - `analysis_type` (str) - Analysis focus ("objects", "layout", "relationships")
  - `roi` (dict) - Region of interest coordinates (optional)
- **Output**: Scene description and spatial analysis

### image_processing_tool
- **Description**: Apply various image processing operations
- **Input**:
  - `image_data` (str) - Input image
  - `operations` (list) - Processing operations to apply
  - `parameters` (dict) - Operation-specific parameters
- **Output**: Processed image and operation results

## Configuration

Server configuration is managed through environment variables and `config.py`:

```python
# Server settings
MCP_SERVER_PORT = 8002
MCP_SERVER_TRANSPORT = "sse"
MCP_SERVER_NAME = "Vision Tools"

# Camera settings
PRIMARY_CAMERA_ID = 0
SECONDARY_CAMERA_ID = 1
DEFAULT_RESOLUTION = "1920x1080"
DEFAULT_FPS = 30

# Vision models
OBJECT_DETECTION_MODEL = "yolov8n.pt"
POSE_ESTIMATION_MODEL = "pose_model.onnx"
DEPTH_MODEL = "dpt_large.pt"

# Processing settings
MAX_IMAGE_SIZE = 4096
SUPPORTED_FORMATS = ["jpg", "png", "bmp", "tiff"]
ENABLE_GPU_ACCELERATION = True
```

## Camera Setup

### Supported Cameras
- USB cameras (webcams, industrial cameras)
- IP cameras (RTSP/HTTP streams)
- Stereo camera pairs
- RGB-D cameras (Intel RealSense, Azure Kinect)

### Camera Calibration
Cameras should be calibrated for accurate measurements:

```bash
python tools/camera_calibration.py --camera-id 0 --pattern chessboard
```

Calibration data is stored in `calibration/camera_{id}_calibration.json`

## Safety Features

- **Image Privacy**: Automatic face/personal information blurring
- **Resource Limits**: Memory and processing time restrictions
- **Error Handling**: Graceful failure recovery
- **Data Validation**: Input image format and size validation
- **Access Control**: Tool execution logging and audit trail

## Development

### Project Structure
```
vision-tools/
├── README.md              # This file
├── server.py             # Main MCP server implementation
├── requirements.txt      # Python dependencies
├── config.py            # Configuration settings
├── tools/               # Individual tool implementations
│   ├── __init__.py
│   ├── capture.py       # Camera capture tools
│   ├── detection.py     # Object detection tools
│   ├── depth.py         # Depth estimation tools
│   ├── inspection.py    # Quality inspection tools
│   ├── pose.py          # Pose estimation tools
│   └── processing.py    # Image processing tools
├── models/              # Pre-trained models
│   ├── yolo/
│   ├── pose/
│   └── depth/
├── calibration/         # Camera calibration data
└── tests/               # Test suite
    ├── test_server.py
    ├── test_tools.py
    └── test_vision.py
```

### Running Tests
```bash
python -m pytest tests/
python tests/test_camera_connection.py  # Hardware tests
```

### Adding New Vision Tools

1. Create tool implementation in `tools/` directory
2. Add required models to `models/` directory
3. Register tool in `server.py`
4. Add tests for new functionality
5. Update this README with tool documentation

## Integration with RoboPilot

To integrate this server with RoboPilot:

1. Update `app/utils/mcp_integration.py`:
```python
MCP_SERVER_CONFIG = {
    "vision_tools": {
        "url": "http://localhost:8002",
        "transport": "sse",
        "enabled": True,
        "description": "Computer vision and image processing tools",
    }
}
```

2. Start this MCP server:
```bash
cd mcp/vision-tools
python server.py
```

3. Start RoboPilot backend - it will automatically connect to this server

## API Documentation

The server exposes the following MCP protocol endpoints:

- `POST /tools` - List available vision tools
- `POST /tools/call` - Execute vision functions
- `GET /health` - Server health and camera status
- `GET /cameras` - List available cameras
- `GET /models` - List loaded vision models

## Performance Optimization

### GPU Acceleration
Enable GPU processing for faster inference:
```python
ENABLE_GPU_ACCELERATION = True
CUDA_DEVICE_ID = 0  # GPU device to use
```

### Memory Management
- Image caching for repeated operations
- Automatic memory cleanup after processing
- Configurable memory limits per operation

### Processing Pipeline
- Batch processing for multiple images
- Asynchronous operation support
- Result caching for expensive operations

## Troubleshooting

### Common Issues

1. **Camera Not Detected**
   - Check USB/network connections
   - Verify camera permissions and drivers
   - Test with `python tools/test_camera.py`

2. **Model Loading Errors**
   - Verify model files in `models/` directory
   - Check model format compatibility
   - Ensure sufficient memory for model loading

3. **Poor Detection Accuracy**
   - Check image quality and lighting
   - Verify camera calibration
   - Adjust confidence thresholds

4. **Performance Issues**
   - Enable GPU acceleration if available
   - Reduce image resolution for faster processing
   - Use lighter models for real-time applications

### Debug Mode

Run the server in debug mode for detailed logging:
```bash
PYTHONPATH=. python server.py --debug --verbose
```

### Log Files

Logs are written to:
- `logs/vision_server.log` - Server operation logs
- `logs/camera.log` - Camera operation logs
- `logs/processing.log` - Vision processing logs

## Model Management

### Pre-trained Models
The server includes several pre-trained models:
- **YOLOv8**: Object detection (nano, small, medium, large)
- **DPT**: Depth estimation from monocular images
- **PoseNet**: Human pose estimation
- **Custom**: Domain-specific trained models

### Model Updates
```bash
python tools/update_models.py --model yolo --version v8n
python tools/train_custom_model.py --dataset custom_dataset/
```

## Support

For issues and questions:
- Check the troubleshooting section above
- Review log files for error details
- Test individual components with provided test scripts
- Consult the main RoboPilot documentation
- Open an issue in the project repository

## License

This MCP server is part of the RoboPilot project and follows the same licensing terms.