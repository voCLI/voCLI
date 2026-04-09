"""VOCLI MCP Server — local voice layer for AI coding tools."""

import sys
import os
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("vocli")

# Ensure Homebrew paths are available on macOS
if sys.platform == "darwin":
    for p in ["/opt/homebrew/bin", "/usr/local/bin"]:
        if p not in os.environ.get("PATH", ""):
            os.environ["PATH"] = p + ":" + os.environ.get("PATH", "")

# Import tools to register them with the MCP server
import vocli.tools  # noqa: F401, E402


def main():
    """Run the VOCLI MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
