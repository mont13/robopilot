from __future__ import annotations
import math
import copy
import socket
import time


def degree_to_rad(arr):
    new_arr = []
    for angle in arr:
        new_arr.append(math.radians(angle))
    return new_arr


# Default home point for the robot (joint angles in radians)
# [Base, Shoulder, Elbow, Wrist1, Wrist2, Wrist3]
HOME_POINT = [-0.0, -math.pi / 2, 0.0, -math.pi / 2, 0.0, 0.0]


class Gripper:
    """Class to handle gripper communication and control."""

    def __init__(self, host, port=30002):
        """Initialize the gripper with host and port."""
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        """Connect to the gripper."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"✅ Successfully connected to gripper at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Error connecting to gripper: {e}")
            self.socket = None
            return False

    def close_connection(self):
        """Close the connection to the gripper."""
        if self.socket:
            self.socket.close()
            self.socket = None
            print("🛑 Gripper disconnected")

    def _send_command(self, command):
        """Send a command to the gripper."""
        if not self.socket:
            print("Error: Gripper not connected. Call connect() first.")
            return False

        try:
            self.socket.send(self._create_command(command).encode("utf8"))
            return True
        except Exception as e:
            print(f"Error sending command to gripper: {e}")
            return False

    def _create_command(self, command):
        """Create a command string for the gripper."""
        prefix = "def process():\n"
        suffix = "\nend\n"
        return prefix + command + suffix

    def open_and_wait(self):
        """Open gripper and wait for completion."""
        return self._send_command('$ 3 "rq_open_and_wait()"\n   rq_open_and_wait()')

    def close_and_wait(self):
        """Close gripper and wait for completion."""
        return self._send_command('$ 3 "rq_close_and_wait()"\n   rq_close_and_wait()')

    def activate_and_wait(self):
        """Activate gripper and wait for completion."""
        return self._send_command(
            '$ 3 "rq_activate_and_wait()"\n   rq_activate_and_wait()'
        )


class Robot:
    """
    A class to represent and control a Universal Robot (UR).

    Attributes:
        ip (str): The IP address of the robot controller.
    """

    def __init__(
        self, ip: str = "192.168.0.96", initial_offset: list[float] | None = None
    ):
        """
        Initializes the Robot instance.

        Args:
            ip (str): The IP address of the robot controller.
            initial_offset (list[float] | None, optional):
                An initial offset, e.g., for a tool center point (TCP)
                [x, y, z, rx, ry, rz]. Defaults to None.
        """
        self._connection_io = None
        self._connection_read = None
        if not isinstance(ip, str) or not ip:  # Basic validation
            raise ValueError("IP address must be a non-empty string.")
        self.ip = ip
        self.ip = ip
        # Use copy.deepcopy to ensure the instance has its own mutable list
        self._home_point: list[float] = copy.deepcopy(HOME_POINT)
        self._offset: list[float] | None = None  # Initialize offset

        # Set initial offset using the setter for validation
        if initial_offset is not None:
            self.offset = initial_offset  # Use the setter

        # Placeholder for actual robot connection object (e.g., from rtde_control)
        self._connection = None

    # --- Getters and Setters ---

    @property
    def home_point(self) -> list[float]:
        """Gets a copy of the robot's home point (joint angles)."""
        # Return a copy to prevent external modification of the internal list
        return list(self._home_point)

    @home_point.setter
    def home_point(self, new_home_point: list[float]):
        """
        Sets the robot's home point (joint angles).

        Args:
            new_home_point (list[float]): A list of 6 joint angles in radians.

        Raises:
            TypeError: If new_home_point is not a list.
            ValueError: If new_home_point does not contain 6 numbers.
        """
        if not isinstance(new_home_point, list):
            raise TypeError("Home point must be a list.")
        if len(new_home_point) != 6:
            raise ValueError("Home point must contain 6 joint angles.")
        if not all(isinstance(j, (int, float)) for j in new_home_point):
            raise ValueError("All elements in home_point must be numbers.")

        self._home_point = list(new_home_point)  # Store a copy

    @property
    def offset(self) -> list[float] | None:
        """
        Gets a copy of the robot's offset (e.g., TCP) or None if not set.
        """
        # Return a copy if it's a list, otherwise return None
        return list(self._offset) if self._offset is not None else None

    @offset.setter
    def offset(self, new_offset: list[float] | None):
        """
        Sets the robot's offset (e.g., TCP).

        Args:
            new_offset (list[float] | None):
                A list of 6 values [x, y, z, rx, ry, rz] representing the
                offset, or None to clear the offset.

        Raises:
            TypeError: If new_offset is not a list or None.
            ValueError: If new_offset is a list but does not contain 6 numbers.
        """
        if new_offset is None:
            self._offset = None
            print("Offset cleared.")
        elif isinstance(new_offset, list):
            if len(new_offset) != 6:
                raise ValueError("Offset must contain 6 values [x,y,z,rx,ry,rz].")
            if not all(isinstance(v, (int, float)) for v in new_offset):
                raise ValueError("All elements in offset must be numbers.")
            self._offset = list(new_offset)  # Store a copy
        else:
            raise TypeError("Offset must be a list of 6 numbers or None.")

    # --- Robot Control Methods ---

    def connect(self):
        """
        method to establish a connection to the robot.
        In a real implementation, this would use a library like rtde_control
        or urx to connect to self.ip.
        """
        print(f"🌐 Connecting to robot at {self.ip}...")
        # Example with rtde_control (requires installation: pip install rtde_control)
        try:
            import rtde_control
            import rtde_receive
            import rtde_io

            self._connection_read = rtde_receive.RTDEReceiveInterface(self.ip)
            self._connection = rtde_control.RTDEControlInterface(self.ip)
            self._connection_io = rtde_io.RTDEIOInterface(self.ip)
            print(f"✅ Successfully connected to robot at {self.ip}.")
            return True
        except ImportError:
            print("Warning: 'rtde_control' library not found. Cannot connect.")
            self._connection_read = None
            self._connection = None
            self._connection_io = None
            return False
        except Exception as e:
            print(f"Error connecting to robot at {self.ip}: {e}")
            self._connection_read = None
            self._connection = None
            self._connection_io = None
            return False

    def disconnect(self):
        """
        method to disconnect from the robot.
        """
        if hasattr(self._connection, "disconnect"):  # Check if it's an rtde obj
            self._connection.disconnect()
        if hasattr(self._connection_read, "disconnect"):  # Check if it's an rtde obj
            self._connection_read.disconnect()
        if hasattr(self._connection_io, "disconnect"):  # Check if it's an rtde obj
            self._connection_io.disconnect()
        self._connection = None
        self._connection_read = None
        self._connection_io = None
        print("🛑 Disconnected")

    def move_j(
        self, target_joints: list[float], speed: float = 0.4, acceleration: float = 0.5
    ):
        """
        Placeholder method to move the robot to target joint angles.

        Args:
            target_joints (list[float]): List of 6 target joint angles (radians).
            speed (float): Joint speed (rad/s).
            acceleration (float): Joint acceleration (rad/s^2).
        """
        if not self._connection:
            print("Error: Robot not connected. Call connect() first.")
            return

        if not isinstance(target_joints, list) or len(target_joints) != 6:
            print("Error: target_joints must be a list of 6 numbers.")
            return

        print(f"  Speed: {speed} rad/s, Acceleration: {acceleration} rad/s^2")
        # Real implementation example (rtde_control):
        if self._connection:
            try:
                self._connection.moveJ(target_joints, speed, acceleration)
                print("move_j command sent successfully.")
            except Exception as e:
                print(f"Error during move_j: {e}")

    def move_l(
        self, target_joints: list[float], speed: float = 0.1, acceleration: float = 0.2
    ):
        """
        Placeholder method to move the robot to target joint angles.

        Args:
            target_joints (list[float]): List of 6 target joint angles (radians).
            speed (float): Joint speed (rad/s).
            acceleration (float): Joint acceleration (rad/s^2).
        """
        if not self._connection:
            print("Error: Robot not connected. Call connect() first.")
            return

        if not isinstance(target_joints, list) or len(target_joints) != 6:
            print("Error: target_joints must be a list of 6 numbers.")
            return

        print(f"  Speed: {speed} rad/s, Acceleration: {acceleration} rad/s^2")
        if self._connection:
            try:
                self._connection.moveL_FK(target_joints, speed, acceleration)
                print("move_l command sent successfully.")
            except Exception as e:
                print(f"Error during move_l: {e}")

    def move_home(self, speed: float = 0.5, acceleration: float = 1.0):
        """
        Moves the robot to its defined home position using move_j.
        """
        print("🏚️ Moving to home position...")
        self.move_j(self._home_point, speed, acceleration)

    # --- Remaining methods from the original Robot class ---
    # ...existing code...

    def get_current_joints(self) -> list[float] | None:
        """
        Placeholder method to get the current joint angles.
        Returns a list of 6 joint angles or None if not connected/error.
        """
        if not self._connection:
            print("Error: Robot not connected.")
            return None
        # Real implementation example (rtde_receive):
        try:
            import rtde_receive

            rtde_r = rtde_receive.RTDEReceiveInterface(self.ip)
            actual_q = rtde_r.getActualQ()
            rtde_r.disconnect()
            return actual_q
        except Exception as e:
            print(f"Error getting joint angles: {e}")
            return None

    def get_current_pose(self) -> list[float] | None:
        """
        Placeholder method to get the current TCP pose.
        Returns a list [x, y, z, rx, ry, rz] or None if not connected/error.
        """
        if not self._connection:
            print("Error: Robot not connected.")
            return None
        # Real implementation example (rtde_receive):
        try:
            import rtde_receive

            rtde_r = rtde_receive.RTDEReceiveInterface(self.ip)
            actual_tcp = rtde_r.getActualTCPPose()
            rtde_r.disconnect()
            return actual_tcp
        except Exception as e:
            return None

    def set_teach_mode(self, freedrive=True):
        """
        If param is True, set robot to freemode.
        """
        if freedrive:
            self._connection.teachMode()
        else:
            self._connection.endTeachMode()

    def write_digital_output(self, index, value):
        """
        Write a digital output at the specified index.

        Args:
            index: Index of the digital output (0-7).
            value: True (1) for ON, False (0) for OFF.
        """
        if index < 0 or index > 7:
            raise ValueError("Index must be between 0 and 7.")

        self._connection_io.setStandardDigitalOut(index, value)

    def read_digital_input(self, index):
        """
        Read the value of a digital input at the specified index.

        Args:
            index: Index of the digital input (0-7).

        Returns:
            bool: True if the input is ON, False if OFF.
        """
        if index < 0 or index > 7:
            raise ValueError("Index must be between 0 and 7.")

        value = self._connection_read.getDigitalInState(index)
        return value

    def read_digital_output(self, index):
        """
        Read the value of a digital output at the specified index.

        Args:
            index: Index of the digital input (0-7).

        Returns:
            bool: True if the input is ON, False if OFF.
        """
        if index < 0 or index > 7:
            raise ValueError("Index must be between 0 and 7.")

        value = self._connection_read.getDigitalOutState(index)
        return value

    def write_analog_output(self, index, value):
        """
        Write an analog output at the specified index.

        Args:
            index: Index of the analog output (0-1).
            value: Analog value (0 to 1, corresponding to 0-10V).
        """
        if index < 0 or index > 1:
            raise ValueError("Index must be between 0 and 1.")

        if not (0 <= value <= 1):
            raise ValueError("Analog value must be between 0 and 1.")

        self._connection_io.setAnalogOutputVoltage(index, value)

    def read_analog_output(self, index=1):
        """
        Read an analog output at the specified index.

        Args:
            index: Index of the analog output (0-1).
            value: Analog value (0 to 1, corresponding to 0-10V).
        """
        if index < 0 or index > 1:
            raise ValueError("Index must be between 0 and 1.")

        if index == 1:
            return self._connection_read.getStandardAnalogOutput1()
        else:
            return self._connection_read.getStandardAnalogOutput0()

    def __str__(self) -> str:
        """String representation of the Robot object."""
        conn_status = "Connected" if self._connection else "Disconnected"
        return (
            f"Robot(IP='{self.ip}', "
            f"Home={self._home_point}, "
            f"Offset={self._offset}, "
            f"Status='{conn_status}')"
        )

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"Robot(ip='{self.ip}', initial_offset={self.offset})"

    @staticmethod
    def create_environment(robot_ip="192.168.0.96", gripper_ip=None):
        """
        Create a robot environment with default settings.

        Args:
            robot_ip (str): IP address of the robot
            gripper_ip (str): IP address of the gripper. If None, uses the robot_ip

        Returns:
            tuple: (Robot instance, Gripper instance)
        """
        # Create robot with default TCP offset
        tcp_offset = [0, 0, 0.15, 0, 0, 0]  # 15cm Z offset
        robot = Robot(ip=robot_ip, initial_offset=tcp_offset)

        # Create gripper using the same IP if not specified
        if gripper_ip is None:
            gripper_ip = robot_ip
        gripper = Gripper(gripper_ip, 30002)

        return robot, gripper


