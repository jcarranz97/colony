"""Colony MCP server package.

A thin Model Context Protocol server that exposes the Colony expense
management API to agentic clients. It holds no credentials of its own —
every request forwards the caller's Colony personal access token.
"""

__version__ = "0.1.0"
