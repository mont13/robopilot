from farmbot import Farmbot
import time
import logging

# Nastavení logování
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("farmbot_log.txt"),  # Log do souboru
        logging.StreamHandler()                 # Log na konzoli
    ]
)
logger = logging.getLogger()

EMAIL = ""
PASSWORD = ""

fb = Farmbot()

def connect():
    TOKEN = fb.get_token(EMAIL, PASSWORD)
    print(f'{TOKEN = }')
    fb.set_token(TOKEN)

def get_position():
    connect()  # Připojí se k Farmbotu
    status = fb.read_status()  # Načte aktuální stav
    position = status['location_data']['position']  # Získá pozici motoru
    x = position['x']
    y = position['y']
    z = position['z']
    print(f"Aktuální pozice: x={x}, y={y}, z={z}")
    return x, y, z

def take_photo():
   print("Fotím...")



def turn_arm(angles, speed):
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

# Hlavní běh
logger.info("Spouštím skript.")
connect()

layer1_x = 550
layer1_z = -900

turn_arm([-90, 0, 0, 0, -90, 0], 50)

# Nastaví pozici pro druhou vrstvu
fb.move(x=layer1_x, y=0, z=layer1_z) 
take_photo()
time.sleep(1)

# Snimani postupne po 1 (brokolice2) 4x v druhe vrstve
for x in range(4):
    layer1_x += 185
    logger.info(f"Pohyb {x+1}/4: Pohybuji na x={layer1_x}...")
    fb.move(x=layer1_x, y=0, z=layer1_z)
    take_photo()
    time.sleep(1)

# Nastaví pozici pro druhou vrstvu
turn_arm([0, 0, 0, 0, 0, 0], 50)

fb.move(x=0, y=0, z=layer1_z) 
take_photo()
time.sleep(1)
