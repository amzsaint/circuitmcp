#!/bin/bash
# Setup script for CircuitMCP - installs all requirements, NGSpice, and configures the environment

set -e  # Exit on error

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}     CircuitMCP Setup Script                          ${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}This script will install CircuitMCP and all dependencies.${NC}"
echo

# Function to check command existence
command_exists() {
    command -v "$1" &> /dev/null
}

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if command_exists python3; then
    python_version=$(python3 --version | awk '{print $2}')
    echo -e "Python version: ${GREEN}$python_version${NC}"
    
    # Check if Python version is 3.9 or higher
    major_version=$(echo $python_version | cut -d. -f1)
    minor_version=$(echo $python_version | cut -d. -f2)
    
    if [ "$major_version" -lt 3 ] || ([ "$major_version" -eq 3 ] && [ "$minor_version" -lt 9 ]); then
        echo -e "${RED}Error: Python 3.9 or higher is required.${NC}"
        exit 1
    fi
else
    echo -e "${RED}Error: Python 3 not found. Please install Python 3.9 or higher.${NC}"
    exit 1
fi

# Determine OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
elif [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "win32" ]]; then
    OS="windows"
fi

echo -e "${YELLOW}Detected operating system: ${GREEN}$OS${NC}"

# Install NGSpice based on OS
echo -e "${YELLOW}Installing NGSpice...${NC}"
if [ "$OS" == "linux" ]; then
    if command_exists apt-get; then
        sudo apt-get update
        sudo apt-get install -y ngspice
    elif command_exists dnf; then
        sudo dnf install -y ngspice
    elif command_exists yum; then
        sudo yum install -y ngspice
    elif command_exists pacman; then
        sudo pacman -S --noconfirm ngspice
    else
        echo -e "${RED}Warning: Could not determine package manager. Please install NGSpice manually.${NC}"
        echo -e "Visit: http://ngspice.sourceforge.net/download.html"
    fi
elif [ "$OS" == "mac" ]; then
    if command_exists brew; then
        brew install ngspice
    else
        echo -e "${RED}Warning: Homebrew not found. Please install Homebrew and then NGSpice.${NC}"
        echo -e "Install Homebrew with: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo -e "Then install NGSpice with: brew install ngspice"
    fi
elif [ "$OS" == "windows" ]; then
    echo -e "${YELLOW}Please download and install NGSpice from: http://ngspice.sourceforge.net/download.html${NC}"
    echo -e "${YELLOW}Press any key to continue when NGSpice is installed...${NC}"
    read -n 1
else
    echo -e "${RED}Unsupported operating system. Please install NGSpice manually.${NC}"
    echo -e "Visit: http://ngspice.sourceforge.net/download.html"
fi

# Create virtual environment (optional)
echo -e "${YELLOW}Would you like to create a virtual environment? (y/n)${NC}"
read -r create_venv
if [[ $create_venv =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    # Check if virtualenv is installed
    if ! command_exists pip3; then
        echo -e "${RED}Error: pip3 not found. Please install pip.${NC}"
        exit 1
    fi
    
    pip3 install virtualenv
    
    if [ -d "venv" ]; then
        echo -e "${YELLOW}Virtual environment already exists. Activating it...${NC}"
    else
        python3 -m virtualenv venv
        echo -e "${GREEN}Virtual environment created.${NC}"
    fi
    
    # Activate virtual environment
    if [ "$OS" == "windows" ]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    echo -e "${GREEN}Virtual environment activated.${NC}"
fi

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip3 install -r requirements.txt

# Install CircuitMCP in development mode
echo -e "${YELLOW}Installing CircuitMCP in development mode...${NC}"
pip3 install -e .

# Check if UVX exists and install CircuitMCP with UVX if available
if command_exists uvx; then
    echo -e "${YELLOW}Installing CircuitMCP with UVX...${NC}"
    uvx install -y "$(pwd)"
    echo -e "${GREEN}CircuitMCP installed with UVX.${NC}"
else
    echo -e "${YELLOW}UVX not found. Skipping UVX installation.${NC}"
    echo -e "${YELLOW}To install with UVX later, run: uvx install git+https://github.com/amzsaint/circuitmcp.git${NC}"
fi

# Create schematics directory if it doesn't exist
mkdir -p schematics

# Run a simple test to verify installation
echo -e "${YELLOW}Running a simple test to verify installation...${NC}"
python3 -c "from circuitmcp import Circuit, mcp; print('Circuit class imported successfully'); print(f'Version: {mcp.__version__ if hasattr(mcp, \"__version__\") else \"0.1.0\"}')"

# Check if the test was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}CircuitMCP installation successful!${NC}"
else
    echo -e "${RED}There was an issue with the CircuitMCP installation.${NC}"
    exit 1
fi

# Print usage instructions
echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}CircuitMCP has been successfully installed.${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "${YELLOW}To use CircuitMCP:${NC}"
echo -e "  ${BLUE}1. Run the server:${NC}"
echo -e "     ${GREEN}circuitmcp-server${NC}"
echo
echo -e "  ${BLUE}2. In Python:${NC}"
echo -e "     ${GREEN}from circuitmcp import mcp, Circuit${NC}"
echo
echo -e "  ${BLUE}3. With Claude Desktop:${NC}"
echo -e "     ${GREEN}./examples/claude_desktop_demo.sh${NC}"
echo
echo -e "  ${BLUE}4. Run the example:${NC}"
echo -e "     ${GREEN}python examples/uvx_demo.py${NC}"
echo
echo -e "${BLUE}======================================================${NC}"

if [[ $create_venv =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Note: You're using a virtual environment. To use CircuitMCP in the future, activate it with:${NC}"
    if [ "$OS" == "windows" ]; then
        echo -e "  ${GREEN}source venv/Scripts/activate${NC}"
    else
        echo -e "  ${GREEN}source venv/bin/activate${NC}"
    fi
fi

echo -e "${BLUE}======================================================${NC}" 