# Colony MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io) server that
exposes the Colony expense-management API to agentic clients (Claude Code,
opencode, and other MCP-capable agents).

It is a thin, stateless wrapper over the Colony REST API. It holds **no**
credentials: every request forwards the caller's Colony **personal access
token** (PAT), so each user only ever sees their own data.

## Quick start (local)

```bash
docker compose up --build        # from the repo root
# MCP server → http://localhost:8002/mcp
```

Generate a PAT in the Colony web app (Settings → API Tokens), then point
an agent at the server:

```bash
claude mcp add --transport http colony http://localhost:8002/mcp \
  --header "Authorization: Bearer colony_pat_..."
```

## Running directly

```bash
uv sync
COLONY_API_URL=http://localhost:8000/api/v1 uv run python -m colony_mcp.server
```

## Configuration

All settings are environment variables (see `colony_mcp/config.py`):

| Variable | Default | Purpose |
|---|---|---|
| `COLONY_API_URL` | `http://localhost:8000/api/v1` | Colony REST API base URL |
| `MCP_HOST` | `0.0.0.0` | Bind address |
| `MCP_PORT` | `8002` | Bind port |
| `MCP_TRANSPORT` | `http` | FastMCP transport |
| `MCP_PATH` | `/mcp` | HTTP path the server is served on |
| `COLONY_REQUEST_TIMEOUT` | `30` | Per-request timeout (seconds) |

## Tools

Read tools aggregate across every household the user belongs to unless a
`household` name is passed. Write tools are limited to cycle expenses and
incomes — recurrent templates are read-only by design.

See `docs/architecture/mcp-server.md` for the full catalogue.