def run_conveyor_monitor(
    robot,
    start_sensor=3,
    end_sensor=2,
    conveyor_activate_pin=2,
    conveyor_speed_pin=1,
    conveyor_speed=0.3,
):
    """
    Monitor sensors and control a conveyor belt.

    Args:
        robot: Robot instance
        start_sensor: Digital input pin for the start sensor
        end_sensor: Digital input pin for the end sensor
        conveyor_activate_pin: Digital output pin for conveyor activation
        conveyor_speed_pin: Analog output pin for conveyor speed
        conveyor_speed: Speed value (0-1) for the conveyor

    Returns:
        bool: True when the end sensor is triggered
    """
    if not robot._connection:
        print("Error: Robot not connected. Call connect() first.")
        return False

    stop = False
    once = False

    while not stop:
        time.sleep(0.2)
        if robot.read_digital_input(start_sensor):
            if not once:
                print("▶️ Start conveyor")
                once = True
            robot.write_digital_output(conveyor_activate_pin, True)
            robot.write_analog_output(conveyor_speed_pin, conveyor_speed)

        if robot.read_digital_input(end_sensor):
            robot.write_digital_output(conveyor_activate_pin, False)
            robot.write_analog_output(conveyor_speed_pin, 0.0)
            stop = True
            print("⏹️ Stop conveyor")

    return True


