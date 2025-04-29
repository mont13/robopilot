from __future__ import annotations

import math
import copy  # To ensure we don't modify the original default HOME_POINT

# Default home point for the robot (joint angles in radians)
# [Base, Shoulder, Elbow, Wrist1, Wrist2, Wrist3]
HOME_POINT = [-0.0, -math.pi / 2, 0.0, -math.pi / 2, 0.0, 0.0]
# Note: I adjusted the default HOME_POINT slightly to a more common 'zero'
# configuration often used with UR robots (-pi/2 for shoulder and wrist1).
# You can change this back to your original if needed:
# HOME_POINT = [-0.0, -math.pi, -0.0, -math.pi, 0.0, 0.0]


class Robot:
    """
    A class to represent and control a Universal Robot (UR).

    Attributes:
        ip (str): The IP address of the robot controller.
    """

    def __init__(self, ip: str, initial_offset: list[float] | None = None):
        """
        Initializes the Robot instance.

        Args:
            ip (str): The IP address of the robot controller.
            initial_offset (list[float] | None, optional):
                An initial offset, e.g., for a tool center point (TCP)
                [x, y, z, rx, ry, rz]. Defaults to None.
        """
        if not isinstance(ip, str) or not ip:  # Basic validation
            raise ValueError("IP address must be a non-empty string.")
        self.ip = ip
        # Use copy.deepcopy to ensure the instance has its own mutable list
        self._home_point: list[float] = copy.deepcopy(HOME_POINT)
        self._offset: list[float] | None = None  # Initialize offset

        # Set initial offset using the setter for validation
        if initial_offset is not None:
            self.offset = initial_offset  # Use the setter

        # Placeholder for actual robot connection object (e.g., from rtde_control)
        self._connection = None
        print(f"Robot object created for IP: {self.ip}")
        print(f"Default home point set to: {self._home_point}")
        print(f"Initial offset: {self._offset}")

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
        print(f"Home point updated to: {self._home_point}")

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
                raise ValueError(
                    "Offset must contain 6 values [x,y,z,rx,ry,rz].")
            if not all(isinstance(v, (int, float)) for v in new_offset):
                raise ValueError("All elements in offset must be numbers.")
            self._offset = list(new_offset)  # Store a copy
            print(f"Offset updated to: {self._offset}")
        else:
            raise TypeError("Offset must be a list of 6 numbers or None.")

    # --- Robot Control Methods (Placeholders) ---

    def connect(self):
        """
        Placeholder method to establish a connection to the robot.
        In a real implementation, this would use a library like rtde_control
        or urx to connect to self.ip.
        """
        print(f"Simulating connection to robot at {self.ip}...")
        # Example with rtde_control (requires installation: pip install rtde_control)
        try:
            import rtde_control
            self._connection = rtde_control.RTDEControlInterface(self.ip)
            print(f"Successfully connected to robot at {self.ip}.")
            return True
        except ImportError:
            print("Warning: 'rtde_control' library not found. Cannot connect.")
            self._connection = None
            return False
        except Exception as e:
            print(f"Error connecting to robot at {self.ip}: {e}")
            self._connection = None
            return False
        # self._connection = "Simulated Connection" # Placeholder
        # print("Connection successful (simulated).")
        # return True

    def disconnect(self):
        """
        Placeholder method to disconnect from the robot.
        """
        print(f"Simulating disconnection from robot at {self.ip}...")
        # Example with rtde_control
        if hasattr(self._connection, 'disconnect'):  # Check if it's an rtde obj
            self._connection.disconnect()
        self._connection = None
        # print("Disconnected (simulated).")

    def move_j(self, target_joints: list[float], speed: float = 0.5, acceleration: float = 1.0):
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

        # print(f"Simulating MOVEJ to: {target_joints}")
        print(f"  Speed: {speed} rad/s, Acceleration: {acceleration} rad/s^2")
        # Real implementation example (rtde_control):
        if self._connection:
            try:
                self._connection.moveJ(target_joints, speed, acceleration)
                print("move_j command sent successfully.")
            except Exception as e:
                print(f"Error during move_j: {e}")

    def move_l(self, target_pose: list[float], speed: float = 0.1, acceleration: float = 0.5):
        """
        Placeholder method to move the robot linearly to a target pose.

        Args:
            target_pose (list[float]): Target pose [x, y, z, rx, ry, rz]
                                      (meters and radians).
            speed (float): Tool speed (m/s).
            acceleration (float): Tool acceleration (m/s^2).
        """
        if not self._connection:
            print("Error: Robot not connected. Call connect() first.")
            return

        if not isinstance(target_pose, list) or len(target_pose) != 6:
            print("Error: target_pose must be a list of 6 numbers.")
            return

        # Apply offset if it exists (simple addition for position part)
        final_pose = list(target_pose)  # Make a copy
        if self._offset:
            # This is a simplistic offset application (additive).
            # Real TCP handling is more complex involving transformations.
            print(f"  Applying offset: {self._offset}")
            try:
                # Example: Adding positional offset - requires careful thought
                # on coordinate frames in a real system.
                final_pose[0] += self._offset[0]
                final_pose[1] += self._offset[1]
                final_pose[2] += self._offset[2]
                # Rotational offsets are more complex (matrix multiplication)
                # print(f"  (Note: Offset application is simplified in this simulation)")
            except Exception as e:
                print(f"  Warning: Could not apply offset - {e}")

        # Print pose potentially modified by offset
        print(f"Simulating MOVEL to: {final_pose}")
        print(f"  Speed: {speed} m/s, Acceleration: {acceleration} m/s^2")
        # Real implementation example (rtde_control):
        # if self._connection:
        #     try:
        #         # Note: Real TCP handling might involve setting TCP via
        #         # self._connection.setTcp(self._offset) before the move
        #         self._connection.moveL(target_pose, speed, acceleration) # Usually moves the current TCP
        #         print("move_l command sent successfully.")
        #     except Exception as e:
        #          print(f"Error during move_l: {e}")

    def move_home(self, speed: float = 0.5, acceleration: float = 1.0):
        """
        Moves the robot to its defined home position using move_j.
        """
        print("Moving to home position...")
        self.move_j(self._home_point, speed, acceleration)

    def get_current_joints(self) -> list[float] | None:
        """
        Placeholder method to get the current joint angles.
        Returns a list of 6 joint angles or None if not connected/error.
        """
        if not self._connection:
            print("Error: Robot not connected.")
            return None
        print("Simulating getting current joint angles...")
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
        # return [0.0] * 6 # Dummy return value

    def get_current_pose(self) -> list[float] | None:
        """
        Placeholder method to get the current TCP pose.
        Returns a list [x, y, z, rx, ry, rz] or None if not connected/error.
        """
        if not self._connection:
            print("Error: Robot not connected.")
            return None
        print("Simulating getting current TCP pose...")
        # Real implementation example (rtde_receive):
        try:
            import rtde_receive
            rtde_r = rtde_receive.RTDEReceiveInterface(self.ip)
            actual_tcp = rtde_r.getActualTCPPose()
            rtde_r.disconnect()
            return actual_tcp
        except Exception as e:
            print(f"Error getting TCP pose: {e}")
            return None
        # return [0.1, 0.2, 0.3, 0.0, 0.0, 0.0] # Dummy return value

    def set_teach_mode(self, freedrive=True):
        """
        If param is True, set robot to freemode.
        """
        if freedrive:
            self._connection.teachMode()
        else:
            self._connection.endTeachMode()

    def __str__(self) -> str:
        """String representation of the Robot object."""
        conn_status = "Connected (Simulated)" if self._connection else "Disconnected"
        return (f"Robot(IP='{self.ip}', "
                f"Home={self._home_point}, "
                f"Offset={self._offset}, "
                f"Status='{conn_status}')")

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (f"Robot(ip='{self.ip}', "
                f"initial_offset={self.offset})")  # Show initial args maybe


