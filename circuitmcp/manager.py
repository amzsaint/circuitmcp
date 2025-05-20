"""
CircuitManager for handling circuit creation, storage and retrieval.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .circuit import Circuit

logger = logging.getLogger(__name__)

class CircuitManager:
    """Manages the collection of Circuit instances for creation/retrieval/update/delete operations."""
    # Class variables for storage
    _circuits: Dict[int, Circuit] = {}
    _next_id: int = 1
    _persistence_path: Optional[str] = None
    
    @classmethod
    def initialize(cls, persistence_path: Optional[str] = None):
        """
        Initialize the CircuitManager, optionally with persistence.
        
        Args:
            persistence_path: Optional path to store/load circuit data
        """
        cls._persistence_path = persistence_path
        if persistence_path:
            try:
                cls._load_from_disk()
            except Exception as e:
                logger.warning(f"Failed to load circuit data from disk: {e}")
                # Continue with empty state
    
    @classmethod
    def create_circuit(cls, name: Optional[str] = None, components: Optional[List[Dict[str, Any]]] = None) -> Circuit:
        """
        Create a new Circuit with an auto-generated ID and optional initial components.
        
        Args:
            name: Optional name for the circuit
            components: Optional list of initial components
            
        Returns:
            The newly created Circuit instance
        """
        cid = cls._next_id
        cls._next_id += 1
        
        # Create new Circuit instance
        circuit = Circuit(circuit_id=cid, name=name)
        
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
        cls._circuits[cid] = circuit
        
        # Persist if configured
        if cls._persistence_path:
            cls._save_to_disk()
            
        return circuit
    
    @classmethod
    def get_circuit(cls, cid: int) -> Optional[Circuit]:
        """
        Retrieve a Circuit by ID.
        
        Args:
            cid: The circuit ID to retrieve
            
        Returns:
            The Circuit if found, None otherwise
        """
        return cls._circuits.get(cid)
    
    @classmethod
    def update_circuit(cls, cid: int, name: Optional[str] = None, 
                       components: Optional[List[Dict[str, Any]]] = None) -> Optional[Circuit]:
        """
        Update an existing circuit by ID.
        
        Args:
            cid: The circuit ID to update
            name: Optional new name for the circuit
            components: Optional new components list
            
        Returns:
            The updated Circuit if found, None otherwise
        """
        circuit = cls.get_circuit(cid)
        if not circuit:
            return None
            
        # Update name if provided
        if name is not None:
            circuit.name = name
            
        # Update components if provided
        if components is not None:
            circuit.update_components(components)
            
        # Persist if configured
        if cls._persistence_path:
            cls._save_to_disk()
            
        return circuit
    
    @classmethod
    def delete_circuit(cls, cid: int) -> bool:
        """
        Delete a circuit by ID.
        
        Args:
            cid: The circuit ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        if cid in cls._circuits:
            del cls._circuits[cid]
            
            # Persist if configured
            if cls._persistence_path:
                cls._save_to_disk()
                
            return True
        return False
    
    @classmethod
    def list_circuits(cls) -> List[Circuit]:
        """
        Get a list of all circuits.
        
        Returns:
            List of all Circuit instances
        """
        return list(cls._circuits.values())
    
    @classmethod
    def _save_to_disk(cls):
        """Persist circuit data to disk."""
        if not cls._persistence_path:
            return
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(cls._persistence_path), exist_ok=True)
        
        # Convert circuit objects to serializable format
        data = {
            "next_id": cls._next_id,
            "circuits": {}
        }
        
        for cid, circuit in cls._circuits.items():
            # Convert each circuit to dict
            data["circuits"][cid] = circuit.to_dict()
            
        # Write to file
        with open(cls._persistence_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    @classmethod
    def _load_from_disk(cls):
        """Load circuit data from disk."""
        if not cls._persistence_path or not os.path.exists(cls._persistence_path):
            return
            
        # Read from file
        with open(cls._persistence_path, 'r') as f:
            data = json.load(f)
            
        # Update next ID
        cls._next_id = data.get("next_id", 1)
        
        # Clear existing circuits
        cls._circuits.clear()
        
        # Recreate circuits from data
        for cid_str, circuit_data in data.get("circuits", {}).items():
            cid = int(cid_str)
            
            # Create circuit
            circuit = Circuit(circuit_id=cid, name=circuit_data.get("name"))
            
            # Set version
            circuit.version = circuit_data.get("version", 1)
            
            # Add components
            for comp in circuit_data.get("components", []):
                circuit.add_component(
                    comp["type"],
                    comp["nodes"],
                    comp.get("value"),
                    comp.get("parameters")
                )
                
            # Add to dictionary
            cls._circuits[cid] = circuit 