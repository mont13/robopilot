import rtde_control
import rtde_receive


robot_ip = "192.168.0.96"
rtde_c = rtde_control.RTDEControlInterface(robot_ip)
rtde_r = rtde_receive.RTDEReceiveInterface(robot_ip)

tcp_offset = [0.0, 0.0, 0.15, 0.0, 0.0, 0.0]
rtde_c.setTcp(tcp_offset)

current_joints = rtde_r.getActualQ()
current_tcp = rtde_r.getActualTCPPose()

print("Current joint positions (rad):", [round(j, 4) for j in current_joints])
print("Current TCP pose [x,y,z,rx,ry,rz]:", [round(p, 4) for p in current_tcp])

rtde_c.disconnect()
