#!/bin/bash
# Mock Server Startup Script for Linux/macOS
# Usage: ./start.sh <mock_name> [options]
# Example: ./start.sh backend --port 8080 --log-level DEBUG
# Help: ./start.sh --help

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for help flag first (before mock name)
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Mock Server Startup Script"
    echo ""
    echo "Usage: ./start.sh <mock_name> [options]"
    echo ""
    echo "Arguments:"
    echo "  mock_name    Name of the mock configuration directory in mocks/"
    echo ""
    echo "Available mocks:"
    ls -1 "$SCRIPT_DIR/mocks/" 2>/dev/null | while read -r dir; do
        [ -d "$SCRIPT_DIR/mocks/$dir" ] && echo "  $dir"
    done
    echo ""
    echo "Server options (passed to main.py):"
    echo ""
    # Activate venv and show main.py help
    if [ -d "$SCRIPT_DIR/venv" ]; then
        source "$SCRIPT_DIR/venv/bin/activate"
    fi
    cd "$SCRIPT_DIR/server"
    python main.py --help
    exit 0
fi

# Get mock name (first argument)
MOCK_NAME="${1:-}"

# Validate mock name
if [ -z "$MOCK_NAME" ]; then
    echo "Error: Mock name is required"
    echo "Usage: ./start.sh <mock_name> [options]"
    echo ""
    echo "Available mocks:"
    ls -1 "$SCRIPT_DIR/mocks/" 2>/dev/null | while read -r dir; do
        [ -d "$SCRIPT_DIR/mocks/$dir" ] && echo "  $dir"
    done
    echo ""
    echo "Use ./start.sh --help for more information"
    exit 1
fi

# Check if mock directory exists
MOCK_DIR="$SCRIPT_DIR/mocks/$MOCK_NAME"
if [ ! -d "$MOCK_DIR" ]; then
    echo "Error: Mock directory not found: $MOCK_DIR"
    echo ""
    echo "Available mocks:"
    ls -1 "$SCRIPT_DIR/mocks/" 2>/dev/null | while read -r dir; do
        [ -d "$SCRIPT_DIR/mocks/$dir" ] && echo "  $dir"
    done
    exit 1
fi

# Shift to remove mock name from arguments, keep the rest
shift

# Activate virtual environment
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "Activating virtual environment..."
    source "$SCRIPT_DIR/venv/bin/activate"
else
    echo "Warning: Virtual environment not found. Run: python3 -m venv venv && pip install -r requirements.txt"
fi

# Start the mock server
echo "Starting mock server for '$MOCK_NAME'..."
echo "Config directory: $MOCK_DIR"
echo ""

cd "$SCRIPT_DIR/server"
python main.py \
    --config-dir "$MOCK_DIR" \
    --endpoints-file endpoints.py \
    --config-file config.py \
    "$@"
