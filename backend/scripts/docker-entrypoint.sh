#!/bin/bash

set -e

# Activate our virtual environment
. /opt/pysetup/.venv/bin/activate

# Make sure the library path includes piper and ur_rtde libraries
export LD_LIBRARY_PATH="/usr/local/lib:/usr/local/lib/piper_phonemize:/usr/local/lib/ur_rtde:${LD_LIBRARY_PATH}"

# Print some debug info
echo "Checking for piper-tts installation..."
pip list | grep piper
echo "Checking for ur_rtde installation..."
pip list | grep ur_rtde

# Evaluating passed command:
exec "$@"
