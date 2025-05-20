#!/bin/bash
# This script demonstrates how to start Claude Desktop with CircuitMCP

# Check if CircuitMCP is installed
if ! command -v circuitmcp-server &> /dev/null; then
    echo "CircuitMCP is not installed. Installing now..."
    uvx install git+https://github.com/amzsaint/circuitmcp.git
fi

# Verify installation
echo "Checking CircuitMCP installation..."
uvx list | grep circuitmcp

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if Claude Desktop is installed
if ! command -v claude-desktop &> /dev/null; then
    echo "Claude Desktop is not installed. Please install Claude Desktop first."
    exit 1
fi

# Create the MCP configuration file if it doesn't exist
CONFIG_FILE="$SCRIPT_DIR/claude_desktop_mcp_config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating MCP configuration file..."
    cat > "$CONFIG_FILE" << EOL
{
  "servers": [
    {
      "name": "Circuit Simulator",
      "command": ["circuitmcp-server", "--host", "127.0.0.1", "--port", "8000"]
    }
  ]
}
EOL
fi

echo "Starting Claude Desktop with CircuitMCP server..."
echo "Configuration file: $CONFIG_FILE"
echo ""
echo "In Claude Desktop, you can ask to create and simulate circuits, for example:"
echo "  'Create a voltage divider circuit with a 9V source and two 10kΩ resistors.'"
echo ""

# Start Claude Desktop with the MCP configuration
claude-desktop --mcp-config="$CONFIG_FILE" 