def run_pick_and_place_cycle(robot, gripper, delay=0.5):
    """
    Run a complete pick and place cycle using the robot and gripper.

    Args:
        robot: Robot instance
        gripper: Gripper instance
        delay: Delay between operations in seconds
    """
    # Predefined positions in degrees
    pick_approach = [-22.06, -99.35, -87.09, -80.57, 89.59, 338.07]
    pick_position = [-22.03, -103.37, -100.23, -63.41, 89.64, 337.96]
    place_approach = [30.10, -89.07, 100.64, -102.14, -92.27, 30.4]
    place_position = [30.13, -86.02, 109.34, -113.88, -92.23, 30.33]

    # Move to home position
    if robot.connect() and gripper.connect():
        print("🤖 Robot connected and Gripper conected")
        print("🤖 Start run and place cycle")
        robot.move_home()

        # Run conveyor until object is detected
        run_conveyor_monitor(robot)

        # Move to approach position
        robot.move_j(degree_to_rad(pick_approach))
        robot.disconnect()

        # Open gripper
        gripper.connect()
        time.sleep(delay)
        gripper.open_and_wait()
        time.sleep(delay)
        gripper.close_connection()
        time.sleep(delay)

        # Move to pick position
        robot.connect()
        robot.move_l(degree_to_rad(pick_position), speed=0.025, acceleration=0.03)
        robot.disconnect()

        # Close gripper (grab object)
        gripper.connect()
        time.sleep(delay)
        gripper.close_and_wait()
        time.sleep(delay)
        gripper.close_connection()
        time.sleep(delay)

        # Return to approach position with object
        robot.connect()
        robot.move_l(degree_to_rad(pick_approach))

        # Move home and then to place approach
        robot.move_home()
        robot.move_j(degree_to_rad(place_approach))

        # Move to place position
        robot.move_l(degree_to_rad(place_position))
        robot.disconnect()

        # Open gripper (release object)
        gripper.connect()
        time.sleep(delay)
        gripper.open_and_wait()
        time.sleep(delay)
        gripper.close_connection()
        time.sleep(delay)

        # Return to approach position
        robot.connect()
        robot.move_l(degree_to_rad(place_approach))

        # Return home
        robot.move_home()
        robot.disconnect()

        print("🤖 Pick and place cycle completed")
        return True
    else:
        print("Failed to connect to robot")
        return False
