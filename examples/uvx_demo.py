#!/usr/bin/env python3
"""
Demo script to show how to use CircuitMCP as an installed package.
"""

import asyncio
import sys
import logging
from circuitmcp import mcp
from circuitmcp.mock_mcp import ClientSession, StdioServerParameters, AsyncExitStack

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def create_and_visualize_circuit():
    """Create a simple voltage divider circuit and generate a schematic"""
    # Connect to the MCP server
    logger.info("Connecting to CircuitMCP server...")
    async with AsyncExitStack() as stack:
        session = await stack.enter_async_context(
            ClientSession(mcp)  # Direct connection to the mcp instance
        )
        
        logger.info("Connected to CircuitMCP server")
        
        # Create a new circuit
        circuit = await session.call_tool("create_circuit", {"name": "Voltage Divider"})
        circuit_id = circuit["id"]
        logger.info(f"Created circuit {circuit_id}: {circuit['name']}")
        
        # Add components to create a voltage divider
        await session.call_tool("add_component", {
            "circuit_id": circuit_id, 
            "component_type": "V", 
            "nodes": ["1", "0"], 
            "value": 9.0
        })
        logger.info("Added 9V source")
        
        await session.call_tool("add_component", {
            "circuit_id": circuit_id, 
            "component_type": "R", 
            "nodes": ["1", "2"], 
            "value": 10000.0
        })
        logger.info("Added 10kΩ resistor R1")
        
        await session.call_tool("add_component", {
            "circuit_id": circuit_id, 
            "component_type": "R", 
            "nodes": ["2", "0"], 
            "value": 10000.0
        })
        logger.info("Added 10kΩ resistor R2")
        
        # Generate a schematic
        schematic = await session.call_tool("generate_schematic", {
            "circuit_id": circuit_id
        })
        
        if "error" in schematic:
            logger.error(f"Schematic generation failed: {schematic['error']}")
        else:
            logger.info(f"Schematic generated: {schematic['filepath']}")
            
        # Get circuit details
        details = await session.get_resource(f"circuit/{circuit_id}")
        logger.info(f"Circuit details: {details}")
        
        logger.info("Demo completed successfully!")

if __name__ == "__main__":
    # Run the demo
    asyncio.run(create_and_visualize_circuit()) 