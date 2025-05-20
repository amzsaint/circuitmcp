"""
Test cases for the API endpoints.
"""

import unittest
from fastapi.testclient import TestClient

from circuitmcp.main import app
from circuitmcp.manager import CircuitManager

# Reset the CircuitManager state before each test
CircuitManager._circuits = {}
CircuitManager._next_id = 1

class TestAPI(unittest.TestCase):
    """Test cases for the API endpoints."""
    
    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)
        # Clear circuits before each test
        CircuitManager._circuits = {}
        CircuitManager._next_id = 1
        
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        
    def test_create_circuit(self):
        """Test creating a circuit."""
        # Create a simple circuit
        response = self.client.post(
            "/circuits",
            json={
                "name": "Test Circuit",
                "components": [
                    {"type": "R", "nodes": ["1", "2"], "value": 1000}
                ]
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "Test Circuit")
        self.assertEqual(len(data["components"]), 1)
        
        # Remember the circuit ID
        circuit_id = data["id"]
        
        # Get the circuit
        response = self.client.get(f"/circuits/{circuit_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], circuit_id)
        
    def test_list_circuits(self):
        """Test listing circuits."""
        # Create two circuits
        self.client.post(
            "/circuits",
            json={"name": "Circuit 1"}
        )
        self.client.post(
            "/circuits",
            json={"name": "Circuit 2"}
        )
        
        # Get the list
        response = self.client.get("/circuits")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "Circuit 1")
        self.assertEqual(data[1]["name"], "Circuit 2")
        
    def test_delete_circuit(self):
        """Test deleting a circuit."""
        # Create a circuit
        response = self.client.post(
            "/circuits",
            json={"name": "Circuit to Delete"}
        )
        circuit_id = response.json()["id"]
        
        # Delete it
        response = self.client.delete(f"/circuits/{circuit_id}")
        self.assertEqual(response.status_code, 200)
        
        # Try to get it (should fail)
        response = self.client.get(f"/circuits/{circuit_id}")
        self.assertEqual(response.status_code, 404)
        
    def test_add_component(self):
        """Test adding a component to a circuit."""
        # Create a circuit
        response = self.client.post(
            "/circuits",
            json={"name": "Circuit with Components"}
        )
        circuit_id = response.json()["id"]
        
        # Add a component
        response = self.client.post(
            f"/circuits/{circuit_id}/components",
            json={
                "type": "R",
                "nodes": ["1", "2"],
                "value": 1000
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["components"]), 1)
        self.assertEqual(data["components"][0]["name"], "R1")
        
    def test_remove_component(self):
        """Test removing a component from a circuit."""
        # Create a circuit with a component
        response = self.client.post(
            "/circuits",
            json={
                "name": "Circuit to Modify",
                "components": [
                    {"type": "R", "nodes": ["1", "2"], "value": 1000}
                ]
            }
        )
        circuit_id = response.json()["id"]
        
        # Remove the component
        response = self.client.delete(f"/circuits/{circuit_id}/components/R1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["components"]), 0)
        
    def test_simulate_circuit(self):
        """Test simulating a circuit."""
        # Create a simple RC circuit
        response = self.client.post(
            "/circuits",
            json={
                "name": "RC Circuit",
                "components": [
                    {"type": "R", "nodes": ["1", "2"], "value": 1000},
                    {"type": "C", "nodes": ["2", "0"], "value": 1e-6},
                    {"type": "V", "nodes": ["1", "0"], "value": 5}
                ]
            }
        )
        circuit_id = response.json()["id"]
        
        # Run an operating point simulation
        response = self.client.post(
            f"/circuits/{circuit_id}/simulate",
            json={
                "analysis": "operating_point"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("nodes", data)
        self.assertIn("branches", data)
        
    def test_update_circuit(self):
        """Test updating a circuit."""
        # Create a circuit
        response = self.client.post(
            "/circuits",
            json={
                "name": "Original Circuit",
                "components": [
                    {"type": "R", "nodes": ["1", "2"], "value": 1000}
                ]
            }
        )
        circuit_id = response.json()["id"]
        
        # Update it
        response = self.client.put(
            f"/circuits/{circuit_id}",
            json={
                "name": "Updated Circuit",
                "components": [
                    {"type": "C", "nodes": ["1", "0"], "value": 1e-6}
                ]
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "Updated Circuit")
        self.assertEqual(len(data["components"]), 1)
        self.assertEqual(data["components"][0]["type"], "C")
        self.assertEqual(data["version"], 2)  # Version should increment
        
    def test_uvx_component(self):
        """Test adding a UVX component."""
        # Create a circuit
        response = self.client.post(
            "/circuits",
            json={"name": "Circuit with UVX"}
        )
        circuit_id = response.json()["id"]
        
        # Add an op-amp
        response = self.client.post(
            f"/circuits/{circuit_id}/uvx",
            json={
                "uvx_data": {
                    "uvx_type": "opamp",
                    "parameters": {
                        "gain": 1e6
                    }
                }
            },
            params={"nodes": ["1", "2", "3"]}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check the component was added
        self.assertEqual(len(data["components"]), 1)
        self.assertEqual(data["components"][0]["type"], "U")
        self.assertEqual(data["components"][0]["parameters"]["uvx_type"], "opamp")
        
if __name__ == "__main__":
    unittest.main() 