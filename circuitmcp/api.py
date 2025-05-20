"""
FastAPI routes for the circuit simulation MCP server.
"""

import os
import tempfile
import logging
from typing import List, Dict, Optional, Any, Union

from fastapi import APIRouter, HTTPException, Depends, Query, Body, Path, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import tempfile

from .manager import CircuitManager
from .schema import (
    ComponentSchema,
    CircuitCreateRequest,
    CircuitResponse,
    SimulationRequest,
    SimulationResponse,
    UVXComponentSchema,
)

logger = logging.getLogger(__name__)

# Create a router for circuit-related endpoints
router = APIRouter(prefix="/circuits", tags=["circuits"])


@router.post("/", response_model=CircuitResponse, summary="Create a new circuit")
async def create_circuit(request: CircuitCreateRequest = Body(...)):
    """
    Create a new circuit.
    
    Optionally provide a name and initial components.
    """
    # Convert request components to dict format expected by CircuitManager
    components = None
    if request.components:
        components = [comp.dict() for comp in request.components]
        
    # Create the circuit
    circuit = CircuitManager.create_circuit(name=request.name, components=components)
    
    # Return as CircuitResponse
    return circuit.to_dict()


@router.get("/", response_model=List[CircuitResponse], summary="List all circuits")
async def list_circuits():
    """
    List all circuits.
    
    Returns an array of all circuits in the system.
    """
    circuits = CircuitManager.list_circuits()
    return [c.to_dict() for c in circuits]


@router.get("/{circuit_id}", response_model=CircuitResponse, summary="Get circuit details")
async def get_circuit(
    circuit_id: int = Path(..., description="The ID of the circuit to retrieve"),
    version: Optional[int] = Query(None, description="Optional specific version to retrieve")
):
    """
    Get details of a specific circuit.
    
    If version is provided, returns that version from history if available.
    """
    circuit = CircuitManager.get_circuit(circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail=f"Circuit {circuit_id} not found")
        
    # If no version specified or matches current, return current
    if version is None or version == circuit.version:
        return circuit.to_dict()
        
    # Look up historical version
    for record in circuit.history:
        if record["version"] == version:
            return {
                "id": circuit.id,
                "name": circuit.name,
                "version": record["version"],
                "components": record["components"]
            }
            
    # Version not found
    raise HTTPException(status_code=404, detail=f"Version {version} not found for circuit {circuit_id}")


@router.put("/{circuit_id}", response_model=CircuitResponse, summary="Update a circuit")
async def update_circuit(
    circuit_id: int = Path(..., description="The ID of the circuit to update"),
    request: CircuitCreateRequest = Body(...)
):
    """
    Replace an existing circuit's components and/or name.
    
    This creates a new version and archives the previous state.
    """
    # Convert request components to dict format
    components = None
    if request.components is not None:
        components = [comp.dict() for comp in request.components]
        
    # Update the circuit
    circuit = CircuitManager.update_circuit(
        cid=circuit_id,
        name=request.name,
        components=components
    )
    
    if not circuit:
        raise HTTPException(status_code=404, detail=f"Circuit {circuit_id} not found")
        
    return circuit.to_dict()


@router.patch("/{circuit_id}", response_model=CircuitResponse, summary="Rename a circuit")
async def rename_circuit(
    circuit_id: int = Path(..., description="The ID of the circuit to rename"),
    name: str = Query(..., description="New name for the circuit")
):
    """
    Update circuit metadata (name) without changing components.
    """
    circuit = CircuitManager.get_circuit(circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail=f"Circuit {circuit_id} not found")
        
    # Update only the name
    circuit.name = name
    
    return circuit.to_dict()


