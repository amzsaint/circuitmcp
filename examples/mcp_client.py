#!/usr/bin/env python3
"""
MCP Client Example for Circuit Simulation

This script demonstrates how to use the Anthropic MCP Python SDK to connect to
and interact with the Circuit Simulation MCP Server.
"""

import asyncio
from typing import Dict, List, Any, Optional
import os
import sys
import json

# Add parent directory to path to import Circuit Simulation MCP Server
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our mock implementation of the MCP SDK
from circuitmcp.mock_mcp import ClientSession, StdioServerParameters, AsyncExitStack

class CircuitMCPClient:
    """MCP client for interacting with the Circuit Simulation MCP Server"""
    
    def __init__(self):
        self.session = None
        self.exit_stack = None
        
    async def connect(self):
        """Connect to the circuit simulation MCP server"""
        server_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                     "circuitmcp", "mcp_server.py")
        
        self.exit_stack = AsyncExitStack()
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(StdioServerParameters(["python", server_script]))
        )
        print("Connected to Circuit Simulation MCP Server")
        
    async def close(self):
        """Close the MCP client session"""
        if self.exit_stack:
            await self.exit_stack.aclose()
            print("Disconnected from Circuit Simulation MCP Server")
    
    async def create_circuit(self, name: Optional[str] = None, 
                            components: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Create a new circuit"""
        params = {}
        if name:
            params["name"] = name
        if components:
            params["components"] = components
            
        result = await self.session.call_tool("create_circuit", params)
        return result
    
    async def add_component(self, circuit_id: int, component_type: str, nodes: List[str], 
                           value: Optional[float] = None, 
                           parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add a component to an existing circuit"""
        params = {
            "circuit_id": circuit_id,
            "component_type": component_type,
            "nodes": nodes
        }
        
        if value is not None:
            params["value"] = value
        if parameters:
            params["parameters"] = parameters
            
        result = await self.session.call_tool("add_component", params)
        return result
    
    async def add_uvx_component(self, circuit_id: int, nodes: List[str], uvx_type: str,
                               parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add a UVX component to a circuit"""
        params = {
            "circuit_id": circuit_id,
            "nodes": nodes,
            "uvx_type": uvx_type
        }
        
        if parameters:
            params["parameters"] = parameters
            
        result = await self.session.call_tool("add_uvx_component", params)
        return result
    
    async def simulate(self, circuit_id: int, analysis: str = "operating_point",
                      params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run a simulation on a circuit"""
        sim_params = {
            "circuit_id": circuit_id,
            "analysis": analysis
        }
        
        if params:
            sim_params["params"] = params
            
        result = await self.session.call_tool("simulate_circuit", sim_params)
        return result
    
    async def generate_schematic(self, circuit_id: int, format: str = "png") -> Dict[str, Any]:
        """Generate a schematic image of the circuit"""
        result = await self.session.call_tool("generate_schematic", {
            "circuit_id": circuit_id,
            "format": format
        })
        return result
    
    async def get_all_circuits(self) -> List[Dict[str, Any]]:
        """Get a list of all available circuits"""
        return await self.session.get_resource("circuits")
    
    async def get_circuit_details(self, circuit_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific circuit"""
        return await self.session.get_resource(f"circuit/{circuit_id}")


async def create_rc_filter():
    """Example creating an RC filter circuit and running simulation"""
    client = CircuitMCPClient()
    
    try:
        await client.connect()
        
        # Create a new circuit
        circuit = await client.create_circuit("RC Low-Pass Filter")
        circuit_id = circuit["id"]
        print(f"Created circuit {circuit_id}: {circuit['name']}")
        
        # Add a 5V voltage source
        await client.add_component(circuit_id, "V", ["1", "0"], 5.0)
        print("Added voltage source V1")
        
        # Add a 1kΩ resistor
        await client.add_component(circuit_id, "R", ["1", "2"], 1000.0)
        print("Added resistor R1")
        
        # Add a 1µF capacitor
        await client.add_component(circuit_id, "C", ["2", "0"], 1e-6)
        print("Added capacitor C1")
        
        # Run an operating point analysis
        result = await client.simulate(circuit_id)
        print("\nSimulation results:")
        print(json.dumps(result, indent=2))
        
        # Generate a schematic
        schematic = await client.generate_schematic(circuit_id)
        print(f"\nSchematic generated: {schematic['filepath']}")
        
    finally:
        await client.close()


async def create_opamp_circuit():
    """Example creating an op-amp circuit using UVX component"""
    client = CircuitMCPClient()
    
    try:
        await client.connect()
        
        # Create a new circuit
        circuit = await client.create_circuit("Non-inverting Op-Amp")
        circuit_id = circuit["id"]
        print(f"Created circuit {circuit_id}: {circuit['name']}")
        
        # Add power supplies
        await client.add_component(circuit_id, "V", ["vcc", "0"], 15.0)
        await client.add_component(circuit_id, "V", ["0", "vee"], 15.0)
        print("Added power supplies")
        
        # Add input voltage
        await client.add_component(circuit_id, "V", ["in", "0"], 1.0)
        print("Added input voltage source")
        
        # Add feedback resistors
        await client.add_component(circuit_id, "R", ["out", "fb"], 10000.0)  # R1 (10kΩ)
        await client.add_component(circuit_id, "R", ["fb", "0"], 1000.0)     # R2 (1kΩ)
        print("Added feedback resistors")
        
        # Add op-amp UVX component
        await client.add_uvx_component(
            circuit_id, 
            ["out", "fb", "in", "vcc", "vee"],  # Output, -, +, V+, V-
            "opamp",
            {
                "model": "ideal",
                "gain": 1000000.0
            }
        )
        print("Added op-amp UVX component")
        
        # Run an operating point analysis
        result = await client.simulate(circuit_id)
        print("\nSimulation results:")
        print(json.dumps(result, indent=2))
        
        # Generate a schematic
        schematic = await client.generate_schematic(circuit_id)
        print(f"\nSchematic generated: {schematic['filepath']}")
        
    finally:
        await client.close()


if __name__ == "__main__":
    # Create and run an RC filter circuit
    print("=== Creating RC Filter Circuit ===")
    asyncio.run(create_rc_filter())
    
    print("\n=== Creating Op-Amp Circuit ===")
    asyncio.run(create_opamp_circuit()) 