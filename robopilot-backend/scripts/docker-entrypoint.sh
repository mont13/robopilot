#!/bin/bash

set -e

# Activate our virtual environment
. /opt/pysetup/.venv/bin/activate

# Print some debug info
echo "Python environment ready"

# Evaluating passed command:
exec "$@"
