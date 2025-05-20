# CircuitMCP

Circuit simulation capabilities exposed through Anthropic's Model Context Protocol (MCP).

## Overview

This project implements an MCP server for circuit simulation, allowing AI assistants to create, modify, and simulate electronic circuits. It uses PySpice for simulation and SchemDraw for generating schematic diagrams.

## Features

- **Circuit Creation**: Create circuits with various electronic components
- **Component Management**: Add, remove, and update components
- **Circuit Simulation**: Run operating point, DC, AC, and transient analyses
- **Schematic Generation**: Generate visual representations of circuits
- **UVX Components**: Support for Universal Verification Xcomponents (op-amps, etc.)

## Installation

### Quick Setup (Recommended)

We provide setup scripts that handle all installation steps automatically:

- **Linux/macOS**: `./setup_circuitmcp.sh`
- **Windows (CMD)**: `setup_circuitmcp.bat`
- **Windows (PowerShell)**: `.\setup_circuitmcp.ps1`

These scripts will:
1. Install required dependencies
2. Install NGSpice (or guide you through installation)
3. Set up a virtual environment (if desired)
4. Install CircuitMCP
5. Configure UVX for Cursor and Claude Desktop integration (if available)

### Using UVX in Cursor or Claude Desktop

The easiest way to install CircuitMCP is using UVX directly in Cursor or Claude Desktop:

```bash
# Install the package from GitHub
uvx install git+https://github.com/amzsaint/circuitmcp.git

# Or install by name once registered
uvx install circuitmcp

# Verify installation
uvx list | grep circuitmcp
```

### Claude Desktop Integration

To use CircuitMCP with Claude Desktop:

1. Install the UVX package:
   ```bash
   uvx install circuitmcp
   ```

2. Create an MCP configuration file (`mcp_config.json`):
   ```json
   {
     "servers": [
       {
         "name": "Circuit Simulator",
         "command": ["circuitmcp-server", "--host", "127.0.0.1", "--port", "8000"]
       }
     ]
   }
   ```

3. Start Claude Desktop with MCP configuration:
   ```bash
   claude-desktop --mcp-config=mcp_config.json
   ```

4. In Claude Desktop, you can now use circuit simulation capabilities:
   ```
   Please create a simple voltage divider circuit with a 9V source and two 10kΩ resistors.
   ```

### Manual Installation

You can also install manually:

1. Clone the repository:
   ```
   git clone https://github.com/amzsaint/circuitmcp.git
   cd circuitmcp
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install the package in development mode:
   ```
   pip install -e .
   ```

4. Install NGSpice (required for simulation):
   - macOS: `brew install ngspice`
   - Ubuntu: `apt-get install ngspice`
   - Windows: Download from the [NGSpice website](http://ngspice.sourceforge.net/download.html)

## Usage

### Running the Server

```bash
# Using the command-line script
circuitmcp-server

# With options
circuitmcp-server --debug --host 0.0.0.0 --port 8000
```

Or in Python:

```python
# Import the server
from circuitmcp import mcp

# Run the server
mcp.run(host="127.0.0.1", port=8000)
```

### Client Example

```python
# See examples/mcp_client.py for full examples
from examples.mcp_client import CircuitMCPClient
import asyncio

async def main():
    client = CircuitMCPClient()
    await client.connect()
    
    # Create a circuit
    circuit = await client.create_circuit("My Circuit")
    circuit_id = circuit["id"]
    
    # Add components
    await client.add_component(circuit_id, "V", ["in", "0"], 5.0)
    await client.add_component(circuit_id, "R", ["in", "out"], 1000.0)
    
    # Generate schematic
    schematic = await client.generate_schematic(circuit_id)
    print(f"Schematic generated: {schematic['filepath']}")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Cursor Integration

When installed via UVX, CircuitMCP can be used directly in Cursor:

1. Open Cursor and type `/install circuitmcp` or `/install git+https://github.com/amzsaint/circuitmcp.git`
2. Use the package in your Python code:
   ```python
   from circuitmcp import mcp, Circuit
   ```
3. Run the server with `/run circuitmcp-server`

## Testing

Run the test script to verify functionality:

```
python -m circuitmcp.test_mcp
```

## Project Structure

- `circuitmcp/`: Main package
  - `mcp_server.py`: MCP server implementation
  - `circuit.py`: Circuit class implementation
  - `mock_mcp.py`: Mock MCP SDK implementation
  - `test_mcp.py`: Test script
- `examples/`: Example client and usage
- `schematics/`: Generated circuit schematics

## License

MIT

## Note on NGSpice

This project requires NGSpice to be installed on your system for simulation capabilities. The schematic generation will work without NGSpice, but simulation features will be unavailable. 