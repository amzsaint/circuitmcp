"""
Pydantic models for API validation and documentation.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class ComponentParameters(BaseModel):
    """Model for component additional parameters."""
    # This is flexible to accommodate different component types
    # Will store values like frequency for AC sources, model params for transistors, etc.
    model_config = {
        "extra": "allow",  # Allow arbitrary fields based on component type
    }

class ComponentSchema(BaseModel):
    """Schema for a single component in a circuit."""
    type: str = Field(..., description="Component type code (R, C, L, V, I, D, Q, M, X, U)")
    nodes: List[str] = Field(..., description="List of node identifiers the component connects")
    value: Optional[float] = Field(None, description="Component value (depends on type)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Additional parameters for the component")
    name: Optional[str] = Field(None, description="Optional name override (auto-generated if not provided)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "R",
                "nodes": ["1", "2"],
                "value": 1000.0,
                "parameters": {"tolerance": "5%"}
            }
        }

class CircuitCreateRequest(BaseModel):
    """Schema for creating a new circuit."""
    name: Optional[str] = Field(None, description="Optional name for the circuit")
    components: Optional[List[ComponentSchema]] = Field(None, description="Initial list of components to add")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Low-pass RC filter",
                "components": [
                    {"type": "R", "nodes": ["1", "2"], "value": 1000.0},
                    {"type": "C", "nodes": ["2", "0"], "value": 1e-6},
                    {"type": "V", "nodes": ["1", "0"], "value": 5.0}
                ]
            }
        }

class CircuitResponse(BaseModel):
    """Schema for circuit response."""
    id: int = Field(..., description="Unique identifier for the circuit")
    name: str = Field(..., description="Human-readable name of the circuit")
    version: int = Field(..., description="Version number of the circuit")
    components: List[ComponentSchema] = Field(..., description="List of components in the circuit")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Low-pass RC filter",
                "version": 1,
                "components": [
                    {"type": "R", "name": "R1", "nodes": ["1", "2"], "value": 1000.0},
                    {"type": "C", "name": "C1", "nodes": ["2", "0"], "value": 1e-6},
                    {"type": "V", "name": "V1", "nodes": ["1", "0"], "value": 5.0}
                ]
            }
        }

class SimulationRequest(BaseModel):
    """Schema for simulation request."""
    analysis: Optional[str] = Field("operating_point", 
                                  description="Analysis type: operating_point, dc, ac, transient")
    params: Optional[Dict[str, Any]] = Field(None, description="Analysis parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysis": "transient",
                "params": {
                    "step_time": 1e-6,
                    "end_time": 1e-3
                }
            }
        }

class NodeVoltageResponse(BaseModel):
    """Schema for node voltage response."""
    # Could be a single value for operating point or a list for transient/dc
    value: Union[float, List[float], Dict[str, List[float]]]

class BranchCurrentResponse(BaseModel):
    """Schema for branch current response."""
    # Could be a single value for operating point or a list for transient/dc
    value: Union[float, List[float], Dict[str, List[float]]]

class SimulationResponse(BaseModel):
    """Schema for simulation response."""
    # For operating point
    nodes: Optional[Dict[str, float]] = Field(None, description="Node voltages for operating point")
    branches: Optional[Dict[str, float]] = Field(None, description="Branch currents for operating point")
    
    # For DC sweep
    sweep: Optional[str] = Field(None, description="Name of swept parameter")
    values: Optional[List[float]] = Field(None, description="Sweep values")
    
    # For transient
    time: Optional[List[float]] = Field(None, description="Time points for transient analysis")
    
    # For AC
    frequency: Optional[List[float]] = Field(None, description="Frequency points for AC analysis")
    
    # For all non-operating point analyses
    # Using Any to allow for dict or list depending on analysis type
    nodes_data: Optional[Dict[str, Any]] = Field(None, description="Node voltage data")
    branches_data: Optional[Dict[str, Any]] = Field(None, description="Branch current data")
    
    class Config:
        json_schema_extra = {
            "examples": [
                # Operating point example
                {
                    "nodes": {"1": 5.0, "2": 3.21},
                    "branches": {"V1": 0.00179}
                },
                # Transient example
                {
                    "time": [0.0, 1e-6, 2e-6, 3e-6],
                    "nodes_data": {
                        "1": [0.0, 1.8, 3.6, 4.5],
                        "2": [0.0, 0.9, 1.8, 2.7]
                    },
                    "branches_data": {
                        "V1": [0.0, 0.0009, 0.0018, 0.0018]
                    }
                }
            ]
        }

class UVXComponentSchema(BaseModel):
    """Schema for UVX (Universal Verification X-component) specification."""
    uvx_type: str = Field(..., description="Type of UVX component (opamp, comparator, adc, dac, etc.)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Additional parameters for the UVX component")
    
    class Config:
        json_schema_extra = {
            "example": {
                "uvx_type": "opamp",
                "parameters": {
                    "gain": 1e6,
                    "rail_high": 15,
                    "rail_low": -15
                }
            }
        }

class CircuitManager(BaseModel):
    """Schema for the whole CircuitManager state (used for serialization)."""
    circuits: Dict[int, CircuitResponse] = Field(..., description="Map of circuit IDs to circuits")
    next_id: int = Field(..., description="Next available circuit ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "circuits": {
                    "1": {
                        "id": 1,
                        "name": "Low-pass RC filter",
                        "version": 1,
                        "components": []
                    }
                },
                "next_id": 2
            }
        } 