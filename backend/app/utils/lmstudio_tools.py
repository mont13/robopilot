"""
Tools for use with the LM Studio API and PraisonAI integration.

This module contains predefined tools that can be used with LM Studio and PraisonAI agents.
Tools are implemented as Python functions with docstrings that describe their functionality.
"""

from __future__ import annotations

import logging
import time

from app.utils.robot import Gripper, Robot, degree_to_rad

DELAY = 0.5

START_SENSOR = 3
END_SENSOR = 2

CONVEYOR_ACTIVATE_PIN = 2
CONVEYOR_SPEED_PIN = 1

# Set up logging
logger = logging.getLogger(__name__)


def robot_move_home() -> dict:
    """
    Move the robot to its home position.

    This function attempts to connect to the robot and move it to the home position.

    Returns:
        dict: A dictionary with success status and message
    """
    print("Moving robot to home position...")
    
    # Initialize robot
    try:
        my_robot = Robot(ip="192.168.0.96")
        print(my_robot)
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to initialize robot: {str(e)}. Check if robot is powered on and network is accessible.",
        }

    # Set an offset (e.g., TCP)
    tcp_offset = [0, 0, 0.15, 0, 0, 0]  # 15cm Z offset, 90 deg Z rotation
    my_robot.offset = tcp_offset

    # Initialize and test gripper connection
    try:
        my_gripper = Gripper("192.168.0.96", 30002)
        time.sleep(DELAY)
        my_gripper.activate_and_wait()
        time.sleep(DELAY)
        my_gripper.close_connection()
        time.sleep(DELAY)
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to initialize or activate gripper: {str(e)}. Check gripper power and network connection.",
        }

    # Test robot connection before proceeding
    try:
        if not my_robot.connect():
            return {
                "success": False,
                "message": "Failed to connect to robot. Check if robot is powered on, network cable is connected, and IP address 192.168.0.96 is reachable.",
            }
        
        # Move to home position
        my_robot.move_home()
        my_robot.disconnect()

        return {
            "success": True,
            "message": "Robot successfully moved to home position",
        }
    except Exception as e:
        try:
            my_robot.disconnect()
        except:
            pass
        return {
            "success": False,
            "message": f"Error during robot movement: {str(e)}. Robot may be in emergency stop or have mechanical issues.",
        }


