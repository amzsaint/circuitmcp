"""
Main entry point for the Circuit MCP Server.
This module provides command-line functionality for running the MCP server.
"""

import sys
import argparse
import logging
from typing import List, Optional

# Import our mcp server
from .mcp_server import mcp

def setup_logging(debug: bool = False) -> None:
    """Configure logging for the application"""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.debug("Debug logging enabled")

def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="CircuitMCP Server")
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    parser.add_argument(
        "--host", 
        type=str, 
        default="127.0.0.1", 
        help="Host address to bind server"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind server"
    )
    
    return parser.parse_args(args)

def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point function for the Circuit MCP Server
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success)
    """
    parsed_args = parse_args(args)
    setup_logging(parsed_args.debug)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting CircuitMCP Server on {parsed_args.host}:{parsed_args.port}")
    
    try:
        # Run the MCP server
        mcp.run(host=parsed_args.host, port=parsed_args.port)
        return 0
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Error running server: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 