"""
Circuit class for the MCP Circuit Simulation Server.
Handles component management, simulation, and schematic drawing.
"""

import os
import tempfile
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
import math
import copy

# Import PySpice for circuit simulation
from PySpice.Spice.Netlist import Circuit as SpiceCircuit
from PySpice.Spice.NgSpice.Shared import NgSpiceShared
from PySpice.Unit import *

# Import SchemDraw for schematic drawing
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for matplotlib
import schemdraw
import schemdraw.elements as elm

# Configure logging
logger = logging.getLogger(__name__)

class Circuit:
    """
    Class representing an electronic circuit with components and simulation capabilities.
    """
    
    def __init__(self, circuit_id: int, name: Optional[str] = None):
        """
        Initialize a new circuit.
        
        Args:
            circuit_id: Unique identifier for the circuit
            name: Optional name for the circuit
        """
        self.id = circuit_id
        self.name = name or f"Circuit {circuit_id}"
        self.version = 1
        self.components = []
        self.history = []
        
        # Track next component IDs by type
        self._next_ids = {"R": 1, "C": 1, "L": 1, "V": 1, "I": 1, "D": 1, "Q": 1, "M": 1, "X": 1, "U": 1}
        
    def add_component(
        self, 
        component_type: str, 
        nodes: List[str], 
        value: Optional[float] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a component to the circuit.
        
        Args:
            component_type: Type of component (R, L, C, V, I, etc.)
            nodes: List of nodes to connect the component
            value: Value of the component (resistance, capacitance, etc.)
            parameters: Additional parameters for the component
            
        Returns:
            Dictionary representing the added component
        """
        # Normalize component type
        component_type = component_type.upper()
        
        # Initialize next ID for component type if not exists
        if component_type not in self._next_ids:
            self._next_ids[component_type] = 1
            
        # Generate component name (e.g., R1, C2, etc.)
        comp_id = self._next_ids[component_type]
        self._next_ids[component_type] += 1
        name = f"{component_type}{comp_id}"
        
        # Create component record
        component = {
            "name": name,
            "type": component_type,
            "nodes": nodes,
        }
        
        if value is not None:
            component["value"] = value
            
        if parameters is not None:
            component["parameters"] = parameters
            
        # Add to components list
        self.components.append(component)
        
        # Create new version when circuit is modified
        self._increment_version()
        
        return component
    
    def remove_component(self, component_name: str) -> bool:
        """
        Remove a component from the circuit by name.
        
        Args:
            component_name: Name of the component to remove (e.g., "R1")
            
        Returns:
            True if component was found and removed, False otherwise
        """
        for i, component in enumerate(self.components):
            if component["name"] == component_name:
                # Remove the component
                self.components.pop(i)
                # Create new version when circuit is modified
                self._increment_version()
                return True
                
        return False
    
    def update_components(self, new_components: List[Dict[str, Any]]) -> None:
        """
        Replace all components with a new set (for bulk updates).
        
        Args:
            new_components: New components list to replace existing ones
        """
        # Save old state to history
        self._increment_version(save_components=True)
        
        # Clear existing components
        self.components = []
        
        # Add new components
        for comp in new_components:
            # Extract required fields
            comp_type = comp["type"]
            nodes = comp["nodes"]
            
            # Extract optional fields
            value = comp.get("value")
            parameters = comp.get("parameters")
            
            # Add component
            self.add_component(comp_type, nodes, value, parameters)
    
    def _increment_version(self, save_components: bool = False) -> None:
        """
        Increment the circuit version and optionally save current state to history.
        
        Args:
            save_components: Whether to save a copy of current components to history
        """
        if save_components:
            # Save current state to history
            old_state = {
                "version": self.version,
                "components": copy.deepcopy(self.components)
            }
            self.history.append(old_state)
            
        # Increment version
        self.version += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the circuit to a dictionary representation.
        
        Returns:
            Dictionary representation of the circuit
        """
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "components": copy.deepcopy(self.components)
        }
        
    def simulate(self, analysis: str = "operating_point", sim_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Simulate the circuit using PySpice.
        
        Args:
            analysis: Type of analysis ("operating_point", "dc", "ac", "transient")
            sim_params: Parameters for the simulation (depends on analysis type)
            
        Returns:
            Dictionary containing simulation results
        """
        if sim_params is None:
            sim_params = {}
            
        # Create PySpice Circuit
        spice_circuit = SpiceCircuit(self.name)
        
        # Add components to the PySpice circuit
        for comp in self.components:
            comp_type = comp["type"]
            nodes = comp["nodes"]
            value = comp.get("value")
            params = comp.get("parameters", {})
            
            # Normalize node names (treat "0", "gnd", "ground" as ground)
            def normalize_node(node):
                if node and str(node).lower() in ("0", "gnd", "ground"):
                    return spice_circuit.gnd
                return node
            
            # Map nodes to PySpice nodes
            spice_nodes = [normalize_node(node) for node in nodes]
            
            # Add component based on type
            try:
                if comp_type == "R":  # Resistor
                    spice_circuit.R(comp["name"], spice_nodes[0], spice_nodes[1], value @ u_Ω)
                    
                elif comp_type == "C":  # Capacitor
                    spice_circuit.C(comp["name"], spice_nodes[0], spice_nodes[1], value @ u_F)
                    
                elif comp_type == "L":  # Inductor
                    spice_circuit.L(comp["name"], spice_nodes[0], spice_nodes[1], value @ u_H)
                    
                elif comp_type == "V":  # Voltage Source
                    # Handle different voltage source types
                    if params and "type" in params:
                        if params["type"] == "sine":
                            amplitude = params.get("amplitude", value or 1)
                            frequency = params.get("frequency", 1000)
                            offset = params.get("offset", 0)
                            spice_circuit.SinusoidalVoltageSource(
                                comp["name"], 
                                spice_nodes[0], 
                                spice_nodes[1], 
                                amplitude=amplitude @ u_V,
                                frequency=frequency @ u_Hz,
                                offset=offset @ u_V
                            )
                        elif params["type"] == "pulse":
                            initial = params.get("initial", 0)
                            pulsed = params.get("pulsed", value or 5)
                            delay = params.get("delay", 0)
                            rise_time = params.get("rise_time", 1e-9)
                            fall_time = params.get("fall_time", 1e-9)
                            pulse_width = params.get("pulse_width", 1e-3)
                            period = params.get("period", 2e-3)
                            spice_circuit.PulseVoltageSource(
                                comp["name"],
                                spice_nodes[0],
                                spice_nodes[1],
                                initial_value=initial @ u_V,
                                pulsed_value=pulsed @ u_V,
                                delay_time=delay @ u_s,
                                rise_time=rise_time @ u_s,
                                fall_time=fall_time @ u_s,
                                pulse_width=pulse_width @ u_s,
                                period=period @ u_s
                            )
                        else:
                            # Default to DC source
                            spice_circuit.V(comp["name"], spice_nodes[0], spice_nodes[1], value @ u_V)
                    else:
                        # Default to DC source
                        spice_circuit.V(comp["name"], spice_nodes[0], spice_nodes[1], value @ u_V)
                        
                elif comp_type == "I":  # Current Source
                    spice_circuit.I(comp["name"], spice_nodes[0], spice_nodes[1], value @ u_A)
                    
                elif comp_type == "D":  # Diode
                    model_name = params.get("model", "default_diode")
                    # Add diode model if not already defined
                    if not hasattr(spice_circuit, f"model_{model_name}"):
                        spice_circuit.model(model_name, "D", is_=params.get("is", 1e-14),
                                           n=params.get("n", 1), vj=params.get("vj", 1))
                    spice_circuit.D(comp["name"], spice_nodes[0], spice_nodes[1], model=model_name)
                    
                elif comp_type == "Q":  # BJT Transistor
                    model_name = params.get("model", "default_npn")
                    # Add BJT model if not already defined
                    if not hasattr(spice_circuit, f"model_{model_name}"):
                        spice_circuit.model(model_name, "NPN", bf=params.get("bf", 100))
                    spice_circuit.Q(comp["name"], spice_nodes[0], spice_nodes[1], spice_nodes[2], model=model_name)
                    
                elif comp_type == "U":  # Universal Verification Component (UVX)
                    uvx_type = params.get("uvx_type", "opamp")
                    
                    if uvx_type == "opamp":
                        # Implement op-amp using a voltage-controlled voltage source
                        # Typically: output, -, +, vcc, vee
                        gain = params.get("gain", 1e6)
                        if len(spice_nodes) >= 3:
                            # Create internal nodes
                            int_node1 = f"int_{comp['name']}_1"
                            int_node2 = f"int_{comp['name']}_2"
                            
                            # Add high-impedance inputs
                            spice_circuit.R(f"{comp['name']}_in_p", spice_nodes[2], int_node1, 1e9 @ u_Ω)
                            spice_circuit.R(f"{comp['name']}_in_n", spice_nodes[1], int_node2, 1e9 @ u_Ω)
                            
                            # Add voltage-controlled voltage source
                            spice_circuit.VCVS(comp["name"], spice_nodes[0], spice_circuit.gnd, int_node1, int_node2, gain)
                    
                    elif uvx_type == "comparator":
                        # Implement comparator with a B source (behavioral source)
                        spice_circuit.B(
                            comp["name"], 
                            spice_nodes[0], 
                            spice_circuit.gnd, 
                            f"V=if(v({spice_nodes[2]})-v({spice_nodes[1]})>0, {params.get('high', 5)}, {params.get('low', 0)})"
                        )
                        
                    elif uvx_type == "adc":
                        # Simplified ADC model
                        # In real implementation, this would be much more complex
                        bits = params.get("bits", 8)
                        ref = params.get("reference", 5)
                        spice_circuit.B(
                            comp["name"],
                            spice_nodes[0],
                            spice_circuit.gnd,
                            f"V=floor(v({spice_nodes[1]})*{2**bits-1}/{ref}+0.5)*{ref}/{2**bits-1}"
                        )
                    
                    elif uvx_type == "dac":
                        # Simplified DAC model
                        bits = params.get("bits", 8)
                        ref = params.get("reference", 5)
                        # Assume digital input is already scaled to 0-1 range
                        spice_circuit.B(
                            comp["name"],
                            spice_nodes[0],
                            spice_circuit.gnd,
                            f"V=v({spice_nodes[1]})*{ref}"
                        )
            except Exception as e:
                logger.exception(f"Error adding component {comp['name']} to circuit: {str(e)}")
                raise ValueError(f"Error adding component {comp['name']}: {str(e)}")
        
        # Create simulator
        simulator = NgSpiceShared.new_instance(spice_circuit)
        
        # Run simulation based on analysis type
        analysis = analysis.lower()
        results = {}
        
        try:
            if analysis == "operating_point":
                # Run operating point analysis
                op = simulator.operating_point()
                
                # Collect node voltages
                results["nodes"] = {}
                for node in op.nodes.values():
                    node_name = str(node)
                    if node_name not in ("0", "gnd"):
                        results["nodes"][node_name] = float(node)
                
                # Collect branch currents
                results["branches"] = {}
                for branch in op.branches.values():
                    branch_name = str(branch)
                    results["branches"][branch_name] = float(branch)
                    
            elif analysis == "dc":
                # Get DC sweep parameters
                source = sim_params.get("source")
                start = sim_params.get("start")
                stop = sim_params.get("stop")
                step = sim_params.get("step")
                
                if not all([source, start is not None, stop is not None, step is not None]):
                    raise ValueError("DC analysis requires 'source', 'start', 'stop', 'step' parameters")
                
                # Run DC sweep analysis
                analysis = simulator.dc_analysis(
                    **{source: slice(start, stop, step)}
                )
                
                # Collect sweep values and results
                results["sweep"] = {
                    "source": source,
                    "values": [float(x) for x in analysis[source]]
                }
                
                # Collect node voltages across sweep
                results["nodes"] = {}
                for node_name, node_values in analysis.nodes.items():
                    if node_name not in ("0", "gnd"):
                        results["nodes"][node_name] = [float(v) for v in node_values]
                
                # Collect branch currents across sweep
                results["branches"] = {}
                for branch_name, branch_values in analysis.branches.items():
                    results["branches"][branch_name] = [float(i) for i in branch_values]
                    
            elif analysis == "ac":
                # Get AC analysis parameters
                start_freq = sim_params.get("start_frequency", 1)
                stop_freq = sim_params.get("stop_frequency", 1e6)
                num_points = sim_params.get("points", 10)
                variation = sim_params.get("variation", "dec")  # dec, oct, lin
                
                # Run AC analysis
                analysis = simulator.ac_analysis(
                    start_frequency=start_freq @ u_Hz,
                    stop_frequency=stop_freq @ u_Hz,
                    number_of_points=num_points,
                    variation=variation
                )
                
                # Collect frequencies
                results["frequency"] = {"values": [float(f) for f in analysis.frequency]}
                
                # Collect node voltages (complex numbers) across frequencies
                results["nodes"] = {}
                for node_name, node_values in analysis.nodes.items():
                    if node_name not in ("0", "gnd"):
                        # Store magnitude and phase
                        results["nodes"][node_name] = {
                            "magnitude": [float(abs(v)) for v in node_values],
                            "phase": [float(math.degrees(math.atan2(v.imag, v.real))) for v in node_values]
                        }
                
                # Collect branch currents across frequencies
                results["branches"] = {}
                for branch_name, branch_values in analysis.branches.items():
                    results["branches"][branch_name] = {
                        "magnitude": [float(abs(i)) for i in branch_values],
                        "phase": [float(math.degrees(math.atan2(i.imag, i.real))) for i in branch_values]
                    }
                    
            elif analysis == "transient":
                # Get transient analysis parameters
                step_time = sim_params.get("step_time")
                end_time = sim_params.get("end_time")
                
                if step_time is None or end_time is None:
                    raise ValueError("Transient analysis requires 'step_time' and 'end_time' parameters")
                
                # Run transient analysis
                analysis = simulator.transient_analysis(
                    step_time=step_time @ u_s,
                    end_time=end_time @ u_s
                )
                
                # Collect time points
                results["time"] = [float(t) for t in analysis.time]
                
                # Collect node voltages over time
                results["nodes"] = {}
                for node_name, node_values in analysis.nodes.items():
                    if node_name not in ("0", "gnd"):
                        results["nodes"][node_name] = [float(v) for v in node_values]
                
                # Collect branch currents over time
                results["branches"] = {}
                for branch_name, branch_values in analysis.branches.items():
                    results["branches"][branch_name] = [float(i) for i in branch_values]
                    
            else:
                raise ValueError(f"Unsupported analysis type: {analysis}")
                
        except Exception as e:
            logger.exception(f"Simulation error: {str(e)}")
            raise ValueError(f"Simulation failed: {str(e)}")
            
        return results
    
    def draw_schematic(self, filepath: str) -> None:
        """
        Generate a schematic drawing of the circuit.
        
        Args:
            filepath: Path to save the schematic image
        """
        # Determine file format from filepath extension
        format = filepath.split(".")[-1].lower()
        if format not in ("png", "svg", "pdf"):
            raise ValueError(f"Unsupported format: {format}. Use png, svg, or pdf.")
        
        # Initialize drawing
        d = schemdraw.Drawing(show=False)
        
        # Map component types to SchemDraw elements
        component_map = {
            "R": elm.Resistor,
            "C": elm.Capacitor,
            "L": elm.Inductor,
            "V": elm.SourceV,
            "I": elm.SourceI,
            "D": elm.Diode,
            "Q": elm.BjtNpn,  # Default to NPN
            "U": None  # Handle UVX components specially
        }
        
        # Track nodes positions
        node_positions = {"0": (0, 0)}  # Ground at origin
        next_pos = (0, 2)  # Start position
        
        # First pass: place components and calculate node positions
        for i, comp in enumerate(self.components):
            comp_type = comp["type"]
            nodes = comp["nodes"]
            
            # Skip unhandled component types
            if comp_type not in component_map or component_map[comp_type] is None:
                continue
                
            # Determine component element
            elem_class = component_map[comp_type]
            
            # Create element
            elem = elem_class()
            
            # Calculate position based on nodes
            # This is a simplified placement algorithm
            if len(nodes) >= 2:
                node1, node2 = nodes[0], nodes[1]
                
                # If nodes don't have positions yet, assign them
                if node1 not in node_positions:
                    node_positions[node1] = (next_pos[0], next_pos[1])
                    next_pos = (next_pos[0] + 2, next_pos[1])
                    
                if node2 not in node_positions:
                    node_positions[node2] = (next_pos[0], next_pos[1])
                    next_pos = (next_pos[0] + 2, next_pos[1])
        
        # Second pass: add components to drawing
        for comp in self.components:
            comp_type = comp["type"]
            name = comp["name"]
            nodes = comp["nodes"]
            
            # Skip unhandled component types
            if comp_type not in component_map or component_map[comp_type] is None:
                continue
                
            # Determine component element
            elem_class = component_map[comp_type]
            
            # Create element
            elem = elem_class().label(name)
            
            # Calculate position based on nodes
            if len(nodes) >= 2:
                node1, node2 = nodes[0], nodes[1]
                
                if node1 in node_positions and node2 in node_positions:
                    pos1 = node_positions[node1]
                    pos2 = node_positions[node2]
                    
                    # Add element at midpoint with appropriate angle
                    mid_x = (pos1[0] + pos2[0]) / 2
                    mid_y = (pos1[1] + pos2[1]) / 2
                    
                    dx = pos2[0] - pos1[0]
                    dy = pos2[1] - pos1[1]
                    angle = math.degrees(math.atan2(dy, dx))
                    
                    d.add(elem, at=(mid_x, mid_y), theta=angle)
                    
                    # Add node labels
                    if node1 != "0" and node1 != "gnd":
                        d.add(elm.Dot().label(node1), at=pos1)
                    if node2 != "0" and node2 != "gnd":
                        d.add(elm.Dot().label(node2), at=pos2)
        
        # Add ground symbols
        if "0" in node_positions:
            d.add(elm.Ground(), at=node_positions["0"])
            
        # Save the drawing
        d.save(filepath) 