def robot_run_pick_and_place_cycle():
    """
    Run a pick and place cycle with the robot.
    This function is a placeholder and should be implemented with actual robot control logic.
    """
    # Create a robot instance
    my_robot = Robot(ip="192.168.0.96")
    print(my_robot)

    # Set an offset (e.g., TCP)
    tcp_offset = [0, 0, 0.15, 0, 0, 0]  # 15cm Z offset, 90 deg Z rotation
    my_robot.offset = tcp_offset

    my_gripper = Gripper("192.168.0.96", 30002)
    time.sleep(DELAY)
    my_gripper.activate_and_wait()
    time.sleep(DELAY)
    my_gripper.close_connection()
    time.sleep(DELAY)

    if my_robot.connect():
        my_robot.move_home()

        stop = False
        once = False
        while not stop:
            time.sleep(0.2)
            if my_robot.read_digital_input(START_SENSOR):
                if not once:
                    print("▶️ Start conveyor")
                    once = True
                my_robot.write_digital_output(CONVEYOR_ACTIVATE_PIN, True)
                my_robot.write_analog_output(CONVEYOR_SPEED_PIN, 0.3)
                # time.sleep(0.1)

            if my_robot.read_digital_input(END_SENSOR):
                my_robot.write_digital_output(CONVEYOR_ACTIVATE_PIN, False)
                my_robot.write_analog_output(CONVEYOR_SPEED_PIN, 0.0)
                stop = True
                print("⏹️ Stop conveyor")
                # time.sleep(0.1)

        n1 = [-22.06, -99.35, -87.09, -80.57, 89.59, 338.07]
        my_robot.move_j(degree_to_rad(n1))

        my_robot.disconnect()

        # gripper OPEN

        my_gripper.connect()
        time.sleep(DELAY)

        my_gripper.open_and_wait()
        time.sleep(DELAY)

        my_gripper.close_connection()
        time.sleep(DELAY)

        time.sleep(DELAY)

        # move to POSITION

        my_robot.connect()

        n2 = [-22.03, -103.37, -100.23, -63.41, 89.64, 337.96]
        # n2 = [-21.87, -100.26, -95.86, -73.03, -87.19, 337.52]
        my_robot.move_l(degree_to_rad(n2), speed=0.5, acceleration=0.03)

        my_robot.disconnect()

        # gripper CLOSE

        my_gripper.connect()
        time.sleep(DELAY)

        my_gripper.close_and_wait()
        time.sleep(DELAY)

        my_gripper.close_connection()
        time.sleep(DELAY)

        # move HOME

        my_robot.connect()

        my_robot.move_l(degree_to_rad(n1))

        my_robot.move_home()

        n3 = [30.10, -89.07, 100.64, -102.14, -92.27, 30.4]
        my_robot.move_j(degree_to_rad(n3))

        n4 = [30.13, -86.02, 109.34, -113.88, -92.23, 30.33]
        my_robot.move_l(degree_to_rad(n4))

        my_robot.disconnect()

        my_gripper.connect()
        time.sleep(DELAY)

        my_gripper.open_and_wait()
        time.sleep(DELAY)

        my_gripper.close_connection()
        time.sleep(DELAY)

        my_robot.connect()

        my_robot.move_l(degree_to_rad(n3))

        my_robot.move_home()

        # Disconnect
        my_robot.disconnect()

        my_robot.connect()

    # program end
    else:
        print("\nCould not connect to the robot.")

    print("\nRobot object final state:")
    print(my_robot)


def robot_control_gripper() -> dict:
    """
    Demonstrate various gripper control operations.

    This function connects to the gripper and performs a sequence of operations:
    open, close, move to specific position, etc.

    Returns:
        dict: A dictionary with success status and message
    """
    # Initialize gripper
    try:
        my_gripper = Gripper("192.168.0.96", 30002)
        time.sleep(DELAY)
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to initialize gripper: {str(e)}. Check if gripper is powered on and network is accessible.",
        }

    try:
        # Test gripper connection and reset
        my_gripper.reset()
        time.sleep(2)
        my_gripper.activate_and_wait()
        time.sleep(1)

        # Open gripper to specific position
        my_gripper.move_and_wait_mm(distance=10)
        time.sleep(1)

        # Fully open and close
        my_gripper.open_and_wait()
        time.sleep(1)
        my_gripper.close_and_wait()
        time.sleep(1)

        # Close connection
        my_gripper.close_connection()

        return {
            "success": True,
            "message": "Gripper control sequence completed successfully",
        }
    except Exception as e:
        try:
            my_gripper.close_connection()
        except:
            pass
        return {
            "success": False,
            "message": f"Error controlling gripper: {str(e)}. Check gripper power, network connection, or if gripper is in fault state.",
        }


def robot_gripper_led_control(turn_on: bool = True) -> dict:
    """
    Control the LED on the gripper.

    Args:
        turn_on: Boolean indicating whether to turn the LED on (True) or off (False)

    Returns:
        dict: A dictionary with success status and message
    """
    # Initialize gripper
    try:
        my_gripper = Gripper("192.168.0.96", 30002)
        time.sleep(DELAY)
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to initialize gripper: {str(e)}. Check if gripper is powered on and network is accessible.",
        }

    try:
        # Test gripper connection and activate
        my_gripper.activate_and_wait()
        time.sleep(DELAY)

        if turn_on:
            my_gripper.gripper_led_on()
            message = "Gripper LED turned on"
        else:
            my_gripper.gripper_led_off()
            message = "Gripper LED turned off"

        time.sleep(DELAY)
        my_gripper.close_connection()

        return {
            "success": True,
            "message": message,
        }
    except Exception as e:
        try:
            my_gripper.close_connection()
        except:
            pass
        return {
            "success": False,
            "message": f"Error controlling gripper LED: {str(e)}. Check gripper connection or if gripper supports LED control.",
        }


