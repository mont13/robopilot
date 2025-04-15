import socket
from gripper_methods_def import create_command


def open_and_wait(s: socket.socket):
    """
    Open gripper.
    """
    s.send(create_command(
        '$ 3 "rq_open_and_wait()"\n   rq_open_and_wait()').encode("utf8"))


def close_and_wait(s: socket.socket):
    """
    Close gripper.
    """
    s.send(create_command(
        '$ 3 "rq_close_and_wait()"\n   rq_close_and_wait()').encode("utf8"))