@router.delete("/{circuit_id}", response_model=Dict[str, str], summary="Delete a circuit")
async def delete_circuit(
    circuit_id: int = Path(..., description="The ID of the circuit to delete")
):
    """
    Delete a circuit and all its data.
    """
    success = CircuitManager.delete_circuit(circuit_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Circuit {circuit_id} not found")
        
    return {"detail": f"Circuit {circuit_id} deleted"}


@router.post("/{circuit_id}/components", response_model=CircuitResponse, summary="Add a component")
async def add_component(
    circuit_id: int = Path(..., description="The ID of the circuit to modify"),
    component: ComponentSchema = Body(...)
):
    """
    Add a new component to an existing circuit.
    """
    circuit = CircuitManager.get_circuit(circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail=f"Circuit {circuit_id} not found")
        
    # Add the component
    comp_data = component.dict()
    name = comp_data.pop("name", None)  # Remove name if provided (will be auto-generated)
    
    circuit.add_component(
        comp_data["type"],
        comp_data["nodes"],
        comp_data.get("value"),
        comp_data.get("parameters")
    )
    
    return circuit.to_dict()


@router.delete("/{circuit_id}/components/{component_name}", response_model=CircuitResponse, summary="Remove a component")
async def remove_component(
    circuit_id: int = Path(..., description="The ID of the circuit to modify"),
    component_name: str = Path(..., description="The name of the component to remove")
):
    """
    Remove a component from a circuit by name.
    """
    circuit = CircuitManager.get_circuit(circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail=f"Circuit {circuit_id} not found")
        
    # Remove the component
    removed = circuit.remove_component(component_name)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Component {component_name} not found in circuit {circuit_id}")
        
    return circuit.to_dict()


@router.post("/{circuit_id}/simulate", response_model=SimulationResponse, summary="Simulate a circuit")
async def simulate_circuit(
    circuit_id: int = Path(..., description="The ID of the circuit to simulate"),
    request: SimulationRequest = Body(...)
):
    """
    Run a simulation on the specified circuit.
    
    Supports different analysis types including operating_point, dc, ac, and transient.
    """
    circuit = CircuitManager.get_circuit(circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail=f"Circuit {circuit_id} not found")
        
    # Run the simulation
    try:
        result = circuit.simulate(
            analysis=request.analysis,
            sim_params=request.params
        )
        return result
    except ValueError as e:
        # Convert ValueError to HTTP 400
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Simulation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.get("/{circuit_id}/image", summary="Get circuit schematic image")
async def get_circuit_image(
    circuit_id: int = Path(..., description="The ID of the circuit"),
    format: str = Query("png", description="Image format (png or svg)")
):
    """
    Generate and return a schematic image of the circuit.
    
    Returns a PNG or SVG image of the circuit schematic.
    """
    circuit = CircuitManager.get_circuit(circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail=f"Circuit {circuit_id} not found")
        
    # Validate format
    format = format.lower()
    if format not in ("png", "svg"):
        raise HTTPException(status_code=400, detail="Format must be 'png' or 'svg'")
        
    # Create temp file
    fd, temp_path = tempfile.mkstemp(suffix=f".{format}")
    os.close(fd)
    
    try:
        # Generate schematic
        circuit.draw_schematic(temp_path)
        
        # Return file
        return FileResponse(
            temp_path,
            media_type=f"image/{format}",
            filename=f"circuit_{circuit_id}_v{circuit.version}.{format}"
        )
    except Exception as e:
        logger.exception(f"Image generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate image: {str(e)}")
    finally:
        # File will be deleted after response is sent
        pass


@router.post("/{circuit_id}/uvx", response_model=CircuitResponse, summary="Add a UVX component")
async def add_uvx_component(
    circuit_id: int = Path(..., description="The ID of the circuit to modify"),
    nodes: List[str] = Query(..., description="List of node identifiers for the component"),
    uvx_data: UVXComponentSchema = Body(...)
):
    """
    Add a Universal Verification Xcomponent (UVX) to a circuit.
    
    UVX components are special components like op-amps, comparators, ADCs, DACs, etc.
    """
    circuit = CircuitManager.get_circuit(circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail=f"Circuit {circuit_id} not found")
        
    # Create parameters dict with uvx_type
    parameters = {
        "uvx_type": uvx_data.uvx_type,
    }
    
    # Add any additional parameters
    if uvx_data.parameters:
        parameters.update(uvx_data.parameters)
    
    # Add the UVX component (component type starts with U)
    circuit.add_component("U", nodes, parameters=parameters)
    
    return circuit.to_dict()


# SPICE-specific routes
@router.post("/{circuit_id}/netlist", response_model=Dict[str, str], summary="Generate SPICE netlist")
async def generate_netlist(
    circuit_id: int = Path(..., description="The ID of the circuit")
):
    """
    Generate a SPICE netlist for the circuit.
    
    Returns the circuit as a SPICE netlist that can be used with external tools.
    """
    circuit = CircuitManager.get_circuit(circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail=f"Circuit {circuit_id} not found")
        
    # For now, simple placeholder (would be implemented in circuit.py)
    return {"netlist": "* Generated SPICE netlist placeholder"}


@router.post("/import_netlist", response_model=CircuitResponse, summary="Import from SPICE netlist")
async def import_netlist(
    name: str = Query(None, description="Optional name for the imported circuit"),
    netlist_file: Optional[UploadFile] = File(None, description="SPICE netlist file"),
    netlist_text: Optional[str] = Body(None, description="SPICE netlist as text")
):
    """
    Import a circuit from a SPICE netlist.
    
    Creates a new circuit from a provided SPICE netlist (file or text).
    """
    # Check that we have either a file or text
    if netlist_file is None and netlist_text is None:
        raise HTTPException(status_code=400, detail="Either netlist_file or netlist_text must be provided")
        
    # Read file if provided
    if netlist_file:
        try:
            contents = await netlist_file.read()
            netlist_text = contents.decode("utf-8")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read netlist file: {str(e)}")
            
    # Import circuit (placeholder - would be implemented in circuit.py)
    # This would parse the netlist and create components
    circuit = CircuitManager.create_circuit(name=name or "Imported Circuit")
    
    return circuit.to_dict()


# Get versions of a circuit
@router.get("/{circuit_id}/versions", response_model=List[int], summary="List circuit versions")
async def list_circuit_versions(
    circuit_id: int = Path(..., description="The ID of the circuit")
):
    """
    List all available versions of a circuit.
    
    Returns a list of version numbers that can be used with the GET /circuits/{id}?version=X endpoint.
    """
    circuit = CircuitManager.get_circuit(circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail=f"Circuit {circuit_id} not found")
        
    # Collect all versions (history + current)
    versions = [record["version"] for record in circuit.history]
    versions.append(circuit.version)  # Add current version
    
    return versions 