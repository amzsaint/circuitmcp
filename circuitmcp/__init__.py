"""
CircuitMCP - Circuit simulation capabilities through Model Context Protocol
"""

__version__ = "0.1.0"

from .circuit import Circuit
from .mcp_server import mcp

__all__ = ["Circuit", "mcp"] 