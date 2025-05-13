#!/bin/bash

set -e

# Activate our virtual environment
. /opt/pysetup/.venv/bin/activate

# Make sure the library path includes piper and ur_rtde libraries
export LD_LIBRARY_PATH="/usr/local/lib:/usr/local/lib/piper_phonemize:/usr/local/lib/ur_rtde:${LD_LIBRARY_PATH}"

# Set environment variables for PraisonAI
# Use LM Studio as default provider, no API key required
export OPENAI_API_BASE=${LMSTUDIO_HOST:-"http://host.docker.internal:1234/v1"}
export OPENAI_API_KEY=${OPENAI_API_KEY:-"NA"}

# Print some debug info
echo "Checking for piper-tts installation..."
pip list | grep piper
echo "Checking for ur_rtde installation..."
pip list | grep ur_rtde
echo "Checking library paths..."
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
ls -la /usr/local/lib/piper_phonemize || echo "No piper_phonemize directory found"
ls -la /usr/local/lib/ur_rtde || echo "No ur_rtde directory found"

# Print PraisonAI environment
echo "PraisonAI environment:"
echo "OPENAI_API_BASE: $OPENAI_API_BASE"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:0:3}..." # Only show first few chars for security

# Evaluating passed command:
exec "$@"
