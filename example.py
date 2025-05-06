from robot import Robot
from GripperSocketControl.gripper import Gripper
import math
import time

START_SENSOR = 3
END_SENSOR = 2

CONVEYOR_ACTIVATE_PIN = 2
CONVEYOR_SPEED_PIN = 1


def degree_to_rad(arr):
    new_arr = []
    for angle in arr:
        new_arr.append(math.radians(angle))
    return new_arr


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

        my_gripper = Gripper("192.168.0.96", 30002)
        time.sleep(1)
        my_gripper.activate_and_wait()
        time.sleep(1)
        my_gripper.close_connection()
        time.sleep(1)

        if my_robot.connect():
            # program begin

            while input() != "q":
                my_robot.move_home()

                stop = False
                while not stop:
                    if my_robot.read_digital_input(START_SENSOR):
                        my_robot.write_digital_output(CONVEYOR_ACTIVATE_PIN, True)
                        my_robot.write_analog_output(CONVEYOR_SPEED_PIN, 0.3)

                    if my_robot.read_digital_input(END_SENSOR):
                        my_robot.write_digital_output(CONVEYOR_ACTIVATE_PIN, False)
                        my_robot.write_analog_output(CONVEYOR_SPEED_PIN, 0.0)
                        stop = True

                n1 = [-22.06, -99.35, -87.09, -80.57, 89.59, 338.07]
                my_robot.move_j(degree_to_rad(n1))

                my_robot.disconnect()

                # gripper OPEN

                my_gripper.connect()
                time.sleep(2)

                my_gripper.open_and_wait()
                time.sleep(2)

                my_gripper.close_connection()
                time.sleep(2)

                time.sleep(2)

                # move to POSITION

                my_robot.connect()

                n2 = [-22.03, -103.37, -100.23, -63.41, 89.64, 337.96]
                # n2 = [-21.87, -100.26, -95.86, -73.03, -87.19, 337.52]
                my_robot.move_l(degree_to_rad(n2), speed=0.025, acceleration=0.03)

                my_robot.disconnect()

                # gripper CLOSE

                my_gripper.connect()
                time.sleep(2)

                my_gripper.close_and_wait()
                time.sleep(2)

                my_gripper.close_connection()
                time.sleep(2)


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
                time.sleep(2)

                my_gripper.open_and_wait()
                time.sleep(2)

                my_gripper.close_connection()
                time.sleep(2)

                my_robot.connect()

                my_robot.move_l(degree_to_rad(n3))

                my_robot.move_home()

                # Disconnect
                my_robot.disconnect()

                my_gripper.connect()
                time.sleep(2)

                my_gripper.open_and_wait()
                time.sleep(2)

                my_gripper.close_connection()
                time.sleep(2)

                my_robot.connect()

            # program end
        else:
            print("\nCould not connect to the robot.")

        print("\nRobot object final state:")
        print(my_robot)

    except ValueError as e:
        print(f"Initialization Error: {e}")