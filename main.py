import rtde_control
import rtde_receive
import rtde_io
import time
import math
import threading

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


def cekani_na_vstup():
    input("🕹️ Stiskni Enter pro zastavení pohybu...\n")

    print("🛑 Pohyb zastaven.")
    rtde_c.stopJ()

    stop_event.set()  # vyšle signál druhému vláknu
    rtde_c.moveJ(HOME_POINT, speed=1)


def pohyb_kloubu():
    print("▶️ Začínám pohyb kloubu...")
    joint_angles = rtde_r.getActualQ()

    to_right = True

    while not stop_event.is_set():
        if to_right:
            joint_angles[5] += math.pi
            joint_angles[4] += math.pi
            joint_angles[0] += math.pi
            to_right = False
        else:
            joint_angles[5] -= math.pi
            joint_angles[4] -= math.pi
            joint_angles[0] -= math.pi
            to_right = True

        rtde_c.moveJ(joint_angles, speed=0.8)
        time.sleep(0.1)


# Init robot to home position
rtde_c.moveJ(HOME_POINT, speed=1)

vlákno_pohyb = threading.Thread(target=pohyb_kloubu)
vlákno_vstup = threading.Thread(target=cekani_na_vstup)

vlákno_pohyb.start()
vlákno_vstup.start()

vlákno_pohyb.join()
vlákno_vstup.join()

rtde_c.disconnect()