# --- Example Usage ---
if __name__ == "__main__":
    try:
        # Create a robot instance
        my_robot = Robot(ip="192.168.0.96")
        print(my_robot)

        # Get current home point
        home = my_robot.home_point
        print(f"\nCurrent Home Point: {home}")

        # Try setting an invalid home point
        try:
            my_robot.home_point = [1, 2, 3]
        except ValueError as e:
            print(f"\nError setting invalid home point: {e}")

        # Get current offset (should be None initially)
        print(f"\nCurrent Offset: {my_robot.offset}")

        # Set an offset (e.g., TCP)
        tcp_offset = [0, 0, 0.15, 0, 0, 0]  # 15cm Z offset, 90 deg Z rotation
        my_robot.offset = tcp_offset
        print(f"Get New Offset: {my_robot.offset}")

        # --- Simulate Movement ---
        print("\n--- Simulating Robot Movement ---")
        if my_robot.connect():
            # Get simulated current state
            print("Current Joints:", my_robot.get_current_joints())
            print("Current Pose:", my_robot.get_current_pose())

            # Move home
            my_robot.move_home(speed=1.0)

            joint_angles = my_robot.get_current_joints()

            if joint_angles is not None:
                for i in range(4):
                    if i % 2 == 0:
                        joint_angles[5] += math.pi
                        joint_angles[4] += math.pi
                        joint_angles[0] += math.pi
                    else:
                        joint_angles[5] -= math.pi
                        joint_angles[4] -= math.pi
                        joint_angles[0] -= math.pi
                    my_robot.move_j(joint_angles, speed=0.2)

            # Move home
            my_robot.move_home(speed=1.0)
            # Disconnect
            my_robot.disconnect()
        else:
            print("\nCould not connect to the robot (simulation).")

        print("\nRobot object final state:")
        print(my_robot)

    except ValueError as e:
        print(f"Initialization Error: {e}")
