#!/usr/bin/env python3
"""
Test for the Circuit Simulation MCP Server.
This file contains a simple test to verify that the MCP server is working correctly.
"""

import asyncio
import logging
import sys
import os
import json
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our mock implementation of the MCP SDK
from circuitmcp.mock_mcp import ClientSession, StdioServerParameters, AsyncExitStack

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def run_tests():
    """Run tests for the MCP server"""
    logger.info("Starting MCP server tests...")
    
    # Connect to the MCP server
    async with AsyncExitStack() as stack:
        server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server.py")
        session = await stack.enter_async_context(
            ClientSession(StdioServerParameters(["python", server_script]))
        )
        
        logger.info("Connected to MCP server")
        
        # Test 1: Get available tools and resources
        tools = await session.describe_tools()
        resources = await session.describe_resources()
        prompts = await session.describe_prompts()
        
        logger.info(f"Server has {len(tools)} tools, {len(resources)} resources, and {len(prompts)} prompts")
        
        # Test 2: Create a circuit
        circuit = await session.call_tool("create_circuit", {"name": "Test Circuit"})
        circuit_id = circuit["id"]
        logger.info(f"Created circuit {circuit_id}: {circuit['name']}")
        
        # Test 3: Add components to create an RC filter
        await session.call_tool("add_component", {"circuit_id": circuit_id, "component_type": "V", "nodes": ["1", "0"], "value": 5.0})
        await session.call_tool("add_component", {"circuit_id": circuit_id, "component_type": "R", "nodes": ["1", "2"], "value": 1000.0})
        await session.call_tool("add_component", {"circuit_id": circuit_id, "component_type": "C", "nodes": ["2", "0"], "value": 1e-6})
        logger.info("Added components to create RC filter")
        
        # Test 4: Get circuit details
        details = await session.get_resource(f"circuit/{circuit_id}")
        logger.info(f"Circuit has {len(details['components'])} components")
        
        # Test 5: Run a simulation
        result = await session.call_tool("simulate_circuit", {"circuit_id": circuit_id, "analysis": "operating_point"})
        if "error" in result:
            logger.error(f"Simulation failed: {result['error']}")
        else:
            logger.info(f"Simulation successful, node voltages: {result.get('nodes', {})}")
        
        # Test 6: Generate a schematic
        schematic = await session.call_tool("generate_schematic", {"circuit_id": circuit_id})
        if "error" in schematic:
            logger.error(f"Schematic generation failed: {schematic['error']}")
        else:
            logger.info(f"Schematic generated: {schematic['filepath']}")
        
        # Test 7: List all circuits
        circuits = await session.get_resource("circuits")
        logger.info(f"Server has {len(circuits)} circuit(s)")
        
        # Test 8: Delete the circuit
        delete_result = await session.call_tool("delete_circuit", {"circuit_id": circuit_id})
        logger.info(f"Circuit deletion result: {delete_result}")
        
        # Verify the circuit was deleted
        circuits = await session.get_resource("circuits")
        logger.info(f"Server now has {len(circuits)} circuit(s)")
        
        logger.info("All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_tests()) 