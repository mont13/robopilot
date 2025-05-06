def send_arm_command(angles, speed):
    """
    Send command to arm via MQTT
    
    Args:
        angles (list): List of 6 angles for each joint
        speed (int): Speed value between 1-100
    """
    import paho.mqtt.client as mqtt
    import json
    
    # MQTT settings
    mqtt_broker = ""
    mqtt_port = 1883
    mqtt_username = ""
    mqtt_password = ""
    mqtt_client_id = ""
    topic = "mycobot/send_angles"

    # Prepare message
    message = json.dumps({
        "angles": angles,
        "speed": speed
    })

    # Connect and publish
    try:
        # Use CallbackAPIVersion.VERSION1 as in hopefully_api.py
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=mqtt_client_id)
        client.username_pw_set(mqtt_username, mqtt_password)
        client.connect(mqtt_broker, mqtt_port, 60)
        client.publish(topic, message)
        client.disconnect()
        return True
    except Exception as e:
        print(f"Error sending command: {e}")
        return False

# Example usage:
send_arm_command([0, 0, 0, 0, 0, 0], 20)  # Home position at speed 20
# send_arm_command([45, -45, 30, 0, 90, 0], 50)  # Custom position at speed 50