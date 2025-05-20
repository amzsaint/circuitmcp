"""
Test cases for the Circuit class.
"""

import unittest
import os
import tempfile
import math
from pathlib import Path

from circuitmcp.circuit import Circuit

class TestCircuit(unittest.TestCase):
    """Test cases for the Circuit class."""
    
    def setUp(self):
        """Set up test case."""
        self.circuit = Circuit(circuit_id=1, name="Test Circuit")
        
    def test_create_circuit(self):
        """Test circuit creation."""
        self.assertEqual(self.circuit.id, 1)
        self.assertEqual(self.circuit.name, "Test Circuit")
        self.assertEqual(self.circuit.version, 1)
        self.assertEqual(len(self.circuit.components), 0)
        
    def test_add_component(self):
        """Test adding components to a circuit."""
        # Add a resistor
        resistor = self.circuit.add_component("R", ["1", "2"], 1000)
        self.assertEqual(resistor["name"], "R1")
        self.assertEqual(resistor["type"], "R")
        self.assertEqual(resistor["nodes"], ["1", "2"])
        self.assertEqual(resistor["value"], 1000)
        
        # Add a capacitor
        capacitor = self.circuit.add_component("C", ["2", "0"], 1e-6)
        self.assertEqual(capacitor["name"], "C1")
        
        # Add a voltage source
        source = self.circuit.add_component("V", ["1", "0"], 5.0)
        self.assertEqual(source["name"], "V1")
        
        # Check total component count
        self.assertEqual(len(self.circuit.components), 3)
        
    def test_remove_component(self):
        """Test removing components from a circuit."""
        # Add some components
        self.circuit.add_component("R", ["1", "2"], 1000)
        self.circuit.add_component("C", ["2", "0"], 1e-6)
        
        # Remove the resistor
        result = self.circuit.remove_component("R1")
        self.assertTrue(result)
        self.assertEqual(len(self.circuit.components), 1)
        
        # Try to remove a non-existent component
        result = self.circuit.remove_component("X1")
        self.assertFalse(result)
        
    def test_update_components(self):
        """Test updating a circuit's components."""
        # Add initial components
        self.circuit.add_component("R", ["1", "2"], 1000)
        self.circuit.add_component("C", ["2", "0"], 1e-6)
        
        # Update components
        new_components = [
            {"type": "R", "nodes": ["1", "2"], "value": 2000},
            {"type": "L", "nodes": ["2", "0"], "value": 1e-3}
        ]
        self.circuit.update_components(new_components)
        
        # Check version increment
        self.assertEqual(self.circuit.version, 2)
        
        # Check new components
        self.assertEqual(len(self.circuit.components), 2)
        self.assertEqual(self.circuit.components[0]["type"], "R")
        self.assertEqual(self.circuit.components[0]["value"], 2000)
        self.assertEqual(self.circuit.components[1]["type"], "L")
        
        # Check history
        self.assertEqual(len(self.circuit.history), 1)
        self.assertEqual(self.circuit.history[0]["version"], 1)
        
    def test_to_dict(self):
        """Test circuit serialization to dict."""
        # Add a component
        self.circuit.add_component("R", ["1", "2"], 1000)
        
        # Convert to dict
        circuit_dict = self.circuit.to_dict()
        
        # Check dict content
        self.assertEqual(circuit_dict["id"], 1)
        self.assertEqual(circuit_dict["name"], "Test Circuit")
        self.assertEqual(circuit_dict["version"], 1)
        self.assertEqual(len(circuit_dict["components"]), 1)
        self.assertEqual(circuit_dict["components"][0]["name"], "R1")
        
    def test_draw_schematic(self):
        """Test schematic drawing."""
        # Add components for a simple RC circuit
        self.circuit.add_component("R", ["1", "2"], 1000)
        self.circuit.add_component("C", ["2", "0"], 1e-6)
        self.circuit.add_component("V", ["1", "0"], 5.0)
        
        # Create temp file for the image
        fd, temp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        
        try:
            # Generate schematic
            self.circuit.draw_schematic(temp_path)
            
            # Check that the file exists and is not empty
            self.assertTrue(os.path.exists(temp_path))
            self.assertTrue(os.path.getsize(temp_path) > 0)
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    def test_uvx_component(self):
        """Test UVX component support."""
        # Add an op-amp
        opamp = self.circuit.add_component("U", ["1", "2", "3"], parameters={"uvx_type": "opamp"})
        self.assertEqual(opamp["name"], "U1")
        self.assertEqual(opamp["parameters"]["uvx_type"], "opamp")
        
if __name__ == "__main__":
    unittest.main() 