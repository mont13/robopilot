import rtde_control
import rtde_receive
import rtde_io
import time
import math
import threading
import speech_recognition as sr

# INIT

HOME_POINT = [-0.0, -1.5708, -0.0, -1.5708, 0.0, 0.0]

robot_ip = "192.168.0.96"
rtde_c = rtde_control.RTDEControlInterface(robot_ip)
rtde_r = rtde_receive.RTDEReceiveInterface(robot_ip)
tcp_offset = [0.0, 0.0, 0.15, 0.0, 0.0, 0.0]
rtde_c.setTcp(tcp_offset)

# Get current position before movement
current_joints = rtde_r.getActualQ()
current_tcp = rtde_r.getActualTCPPose()

print("Current joint positions (rad):", [round(j, 4) for j in current_joints])
print("Current TCP pose [x,y,z,rx,ry,rz]:", [round(p, 4) for p in current_tcp])

stop_event = threading.Event()

# Voice Recognition Function
def voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Say 'start' to begin robot movement or 'stop' to end:")
        audio = recognizer.listen(source)

    try:
        command = recognizer.recognize_google(audio).lower()
        print(f"🗣️ You said: '{command}'")
        return command
    except sr.UnknownValueError:
        print("⚠️ Could not understand audio")
    except sr.RequestError as e:
        print(f"⚠️ Could not request results from service; {e}")

    return ""

# Wait for "stop" voice command
def cekani_na_vstup():
    while not stop_event.is_set():
        command = voice_input()
        if "stop" in command:
            print("🛑 Pohyb zastaven hlasovým příkazem.")
            rtde_c.stopJ()
            stop_event.set()

# Robot joint movement function
def pohyb_kloubu():
    print("▶️ Čekám na hlasový příkaz 'start'...")
    while not stop_event.is_set():
        command = voice_input()
        if "start" in command:
            print("▶️ Začínám pohyb kloubu...")
            joint_angles = rtde_r.getActualQ()

            while not stop_event.is_set():
                joint_angles[5] += math.pi
                rtde_c.moveJ(joint_angles, speed=0.3,
                             acceleration=0.5, asynchronous=True)
                time.sleep(0.1)

vlákno_pohyb = threading.Thread(target=pohyb_kloubu)
vlákno_vstup = threading.Thread(target=cekani_na_vstup)

vlákno_pohyb.start()
vlákno_vstup.start()

vlákno_pohyb.join()
vlákno_vstup.join()

rtde_c.disconnect()
