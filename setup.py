from setuptools import setup, find_packages
import os

# Read requirements from requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Read long description from README.md
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="circuitmcp",
    version="0.1.0",
    author="CircuitMCP Team",
    author_email="your.email@example.com",
    description="Circuit simulation capabilities exposed through Anthropic's Model Context Protocol (MCP)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/amzsaint/circuitmcp",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "circuitmcp-server=circuitmcp.main:main",
        ],
    },
) 