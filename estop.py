import socket
import logging
import sys
import time

# --- Configuration ---
ROBOT_HOST = '192.168.0.96'  # <<< REPLACE WITH YOUR ROBOT'S IP
SECONDARY_PORT = 30002
COMMAND_TIMEOUT = 5  # Seconds to wait for connection/response

# --- Popup Message Configuration ---
POPUP_TITLE = "Remote Pause Request"
POPUP_MESSAGE = "Program execution paused by external command. Check control PC."
IS_WARNING = False  # Set True for yellow warning icon
# Set True for red error icon (usually forces Stop/Continue choice)
IS_ERROR = True
# If True, script waits for user interaction. If False, script continues after popup appears (less common use)
BLOCKING = True

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s:%(name)s:%(message)s')
_log = logging.getLogger(__name__)


def send_urscript_command(host, port, command):
    """Connects to the UR Secondary Interface and sends a URScript command."""
    _log.info(
        f"Attempting to connect to Secondary Interface at {host}:{port}...")
    try:
        # Use a 'with' statement for automatic socket closing
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(COMMAND_TIMEOUT)  # Set connection and read timeout
            sock.connect((host, port))
            _log.info("Connected to Secondary Interface.")

            # URScript commands need newline termination when sent via socket
            full_command = command + '\n'
            # Log without newline for clarity
            _log.info(f"Sending URScript command: {command}")
            sock.sendall(full_command.encode('utf-8'))

            # Port 30002 usually doesn't send acknowledgements for commands like popup.
            # We'll assume success if sendall() doesn't raise an error.
            time.sleep(0.1)  # Small delay can sometimes be helpful
            _log.info("Command sent successfully (no response expected).")
            return True

    except socket.timeout:
        _log.error(
            f"Timeout connecting or sending to Secondary Interface at {host}:{port}.")
        return False
    except socket.error as e:
        _log.error(f"Socket error communicating with Secondary Interface: {e}")
        return False
    except Exception as e:
        _log.error(f"An unexpected error occurred: {e}")
        return False


# --- Main Execution ---
if __name__ == "__main__":
    _log.warning("!!! INFO !!!")
    _log.warning(
        "This script will attempt to trigger a POPUP on the robot's Teach Pendant.")
    _log.warning(
        "This will PAUSE the currently running program and require USER INTERACTION at the pendant.")
    _log.warning("It is NOT a safety stop.")
    _log.warning("Ensure the robot is in a safe state before pausing.")

    # Construct the URScript popup command string
    # Note: Boolean values in URScript are 'True'/'False' (case-sensitive)
    ur_command = (
        f'popup("{POPUP_MESSAGE}", '
        f'title="{POPUP_TITLE}", '
        # Convert Python bool to URScript string
        f'warning={str(IS_WARNING)}, '
        f'error={str(IS_ERROR)}, '     # Convert Python bool to URScript string
        f'blocking={str(BLOCKING)})'  # Convert Python bool to URScript string
    )

    try:
        input(f"Press Enter to send POPUP command or Ctrl+C to abort...")
    except KeyboardInterrupt:
        _log.info("Operation aborted by user.")
        sys.exit(0)

    # Send the URScript popup command
    success = send_urscript_command(ROBOT_HOST, SECONDARY_PORT, ur_command)

    if success:
        _log.info("URScript popup command sent successfully.")
        _log.info("Robot program should be paused, check the Teach Pendant.")
    else:
        _log.error("Failed to send URScript popup command.")
        _log.error("Robot program may not have paused!")

    _log.info("Script finished.")
