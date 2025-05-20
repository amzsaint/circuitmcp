#!/usr/bin/env python3
"""
Example script demonstrating how to use the CircuitMCP API.

This script creates a simple RC low-pass filter circuit, runs different simulations on it,
and generates a schematic image.
"""

import sys
import os
import requests
import json
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# Server URL
BASE_URL = "http://localhost:8000"

def print_json(obj):
    """Pretty print JSON data"""
    print(json.dumps(obj, indent=2))

def main():
    # Check if the server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print(f"Server is not responding correctly. Status code: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("Could not connect to the server. Make sure it's running on the correct URL.")
        return

    print("1. Creating a new RC low-pass filter circuit")
    # Create a circuit with a resistor, capacitor, and voltage source
    circuit_data = {
        "name": "RC Low-pass Filter",
        "components": [
            {"type": "R", "nodes": ["1", "2"], "value": 1000},  # 1k resistor
            {"type": "C", "nodes": ["2", "0"], "value": 1e-6},  # 1µF capacitor
            {"type": "V", "nodes": ["1", "0"], "value": 5}      # 5V source
        ]
    }
    
    response = requests.post(f"{BASE_URL}/circuits", json=circuit_data)
    if response.status_code != 200:
        print(f"Failed to create circuit: {response.text}")
        return
        
    circuit = response.json()
    circuit_id = circuit["id"]
    print(f"Circuit created with ID: {circuit_id}")
    print_json(circuit)
    
    print("\n2. Running an operating point analysis")
    # Run an operating point analysis
    sim_request = {
        "analysis": "operating_point"
    }
    
    response = requests.post(f"{BASE_URL}/circuits/{circuit_id}/simulate", json=sim_request)
    if response.status_code != 200:
        print(f"Simulation failed: {response.text}")
    else:
        sim_results = response.json()
        print("Simulation results:")
        print_json(sim_results)
        
    print("\n3. Running a transient analysis")
    # Run a transient analysis
    sim_request = {
        "analysis": "transient",
        "params": {
            "step_time": 1e-5,  # 10 microseconds step
            "end_time": 1e-2    # 10 milliseconds total
        }
    }
    
    response = requests.post(f"{BASE_URL}/circuits/{circuit_id}/simulate", json=sim_request)
    if response.status_code != 200:
        print(f"Transient simulation failed: {response.text}")
    else:
        sim_results = response.json()
        print("Transient analysis has time points and node voltages over time")
        
        # Plot the transient response for node 2 (across the capacitor)
        if "time" in sim_results and "nodes_data" in sim_results and "2" in sim_results["nodes_data"]:
            time = sim_results["time"]
            node2_voltage = sim_results["nodes_data"]["2"]
            
            plt.figure(figsize=(10, 6))
            plt.plot(time, node2_voltage)
            plt.title("RC Low-pass Filter Transient Response")
            plt.xlabel("Time (s)")
            plt.ylabel("Voltage (V)")
            plt.grid(True)
            plt.savefig("transient_response.png")
            print("Transient response plot saved to 'transient_response.png'")
        
    print("\n4. Generating a schematic image")
    # Get a schematic image
    response = requests.get(f"{BASE_URL}/circuits/{circuit_id}/image", stream=True)
    if response.status_code != 200:
        print(f"Failed to get image: {response.text}")
    else:
        with open("circuit_schematic.png", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Schematic image saved to 'circuit_schematic.png'")
        
    print("\n5. Adding an op-amp component (UVX)")
    # Let's add an op-amp as an example UVX component
    opamp_data = {
        "nodes": ["2", "3", "4"],  # in+, in-, out
        "uvx_data": {
            "uvx_type": "opamp",
            "parameters": {
                "gain": 1e6
            }
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/circuits/{circuit_id}/uvx",
        json=opamp_data,
        params={"nodes": ["2", "3", "4"]}
    )
    
    if response.status_code != 200:
        print(f"Failed to add op-amp: {response.text}")
    else:
        updated_circuit = response.json()
        print("Circuit updated with op-amp:")
        print_json(updated_circuit)
        
    print("\nExample completed successfully!")

if __name__ == "__main__":
    main() 