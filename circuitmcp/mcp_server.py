"""
MCP (Model Context Protocol) server implementation for circuit simulation.
This file implements a server using the official Anthropic MCP Python SDK.
"""

import os
import tempfile
import logging
from typing import List, Dict, Any, Optional, Union
import math

# Use our mock implementation instead of the official SDK
from .mock_mcp import FastMCP

# Import PySpice for circuit simulation
from PySpice.Spice.Netlist import Circuit as SpiceCircuit
from PySpice.Spice.NgSpice.Shared import NgSpiceShared
from PySpice.Unit import *

# Import SchemDraw for schematic drawing
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for matplotlib
import schemdraw
import schemdraw.elements as elm

from .circuit import Circuit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create an MCP server with a descriptive name
mcp = FastMCP("Circuit Simulation MCP Server")

# In-memory storage for circuits
# In a production environment, you might want to use a database
circuits = {}
next_circuit_id = 1

# Create output directory for schematics
os.makedirs("schematics", exist_ok=True)

# MCP Tools: Functions that perform actions

@mcp.tool()
def create_circuit(name: Optional[str] = None, components: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Create a new circuit.
    
    Args:
        name: Optional name for the circuit
        components: Optional list of initial components
        
    Returns:
        Dictionary with circuit details
    """
    global next_circuit_id
    
    circuit = Circuit(circuit_id=next_circuit_id, name=name)
    
    # Add initial components if provided
    if components:
        for comp in components:
            circuit.add_component(
                comp["type"],
                comp["nodes"],
                comp.get("value"),
                comp.get("parameters")
            )
            
    # Store the circuit
    circuits[next_circuit_id] = circuit
    next_circuit_id += 1
    
    return circuit.to_dict()

@mcp.tool()
def add_component(
    circuit_id: int, 
    component_type: str, 
    nodes: List[str], 
    value: Optional[float] = None,
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Add a component to an existing circuit.
    
    Args:
        circuit_id: ID of the circuit to modify
        component_type: Component type (R, C, L, V, I, D, Q, M, X, U)
        nodes: List of node identifiers
        value: Component value (depends on type)
        parameters: Additional parameters for the component
        
    Returns:
        Updated circuit details
    """
    if circuit_id not in circuits:
        return {"error": f"Circuit {circuit_id} not found"}
    
    circuit = circuits[circuit_id]
    
    # Add the component
    circuit.add_component(
        component_type,
        nodes,
        value,
        parameters
    )
    
    return circuit.to_dict()

@mcp.tool()
def remove_component(circuit_id: int, component_name: str) -> Dict[str, Any]:
    """
    Remove a component from a circuit.
    
    Args:
        circuit_id: ID of the circuit to modify
        component_name: Name of component to remove (e.g., "R1")
        
    Returns:
        Updated circuit details or error
    """
    if circuit_id not in circuits:
        return {"error": f"Circuit {circuit_id} not found"}
    
    circuit = circuits[circuit_id]
    removed = circuit.remove_component(component_name)
    
    if not removed:
        return {"error": f"Component {component_name} not found"}
    
    return circuit.to_dict()

@mcp.tool()
def update_circuit(
    circuit_id: int,
    name: Optional[str] = None,
    components: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Update an existing circuit's components and/or name.
    
    Args:
        circuit_id: ID of the circuit to update
        name: Optional new name for the circuit
        components: Optional new components list
        
    Returns:
        Updated circuit details or error
    """
    if circuit_id not in circuits:
        return {"error": f"Circuit {circuit_id} not found"}
        
    circuit = circuits[circuit_id]
    
    # Update name if provided
    if name is not None:
        circuit.name = name
        
    # Update components if provided
    if components is not None:
        circuit.update_components(components)
        
    return circuit.to_dict()

@mcp.tool()
def simulate_circuit(
    circuit_id: int, 
    analysis: str = "operating_point", 
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run a circuit simulation using PySpice/NGSpice.
    
    Args:
        circuit_id: ID of the circuit to simulate
        analysis: Type of analysis ("operating_point", "dc", "ac", "transient")
        params: Parameters for the simulation (depends on analysis type)
        
    Returns:
        Simulation results (node voltages, branch currents, etc.)
    """
    if circuit_id not in circuits:
        return {"error": f"Circuit {circuit_id} not found"}
    
    circuit = circuits[circuit_id]
    
    try:
        # Run the simulation using the Circuit object's simulate method
        result = circuit.simulate(
            analysis=analysis,
            sim_params=params or {}
        )
        return result
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.exception(f"Simulation error: {str(e)}")
        return {"error": f"Simulation failed: {str(e)}"}

@mcp.tool()
def generate_schematic(circuit_id: int, format: str = "png") -> Dict[str, Any]:
    """
    Generate a schematic image of the circuit.
    
    Args:
        circuit_id: ID of the circuit to visualize
        format: Image format (png or svg)
        
    Returns:
        Dictionary with filepath to the generated image
    """
    if circuit_id not in circuits:
        return {"error": f"Circuit {circuit_id} not found"}
    
    # Validate format
    format = format.lower()
    if format not in ("png", "svg"):
        return {"error": "Format must be 'png' or 'svg'"}
    
    circuit = circuits[circuit_id]
    
    # Define output filepath
    filepath = f"schematics/circuit_{circuit_id}_v{circuit.version}.{format}"
    
    try:
        # Generate schematic using the Circuit object's draw_schematic method
        circuit.draw_schematic(filepath)
        
        return {
            "filepath": filepath,
            "message": f"Schematic generated for circuit {circuit_id} (version {circuit.version})"
        }
    except Exception as e:
        logger.exception(f"Image generation error: {str(e)}")
        return {"error": f"Failed to generate image: {str(e)}"}

@mcp.tool()
def add_uvx_component(
    circuit_id: int,
    nodes: List[str],
    uvx_type: str,
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Add a Universal Verification Xcomponent (UVX) to a circuit.
    
    Args:
        circuit_id: ID of the circuit to modify
        nodes: List of node identifiers for the component
        uvx_type: Type of UVX component (opamp, comparator, adc, dac, etc.)
        parameters: Additional parameters for the UVX component
        
    Returns:
        Updated circuit details or error
    """
    if circuit_id not in circuits:
        return {"error": f"Circuit {circuit_id} not found"}
    
    circuit = circuits[circuit_id]
    
    # Create parameters dict with uvx_type
    uvx_params = {
        "uvx_type": uvx_type,
    }
    
    # Add any additional parameters
    if parameters:
        uvx_params.update(parameters)
    
    # Add the UVX component (component type starts with U)
    circuit.add_component("U", nodes, parameters=uvx_params)
    
    return circuit.to_dict()

@mcp.tool()
def delete_circuit(circuit_id: int) -> Dict[str, Any]:
    """
    Delete a circuit and all its data.
    
    Args:
        circuit_id: ID of the circuit to delete
        
    Returns:
        Success message or error
    """
    if circuit_id not in circuits:
        return {"error": f"Circuit {circuit_id} not found"}
    
    # Delete the circuit
    del circuits[circuit_id]
    
    return {"message": f"Circuit {circuit_id} deleted successfully"}

# MCP Resources: Data sources that can be read

@mcp.resource("circuits")
def list_circuits() -> List[Dict[str, Any]]:
    """
    List all available circuits.
    
    Returns:
        List of circuit summary information
    """
    return [
        {
            "id": circuit.id,
            "name": circuit.name,
            "version": circuit.version,
            "components_count": len(circuit.components)
        }
        for circuit in circuits.values()
    ]

@mcp.resource("circuit/{circuit_id}")
def get_circuit_details(circuit_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a specific circuit.
    
    Args:
        circuit_id: ID of the circuit
        
    Returns:
        Complete circuit details or error
    """
    if circuit_id not in circuits:
        return {"error": f"Circuit {circuit_id} not found"}
        
    circuit = circuits[circuit_id]
    return circuit.to_dict()

@mcp.resource("circuit/{circuit_id}/versions")
def get_circuit_versions(circuit_id: int) -> Dict[str, Any]:
    """
    Get version history of a circuit.
    
    Args:
        circuit_id: ID of the circuit
        
    Returns:
        List of available versions or error
    """
    if circuit_id not in circuits:
        return {"error": f"Circuit {circuit_id} not found"}
        
    circuit = circuits[circuit_id]
    
    # Collect all versions (history + current)
    versions = [record["version"] for record in circuit.history]
    versions.append(circuit.version)  # Add current version
    
    return {
        "id": circuit.id,
        "name": circuit.name,
        "current_version": circuit.version,
        "versions": versions
    }

# MCP Prompts: Pre-defined templates for interactions

@mcp.prompt()
def create_rc_filter():
    """Instructions for creating a simple RC low-pass filter circuit"""
    return """
    Let's create a simple RC low-pass filter circuit. This circuit consists of a resistor and capacitor in series,
    with the output taken across the capacitor.
    
    Here are the steps:
    1. Create a new circuit
    2. Add a voltage source (V1) between node 1 and ground (node 0)
    3. Add a resistor (R1) between nodes 1 and 2
    4. Add a capacitor (C1) between node 2 and ground
    5. Run an operating point analysis to check the DC voltages
    6. Generate a schematic to visualize the circuit
    
    Let me help you implement this.
    """

@mcp.prompt()
def create_common_emitter_amplifier():
    """Instructions for creating a BJT common emitter amplifier circuit"""
    return """
    Let's create a BJT common emitter amplifier circuit. This circuit uses a bipolar junction transistor (BJT)
    in a common emitter configuration to amplify signals.
    
    Here are the steps:
    1. Create a new circuit
    2. Add a DC voltage source (VCC) between node "vcc" and ground
    3. Add collector resistor (RC) between "vcc" and "collector"
    4. Add emitter resistor (RE) between "emitter" and ground
    5. Add base resistors for biasing (R1, R2)
    6. Add input capacitor (Cin) and output capacitor (Cout) for AC coupling
    7. Add a BJT transistor (Q1) with collector, base, and emitter nodes
    8. Run a DC operating point analysis to check biasing
    9. Run an AC analysis to check frequency response
    10. Generate a schematic to visualize the circuit
    
    Let me help you implement this.
    """

@mcp.prompt()
def run_transient_analysis():
    """Instructions for running a transient analysis on a circuit"""
    return """
    I'll help you run a transient analysis to see how your circuit behaves over time.
    
    Transient analysis requires these parameters:
    - step_time: The time step for simulation (e.g., 1e-6 for 1µs)
    - end_time: The duration to simulate (e.g., 1e-3 for 1ms)
    
    For meaningful results, your circuit should include time-varying sources or initial conditions.
    For example, you might want to:
    
    1. Add a pulse or sine voltage source instead of a DC source
    2. Run the simulation with appropriate time parameters
    3. Analyze the results to see how node voltages change over time
    
    Let's run a transient analysis on your circuit and analyze the results.
    """

@mcp.prompt()
def create_opamp_circuit():
    """Instructions for creating an operational amplifier circuit using UVX components"""
    return """
    Let's create a circuit with an operational amplifier (op-amp) using the UVX component system.
    
    Here are the steps:
    1. Create a new circuit
    2. Add power supply voltages (+V and -V)
    3. Add input components (resistors, capacitors, voltage sources)
    4. Add an op-amp UVX component with appropriate nodes
    5. Add feedback components (typically resistors)
    6. Run a simulation to analyze the circuit behavior
    7. Generate a schematic to visualize the circuit
    
    UVX components are special components in our circuit simulator that model complex devices
    like op-amps, comparators, ADCs, and DACs. They provide realistic behavior without needing
    to model all the internal transistors.
    
    Let me help you implement this.
    """

# Modified run method to support host and port
def run(host: str = "127.0.0.1", port: int = 8000):
    """
    Run the MCP server.
    
    Args:
        host: Host address to bind the server
        port: Port to bind the server
    """
    print(f"Starting Circuit Simulation MCP Server on {host}:{port}")
    print(f"Available tools: {list(mcp.tools.keys())}")
    print(f"Available resources: {list(mcp.resources.keys())}")
    print(f"Available prompts: {list(mcp.prompts.keys())}")
    # In our mock implementation, we don't actually start a server
    # In a real implementation with the Anthropic SDK, this would start the server
    # For now, we just print the message

# Attach the run method to the mcp object
mcp.run = run

# If this module is executed directly, run the MCP server
if __name__ == "__main__":
    print("Starting Circuit Simulation MCP Server...")
    # This will run the MCP server
    mcp.run() 