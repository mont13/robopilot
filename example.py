from robot import Robot
from GripperSocketControl.gripper import Gripper
import math
import time

DELAY = 0.5

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
        # home = my_robot.home_point

        # Try setting an invalid home point
        # try:
        #     my_robot.home_point = [1, 2, 3]
        # except ValueError as e:
        #     print(f"\nError setting invalid home point: {e}")

        # Get current offset (should be None initially)

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

            while input("press any key to continue, otherwise q") != "q":
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
                my_robot.move_l(degree_to_rad(n2), speed=0.025, acceleration=0.03)

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

    except ValueError as e:
        print(f"Initialization Error: {e}")