# Object Detection API with OAK-D and FastAPI

This project provides a FastAPI web server that exposes real-time object detection results from a Luxonis OAK-D (or compatible DepthAI) camera. It uses a pre-trained MobileNet-SSD model for object detection.

## Features

*   **Real-time Object Detection:** Leverages DepthAI to perform inference on the OAK camera.
*   **FastAPI Backend:** Exposes detection results via a modern, high-performance API.
*   **Automatic Model Download:** Uses `blobconverter` to fetch the necessary AI model blob.
*   **Background Processing:** Runs camera operations in a separate thread to keep the API responsive.
*   **Health Check Endpoint:** Provides status of the API and camera connection.
*   **Interactive API Docs:** Swagger UI (`/docs`) for easy API exploration and testing.
*   **CORS Enabled:** Allows requests from any origin by default.

## Prerequisites

Before running the script, ensure you have the following:

1.  **Python:** Python 3.7 or newer.
2.  **pip:** Python package installer (usually comes with Python).
3.  **OAK-D Camera:** An OAK-D, OAK-D Lite, OAK-D S2, OAK-1, etc., camera connected to your computer via a USB3 port.
4.  **Operating System:** Linux, macOS, or Windows with DepthAI SDK requirements met.
    *   **Linux:** You may need to set up udev rules. See [DepthAI Linux udev Rules](https://docs.luxonis.com/en/latest/pages/api/#udev-rules).

## Setup

1.  **Save the Code:**
    Save the provided Python code into a file named `api.py` (or your preferred name).

2.  **Create a Virtual Environment (Recommended):**
    Open your terminal or command prompt in the project directory.
    ```bash
    python -m venv venv
    ```
    Activate the virtual environment:
    *   On Windows:
        ```bash
        venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

3.  **Install Dependencies:**
    Install the necessary Python packages using pip:
    ```bash
    pip install fastapi "uvicorn[standard]" depthai blobconverter numpy
    ```
    *   `fastapi`: The web framework.
    *   `uvicorn[standard]`: The ASGI server to run FastAPI.
    *   `depthai`: The core library for interacting with OAK cameras.
    *   `blobconverter`: For downloading pre-compiled AI model blobs.
    *   `numpy`: For numerical operations.

4.  **Connect your OAK-D Camera:**
    Ensure your OAK-D camera is properly connected to a USB3 port on your computer.

## Running the Application

1.  **Navigate to the Directory:**
    In your terminal, make sure you are in the directory where you saved `api.py`.

2.  **Start the Uvicorn Server:**
    Run the following command:
    ```bash
    uvicorn api:app --host 0.0.0.0 --port 8000
    ```
    *   `api:app`: Tells Uvicorn to look for an object named `app` (your FastAPI instance) inside a file named `api.py`. If you named your Python file differently (e.g., `main.py`), adjust the command accordingly (e.g., `uvicorn main:app ...`).
    *   `--host 0.0.0.0`: Makes the server accessible from any IP address on your machine, including from other devices on your local network.
    *   `--port 8000`: Specifies the port the server will listen on.

3.  **Initial Run & Model Download:**
    The first time you run the script, `blobconverter` will download the MobileNet-SSD model blob. This might take a few moments. Subsequent runs will use the cached blob.

4.  **Expected Log Output:**
    You should see output similar to this:
    ```
    INFO:     Started server process [XXXXX]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
    INFO:     Starting Object Detection API server...
    INFO:     Server will be available on all interfaces (0.0.0.0:8000).
    INFO:     Try accessing on this machine via: http://localhost:8000 or http://<your_local_ip>:8000
    INFO:     Available Endpoints:
    INFO:       API Docs (Swagger UI): http://localhost:8000/docs
    INFO:       Detections:            http://localhost:8000/detections
    INFO:       Health Check:          http://localhost:8000/health
    INFO:       Test Endpoint:         http://localhost:8000/test
    INFO:     Press Ctrl+C to stop the server.
    INFO:     Creating DepthAI pipeline...
    INFO:     DepthAI pipeline created successfully.
    INFO:     Camera worker thread initiated.
    INFO:     Successfully connected to OAK device: <Device Name>
    INFO:     USB speed: <USB Speed e.g., SUPER>
    ```

## Accessing the API Endpoints

Once the server is running, you can interact with it using a web browser or API client tools like Postman or `curl`.

### 1. `/docs` - API Documentation (Swagger UI)

*   **URL:** `http://localhost:8000/docs`
*   **Method:** `GET`
*   **Description:** Provides an interactive interface (Swagger UI) to explore and test all API endpoints.

### 2. `/detections` - Get Latest Detections

*   **URL:** `http://localhost:8000/detections`
*   **Method:** `GET`
*   **Description:** Returns the most recent set of detected objects from the OAK-D camera.
*   **Successful Response (200 OK):**
    ```json
    {
      "detections": [
        {
          "label": "person",
          "confidence": 0.85,
          "bbox": { "xmin": 100, "ymin": 50, "xmax": 200, "ymax": 250 }
        },
        {
          "label": "car",
          "confidence": 0.92,
          "bbox": { "xmin": 30, "ymin": 80, "xmax": 150, "ymax": 180 }
        }
      ],
      "timestamp": 1678886400.12345
    }
    ```
*   **No New Detections (204 No Content):** If the camera is running but no new detections are in the queue at that moment.
*   **Service Unavailable (503 Service Unavailable):** If the camera system is down or experienced an error. The response body will contain an error detail.

### 3. `/health` - Health Check

*   **URL:** `http://localhost:8000/health`
*   **Method:** `GET`
*   **Description:** Provides status information about the API and the camera worker thread.
*   **Example Response (Healthy):**
    ```json
    {
        "status": "healthy",
        "timestamp": 1678886405.54321,
        "service_name": "Object Detection API",
        "camera_pipeline_initialized": true,
        "camera_thread_active": true,
        "camera_status_details": "running",
        "last_camera_error_hint": "N/A",
        "detection_queue_current_size": 0,
        "hostname": "my-computer",
        "ip_address": "192.168.1.100"
    }
    ```
    If there are issues, `status` might be `"degraded"`, and other fields will provide more context.

### 4. `/test` - Test Endpoint

*   **URL:** `http://localhost:8000/test`
*   **Method:** `GET`
*   **Description:** A simple endpoint to confirm the API server is responding (does not require camera).
*   **Example Response:**
    ```json
    {
        "message": "API is working!",
        "timestamp": 1678886410.67890,
        "hostname": "my-computer",
        "ip_address": "192.168.1.100"
    }
    ```

## Configuration

You can modify the following constants at the beginning of the `api.py` script:

*   `MODEL_ZOO_NAME = "mobilenet-ssd"`: Specifies the object detection model. You can find other compatible models on the [blobconverter models list](https://docs.luxonis.com/projects/blobconverter/en/latest/models_zoo/#detection-models).
*   `NN_CONFIDENCE_THRESHOLD = 0.5`: Minimum confidence score (0.0 to 1.0) for a detection to be considered valid.
*   `NN_INPUT_SIZE = (300, 300)`: Input image size for the neural network. This should match the model's requirements.
*   `CAMERA_FPS = 30`: Desired frames per second for the camera.

If you change these, you'll need to stop and restart the Uvicorn server.

## Stopping the Application

To stop the API server, go to the terminal where Uvicorn is running and press `Ctrl+C`. The application includes shutdown hooks to attempt a graceful stop of the camera worker thread.

## Troubleshooting

*   **`RuntimeError: No available devices` or similar DepthAI errors:**
    *   Ensure your OAK camera is connected to a **USB3 port**.
    *   Check if another application is already using the camera.
    *   On Linux, ensure udev rules are correctly set up (see Prerequisites).
    *   Try unplugging and replugging the camera.
    *   Restart your computer.
*   **`ModuleNotFoundError`:**
    *   Ensure you have installed all dependencies listed in the "Setup" section.
    *   If using a virtual environment, make sure it's activated.
*   **Slow performance or low FPS:**
    *   Verify the camera is connected to a USB3 port (check `USB speed` in startup logs or the `/health` endpoint output). USB2 will significantly limit performance.
    *   The host system's CPU/resources can also be a bottleneck.
*   **Firewall Issues:** If accessing from another device on your network fails, check your system's firewall settings to ensure incoming connections on port 8000 (or your configured port) are allowed.