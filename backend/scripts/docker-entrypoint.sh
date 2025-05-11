#!/bin/bash

set -e

# Activate our virtual environment
. /opt/pysetup/.venv/bin/activate

# Make sure the library path includes piper libraries
export LD_LIBRARY_PATH="/usr/local/lib:/usr/local/lib/piper_phonemize:${LD_LIBRARY_PATH}"

# Print some debug info
echo "Checking for piper-tts installation..."
pip list | grep piper
echo "Checking library paths..."
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
ls -la /usr/local/lib/piper_phonemize || echo "No piper_phonemize directory found"

# Evaluating passed command:
exec "$@"
