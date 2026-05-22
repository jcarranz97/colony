# Colony MCP Server

Standalone [FastMCP](https://gofastmcp.com) server that wraps the Colony
REST API for agentic clients. Python 3.13+, managed with `uv`.

## Layout

```text
mcp-server/
├── colony_mcp/
│   ├── config.py        # env-var settings (pydantic-settings)
│   ├── client.py        # httpx wrapper; forwards the caller's PAT
│   ├── households.py    # resolve / aggregate across households
│   ├── server.py        # FastMCP instance, /health route, entry point
│   └── tools/           # one module per tool group
│       ├── overview.py  # whoami, list_households
│       ├── cycles.py    # cycles, summaries, incomes
│       ├── expenses.py  # due / overdue / autopay, mark paid
│       ├── payments.py  # payment methods, recurrent templates (read-only)
│       └── comments.py  # read / write comments on any item
└── Dockerfile
```

## Commands

```bash
uv sync                                  # install deps
uv run python -m colony_mcp.server       # run the server
uv run ruff check . --fix && uv run ruff format .
uv run pyright .
```

## Conventions

- **No credentials in this server.** Every Colony call goes through
  `colony_request()` in `client.py`, which forwards the inbound
  `Authorization` header. Never add a service account.
- **Curated tools only.** Each tool is a small, well-documented async
  function — not a 1:1 mirror of a REST endpoint. Docstrings and type
  hints become the schema the agent sees, so keep them clear.
- **Write scope is deliberate.** Tools may read anything, create cycles,
  and mutate cycle expenses/incomes. Do **not** add tools that edit or
  delete existing cycles, or that create/edit/delete recurrent templates,
  households, users, or payment methods.
- **Adding a tool:** write the async function in the relevant
  `tools/*.py` module, then register it in that module's `register()`.
- Type-hint everything; Google-style docstrings; 88-char lines.
