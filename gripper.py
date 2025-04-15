import time
import pyRobotiqGripper


# Nahraďte skutečnou IP adresou vašeho UR kontroleru
ROBOT_IP = "192.168.0.96"  # Příklad IP adresy

# Vytvoření instance gripperu
# Standardně komunikuje na portu 502, což je výchozí pro Modbus TCP na UR
# Pokud máte více gripperů nebo nestandardní nastavení, může být potřeba specifikovat 'device_id'
gripper = pyRobotiqGripper.RobotiqGripper()

try:
    print(f"Připojování k robotu na adrese {ROBOT_IP}...")
    # Připojení ke gripperu (přes UR kontroler)
    gripper.connect(ROBOT_IP, 502)  # 502 je standardní Modbus TCP port
    print("Připojeno.")

    # Aktivace gripperu - NUTNÝ KROK PŘED POUŽITÍM!
    # Gripper se musí nejprve plně otevřít a zavřít, aby se zkalibroval.
    print("Aktivace gripperu...")
    if not gripper.is_active():
        gripper.activate()
        # Počkejte chvíli na dokončení aktivace
        time.sleep(2)
        if gripper.is_active():
            print("Gripper úspěšně aktivován.")
        else:
            print("Chyba: Gripper se nepodařilo aktivovat.")
            exit()  # Ukončení, pokud aktivace selhala
    else:
        print("Gripper je již aktivován.")

    # Získání a tisk stavu gripperu
    status = gripper.get_status()
    print(f"Stav gripperu: {status}")
    print(f"Aktuální pozice: {gripper.get_position()}")

    # Můžete také použít předdefinované funkce open/close
    print("Použití gripper.open()...")
    gripper.open()
    time.sleep(2)
    print(f"Pozice po gripper.open(): {gripper.get_position()}")

    print("Použití gripper.close()...")
    gripper.close()
    time.sleep(2)
    print(f"Pozice po gripper.close(): {gripper.get_position()}")


except Exception as e:
    print(f"Došlo k chybě: {e}")

finally:
    # Vždy je dobré se na konci odpojit
    print("Odpojování gripperu...")
    gripper.disconnect()
    print("Odpojeno.")
