"""
Mock implementation of the MCP SDK for testing purposes.
"""

import inspect
import functools
from typing import Any, Dict, List, Callable, Optional, Set, Union


class FastMCP:
    """
    Mock implementation of the FastMCP class from the MCP SDK.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.tools = {}
        self.resources = {}
        self.prompts = {}
    
    def tool(self, name: Optional[str] = None):
        """Decorator to register a tool function."""
        def decorator(func):
            nonlocal name
            if name is None:
                name = func.__name__
            self.tools[name] = func
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def resource(self, path: str):
        """Decorator to register a resource function."""
        def decorator(func):
            self.resources[path] = func
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def prompt(self, name: Optional[str] = None):
        """Decorator to register a prompt function."""
        def decorator(func):
            nonlocal name
            if name is None:
                name = func.__name__
            self.prompts[name] = func
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def run(self):
        """
        Mock method to run the server.
        In a real implementation, this would start the server.
        """
        print(f"Mock MCP server '{self.name}' is running")
        print(f"Available tools: {list(self.tools.keys())}")
        print(f"Available resources: {list(self.resources.keys())}")
        print(f"Available prompts: {list(self.prompts.keys())}")
        
    def call_tool(self, name: str, params: Dict[str, Any]) -> Any:
        """
        Call a tool by name with the given parameters.
        This is used for testing.
        
        Args:
            name: Name of the tool to call
            params: Parameters to pass to the tool
            
        Returns:
            Result of the tool call
        """
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")
        
        # Get the function signature
        sig = inspect.signature(self.tools[name])
        
        # Match parameters to function signature
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name in params:
                kwargs[param_name] = params[param_name]
            elif param.default == inspect.Parameter.empty:
                raise ValueError(f"Missing required parameter '{param_name}' for tool '{name}'")
        
        # Call the function
        return self.tools[name](**kwargs)
    
    def get_resource(self, path: str, params: Dict[str, Any] = None) -> Any:
        """
        Get a resource by path with the given parameters.
        This is used for testing.
        
        Args:
            path: Path of the resource to get
            params: Parameters to pass to the resource
            
        Returns:
            Result of the resource
        """
        # Find matching resource
        resource_func = None
        path_params = {}
        
        for resource_path, func in self.resources.items():
            # Check if path is a direct match
            if resource_path == path:
                resource_func = func
                break
            
            # Check if path matches a parameterized resource path
            # For example, "circuit/{circuit_id}" would match "circuit/1"
            parts = resource_path.split("/")
            path_parts = path.split("/")
            
            if len(parts) == len(path_parts):
                match = True
                for i, part in enumerate(parts):
                    if part.startswith("{") and part.endswith("}"):
                        # This is a path parameter
                        param_name = part[1:-1]
                        path_params[param_name] = path_parts[i]
                    elif part != path_parts[i]:
                        match = False
                        break
                
                if match:
                    resource_func = func
                    break
        
        if resource_func is None:
            raise ValueError(f"Resource '{path}' not found")
        
        # Get the function signature
        sig = inspect.signature(resource_func)
        
        # Match parameters to function signature
        kwargs = {}
        
        # First, add path parameters
        for param_name, param_value in path_params.items():
            # Try to convert to int if parameter is annotated as int
            if param_name in sig.parameters and sig.parameters[param_name].annotation == int:
                try:
                    kwargs[param_name] = int(param_value)
                except ValueError:
                    kwargs[param_name] = param_value
            else:
                kwargs[param_name] = param_value
        
        # Then, add query parameters if provided
        if params:
            for param_name, param_value in params.items():
                kwargs[param_name] = param_value
        
        # Call the function
        return resource_func(**kwargs)
    
    def get_prompt(self, name: str) -> str:
        """
        Get a prompt by name.
        This is used for testing.
        
        Args:
            name: Name of the prompt to get
            
        Returns:
            Prompt text
        """
        if name not in self.prompts:
            raise ValueError(f"Prompt '{name}' not found")
        
        return self.prompts[name]()


# Mock implementation of the client for testing
class ClientSession:
    """
    Mock implementation of the ClientSession class from the MCP SDK.
    """
    
    def __init__(self, server):
        self.server = server
    
    async def call_tool(self, name: str, params: Dict[str, Any]) -> Any:
        """
        Call a tool by name with the given parameters.
        
        Args:
            name: Name of the tool to call
            params: Parameters to pass to the tool
            
        Returns:
            Result of the tool call
        """
        return self.server.call_tool(name, params)
    
    async def get_resource(self, path: str, params: Dict[str, Any] = None) -> Any:
        """
        Get a resource by path with the given parameters.
        
        Args:
            path: Path of the resource to get
            params: Parameters to pass to the resource
            
        Returns:
            Result of the resource
        """
        return self.server.get_resource(path, params)
    
    async def describe_tools(self) -> List[Dict[str, Any]]:
        """
        Get a list of tools available on the server.
        
        Returns:
            List of tool descriptions
        """
        return [
            {"name": name, "description": func.__doc__ or ""}
            for name, func in self.server.tools.items()
        ]
    
    async def describe_resources(self) -> List[Dict[str, Any]]:
        """
        Get a list of resources available on the server.
        
        Returns:
            List of resource descriptions
        """
        return [
            {"path": path, "description": func.__doc__ or ""}
            for path, func in self.server.resources.items()
        ]
    
    async def describe_prompts(self) -> List[Dict[str, Any]]:
        """
        Get a list of prompts available on the server.
        
        Returns:
            List of prompt descriptions
        """
        return [
            {"name": name, "description": func.__doc__ or ""}
            for name, func in self.server.prompts.items()
        ]


# Mock implementation of the StdioServerParameters class
class StdioServerParameters:
    """
    Mock implementation of the StdioServerParameters class from the MCP SDK.
    """
    
    def __init__(self, command: List[str]):
        self.command = command
        

# Mock implementation of the AsyncExitStack class
class AsyncExitStack:
    """
    Mock implementation of the AsyncExitStack class.
    """
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def enter_async_context(self, context_manager):
        # For our mock, we just return a direct reference to a server
        # This isn't remotely realistic, but it works for testing
        from circuitmcp.mcp_server import mcp
        return ClientSession(mcp)
    
    async def aclose(self):
        pass 