def robot_move_to_specified_position(position_name: str) -> dict:
    """
    Move the robot to a specified predefined position.

    Args:
        position_name: String identifier for the predefined position
            Options: "pickup", "dropoff", "inspect"

    Returns:
        dict: A dictionary with success status and message
    """
    # Define positions first for validation
    positions = {
        "pickup": [-22.06, -99.35, -87.09, -80.57, 89.59, 338.07],
        "dropoff": [30.10, -89.07, 100.64, -102.14, -92.27, 30.4],
        "inspect": [0.0, -90.0, 90.0, -90.0, -90.0, 0.0],
    }

    if position_name not in positions:
        return {
            "success": False,
            "message": f"Unknown position: {position_name}. Available positions: {list(positions.keys())}",
        }

    # Initialize robot
    try:
        my_robot = Robot(ip="192.168.0.96")
        # Set an offset (e.g., TCP)
        tcp_offset = [0, 0, 0.15, 0, 0, 0]  # 15cm Z offset
        my_robot.offset = tcp_offset
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to initialize robot: {str(e)}. Check if robot is powered on and network is accessible.",
        }

    # Test robot connection before proceeding
    try:
        if not my_robot.connect():
            return {
                "success": False,
                "message": "Failed to connect to robot. Check if robot is powered on, network cable is connected, and IP address 192.168.0.96 is reachable.",
            }

        # Move to the specified position
        my_robot.move_j(degree_to_rad(positions[position_name]))
        my_robot.disconnect()

        return {
            "success": True,
            "message": f"Robot moved to {position_name} position",
        }
    except Exception as e:
        try:
            my_robot.disconnect()
        except:
            pass
        return {
            "success": False,
            "message": f"Error moving robot to {position_name}: {str(e)}. Robot may be in emergency stop or have mechanical issues.",
        }


def robot_reset_all() -> dict:
    """
    Reset both the robot and gripper to their initial states.

    This function:
    1. Moves the robot to home position
    2. Resets the gripper
    3. Activates the gripper
    4. Opens the gripper

    Returns:
        dict: A dictionary with success status and message
    """
    robot_success = False
    gripper_success = False
    errors = []

    # Initialize and reset robot
    try:
        my_robot = Robot(ip="192.168.0.96")
        # Set an offset (e.g., TCP)
        tcp_offset = [0, 0, 0.15, 0, 0, 0]  # 15cm Z offset
        my_robot.offset = tcp_offset

        if my_robot.connect():
            my_robot.move_home()
            my_robot.disconnect()
            robot_success = True
        else:
            errors.append("Failed to connect to robot. Check power and network connection.")
    except Exception as e:
        errors.append(f"Robot reset failed: {str(e)}. Check if robot is powered and network accessible.")

    # Initialize and reset gripper
    try:
        my_gripper = Gripper("192.168.0.96", 30002)
        time.sleep(DELAY)
        my_gripper.reset()
        time.sleep(2)
        my_gripper.activate_and_wait()
        time.sleep(1)
        my_gripper.open_and_wait()
        time.sleep(1)
        my_gripper.close_connection()
        gripper_success = True
    except Exception as e:
        errors.append(f"Gripper reset failed: {str(e)}. Check gripper power and network connection.")

    # Return appropriate response based on results
    if robot_success and gripper_success:
        return {
            "success": True,
            "message": "Robot and gripper reset successfully",
        }
    elif gripper_success and not robot_success:
        return {
            "success": False,
            "message": f"Gripper reset successfully, but robot failed: {errors[0]}",
        }
    elif robot_success and not gripper_success:
        return {
            "success": False,
            "message": f"Robot reset successfully, but gripper failed: {errors[-1]}",
        }
    else:
        return {
            "success": False,
            "message": f"Both robot and gripper reset failed: {'; '.join(errors)}",
        }
