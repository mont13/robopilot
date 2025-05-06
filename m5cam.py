import requests
import os
from datetime import datetime

# Replace with your camera's IP address
camera_ip = "192.168.4.1"


# Define the capture URL
capture_url = f"http://{camera_ip}/api/v1/capture"

# Define the directory where you want to save the photos on your PC
save_directory = os.path.join(os.getcwd(), "CamS3_Photos")
os.makedirs(save_directory, exist_ok=True)

# Generate a unique filename using the current timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"captured_image_{timestamp}.jpg"
full_path = os.path.join(save_directory, filename)

# Capture the photo
try:
    response = requests.get(capture_url, timeout=10)
    response.raise_for_status()  # Raise an exception for bad status codes

    # Save the captured image to your PC
    with open(full_path, "wb") as f:
        f.write(response.content)
    print(f"Image captured and saved successfully to: {full_path}")

except requests.RequestException as e:
    print(f"Failed to capture image. Error: {e}")

