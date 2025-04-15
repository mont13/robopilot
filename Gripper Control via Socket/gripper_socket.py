import socket
import time

HOST = "192.168.0.96"
PORT = 30002

a = """def my_program():
    movel(p[0.3, 0.1, 0.2, 0, 3.14, 0], a=0.5, v=0.2)
end
my_program()"""

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

time.sleep(1)

f = open("./Gripper Control via Socket/gripper_open.script", "rb")
l = f.read(1024)

while l:
    s.send(l)
    l = f.read(1024)


time.sleep(1)

s.close()
