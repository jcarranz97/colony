# MCP Server

The **Colony MCP server** exposes the Colony expense API to agentic
workflows through the [Model Context Protocol](https://modelcontextprotocol.io).
Once connected, an agent (Claude Code, opencode, or any MCP-capable client)
can answer questions like *"what's due this week?"*, *"when is my next
payment?"*, or *"is the electricity bill on autopay?"* — and take safe
actions such as marking an expense paid.

It is a standalone service in `mcp-server/`, built with
[FastMCP](https://gofastmcp.com), running alongside the backend, frontend,
and docs.

---

## Design principles

- **Stateless pass-through.** The MCP server stores **no** credentials. On
  every request it forwards the caller's Colony token to the REST API, so
  each user only ever sees their own data.
- **Curated tools.** Tools map to real tasks ("expenses due this week"),
  not 1:1 to REST endpoints. Fewer, well-described tools are easier for an
  agent to use correctly.
- **Deliberate write scope.** Tools can read everything, create cycles,
  mutate cycle expenses and incomes, and post comments on any item. They
  **cannot** edit or delete existing cycles, edit recurrent templates,
  delete anything, or manage households, users, or payment methods.
- **Multi-household by default.** Read tools aggregate across every
  household the user belongs to unless a household name is given.

---

## Architecture

```mermaid
flowchart LR
    agent["Agent<br/>(Claude Code / opencode)"]
    mcp["Colony MCP server<br/>(FastMCP, :8002)"]
    api["Colony API<br/>(FastAPI, :8000)"]
    db[("PostgreSQL")]

    agent -- "MCP over HTTP<br/>Authorization: Bearer colony_pat_…" --> mcp
    mcp -- "REST + forwarded token" --> api
    api --> db
```

The MCP server speaks the streamable-HTTP MCP transport. A single deployed
instance serves every user — requests are isolated by the token each one
carries, not by separate deployments.

---

## Authentication — Personal Access Tokens

Colony users authenticate the API with **Personal Access Tokens (PATs)** —
long-lived, named, revocable tokens, similar to GitHub PATs. They are
generated in the web app under **Settings → API Tokens**.

A PAT is prefixed `colony_pat_`. Only a SHA-256 hash is stored; the
plaintext is shown **once** at creation and is never recoverable.

The MCP client sends the PAT as an `Authorization: Bearer` header on the
MCP connection. The MCP server reads it from each inbound request and
replays it against the Colony API:

```mermaid
sequenceDiagram
    participant A as Agent
    participant M as MCP server
    participant C as Colony API
    A->>M: call tool (Authorization: Bearer colony_pat_…)
    M->>C: GET /cycles/ (same bearer token)
    C->>C: resolve PAT → user, scope to that user
    C-->>M: that user's data only
    M-->>A: tool result
```

Because the token *is* the user identity, per-user data isolation is
automatic: one user's PAT never returns another user's data. Revoking a
token in the web app cuts off the agent immediately.

!!! note "Why not OAuth?"
    A browser-based OAuth flow was considered. It would require turning
    Colony into a full OAuth authorization server — a much larger project.
    PATs give the same multi-user isolation and a clean revoke story with
    far less moving machinery, which suits a self-hosted, few-user app.

---

## Multi-household behaviour

Colony scopes data per household, and a user may belong to several. The
REST list endpoints accept an optional `household_id` query parameter
(see [API specification](api-specification.md)); omitting it falls back to
the user's active household.

The MCP read tools expose this as an optional `household` argument:

- **Omitted** → the tool queries `GET /households/me`, runs the request
  once per household, and **merges the results**, tagging each item with
  its household name.
- **Provided** → the tool resolves the name to an id and scopes to just
  that household.

Cycle-scoped tools (those taking a `cycle_id`) resolve the owning
household automatically — no `household` argument is needed.

`create_cycle` has no cycle to resolve from, so it accepts an optional
`household`. It must commit to exactly one household: when omitted, the
user's sole household is used; if they belong to several, the tool asks
them to name one.

---

## Tool catalogue

Read tools accept an optional `household` argument (omit to aggregate).

| Tool | Purpose |
|---|---|
| `whoami` | Identify the account the session is acting as |
| `list_households` | List the user's households |
| `list_cycles` | List budgeting cycles (optional `status` filter) |
| `get_current_cycle` | The open (active or draft) cycle(s) covering today |
| `get_cycle_summary` | Totals and status breakdown for a cycle |
| `list_cycle_expenses` | Expenses of one cycle, with a totals summary |
| `find_expenses` | Locate expenses across open cycles by description |
| `expenses_due_this_week` | Unpaid expenses due in the next 7 days |
| `upcoming_expenses` | Unpaid expenses due within `days` days |
| `overdue_expenses` | Expenses past due and still unpaid |
| `next_payment` | The single soonest unpaid expense |
| `list_autopay_expenses` | Expenses set to pay automatically |
| `list_cycle_incomes` | Incomes recorded in a cycle |
| `list_payment_methods` | Payment methods (cards, cash, transfers) |
| `recurrent_expenses_overview` | Recurrent expense templates (read-only) |
| `recurrent_incomes_overview` | Recurrent income templates (read-only) |

Write tools — cycle creation, plus cycle expenses and incomes:

| Tool | Purpose |
|---|---|
| `create_cycle` | Create a new budgeting cycle (optionally seeded from templates) |
| `mark_expense_paid` | Mark a single cycle expense as paid |
| `mark_cycle_expenses_paid` | Mark several (or all unpaid) expenses in a cycle paid |
| `skip_expense` | Mark an expense as skipped (not applicable this cycle) |
| `mark_expense_paid_other` | Mark an expense as paid by other means (off-budget) |
| `reset_expense_to_pending` | Undo a skip or "paid (other)" mark, back to pending |
| `add_cycle_expense` | Add a new expense to a cycle |
| `update_cycle_expense` | Update fields on a cycle expense |
| `add_cycle_income` | Record a new income in a cycle |
| `update_cycle_income` | Update fields on a cycle income |

Comments — read and write notes on any Colony item:

| Tool | Purpose |
|---|---|
| `add_comment` | Post a comment on any item (cycle, expense, income, …) |
| `get_comments` | List the comments on a single item |
| `get_cycle_comments` | List every comment across a whole cycle |

Comments resolve against the user's **active household** — the comments
endpoints are not multi-household, so an item in a different household
has no visible comments and cannot be commented on.

Editing or deleting existing cycles, recurrent templates, households,
users, payment methods, and exchange rates are **not** supported through
the MCP server. Comments themselves cannot be edited or deleted through
the MCP server either — only created and read.

---

## Connecting an agent

First, generate a token: open the Colony web app, go to **Settings → API
Tokens**, create one, and copy the `colony_pat_…` secret (shown once).

### Claude Code

```bash
claude mcp add --transport http colony \
  http://localhost:8002/mcp \
  --header "Authorization: Bearer colony_pat_your_token_here"
```

In production, replace the URL with the deployed address, e.g.
`http://<node-ip>:30820/mcp` or `http://mcp.colony.dev.lan/mcp`.

#### Always allowing Colony tools

By default Claude Code asks for confirmation before each MCP tool call.
To stop the prompts for the Colony server, allow its tools once.

**Interactively** — when Claude next asks to run a Colony tool, choose the
*"Yes, and don't ask again"* option in the prompt.

**Persistently** — add a permission rule to a Claude Code `settings.json`.
MCP tools are named `mcp__<server>__<tool>`, and the rule `mcp__colony`
covers **every** tool on the `colony` server:

```json
{
  "permissions": {
    "allow": ["mcp__colony"]
  }
}
```

Put this in `.claude/settings.json` inside a project (applies there) or in
`~/.claude/settings.json` (applies everywhere). The `/permissions` slash
command edits the same lists from inside a session.

!!! note "Allowing reads but not writes"
    `mcp__colony` also auto-approves the write tools (`mark_expense_paid`,
    `add_cycle_expense`, …). To keep a confirmation prompt on changes,
    list the read tools individually instead — e.g.
    `mcp__colony__expenses_due_this_week`, `mcp__colony__next_payment` —
    and leave the write tools out of the allow list.

### opencode

Add to `opencode.json`:

```json
{
  "mcp": {
    "colony": {
      "type": "remote",
      "url": "http://localhost:8002/mcp",
      "enabled": true,
      "headers": {
        "Authorization": "Bearer colony_pat_your_token_here"
      }
    }
  }
}
```

Each person uses **their own** token, so the same shared MCP server gives
each of them only their own data.

### Updating the token

A token stops working when it expires, is revoked, or — as after a
`docker compose down -v` — the database that stores it is wiped and
recreated. The MCP server itself keeps no tokens; each agent client
holds its own copy, so the fix is to update it in that client.

First, generate a fresh token: in the Colony web app go to **Settings →
API Tokens**, create one, and copy the new `colony_pat_…` secret.

**Claude Code** — there is no in-place edit, so remove the server and
add it again with the new token:

```bash
claude mcp remove colony
claude mcp add --transport http colony \
  http://localhost:8002/mcp \
  --header "Authorization: Bearer colony_pat_your_new_token_here"
```

Then run `claude mcp list` to confirm `colony` reconnects. Permission
rules in `settings.json` are keyed by the server name (`colony`), so
they survive the re-add — there is no need to re-allow the tools. If
you originally added the server with an explicit scope (`-s user` or
`-s project`), pass the same `-s` flag to `claude mcp remove`.

**opencode** — edit `opencode.json` and replace the old `colony_pat_…`
value in the `Authorization` header with the new one, then restart
opencode so it picks up the change:

```json
{
  "mcp": {
    "colony": {
      "type": "remote",
      "url": "http://localhost:8002/mcp",
      "enabled": true,
      "headers": {
        "Authorization": "Bearer colony_pat_your_new_token_here"
      }
    }
  }
}
```

---

## Configuration

The MCP server is configured entirely through environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `COLONY_API_URL` | `http://localhost:8000/api/v1` | Colony REST API base URL |
| `MCP_HOST` | `0.0.0.0` | Bind address |
| `MCP_PORT` | `8002` | Bind port |
| `MCP_TRANSPORT` | `http` | FastMCP transport |
| `MCP_PATH` | `/mcp` | HTTP path the MCP server is served on |
| `COLONY_REQUEST_TIMEOUT` | `30` | Per-request timeout (seconds) |

A plain `GET /health` endpoint (outside the MCP path) is provided for
container liveness and readiness probes.

---

## Local development

`docker compose up --build` starts the MCP server alongside the rest of
the stack:

| Service | URL |
|---|---|
| MCP server | `http://localhost:8002/mcp` |
| Health check | `http://localhost:8002/health` |

To run it directly against a local backend:

```bash
cd mcp-server
uv sync
COLONY_API_URL=http://localhost:8000/api/v1 uv run python -m colony_mcp.server
```

---

## Production deployment

The MCP server ships as its own image and Helm-managed workload.

**Build and push** to the Harbor registry (same convention as the backend
and frontend images):

```bash
docker build -t 192.168.1.206:30002/library/colony-mcp:latest ./mcp-server
docker push 192.168.1.206:30002/library/colony-mcp:latest
```

**Deploy** with the Helm chart — the `mcp` block in `helm/colony/values.yaml`
controls the image, replica count, and `NodePort` (default `30820`):

```bash
helm upgrade --install colony ./helm/colony
```

The chart creates an `mcp` Deployment, Service, and ConfigMap. No
Kubernetes Secret is needed — the MCP server holds no credentials; users'
tokens travel in request headers. By default the ConfigMap points
`COLONY_API_URL` at the in-cluster backend Service.

Point an agent at `http://<node-ip>:30820/mcp` with a Colony PAT.

### Reaching it by hostname (ingress)

To reach the MCP server by hostname instead of a NodePort — alongside the
frontend and backend ingresses — set `ingress.mcp.host`:

```bash
helm upgrade --install colony ./helm/colony \
  --set ingress.enabled=true \
  --set ingress.frontend.host=colony.dev.lan \
  --set ingress.backend.host=api.colony.dev.lan \
  --set ingress.mcp.host=mcp.colony.dev.lan
```

The MCP ingress is opt-in: it renders only when `ingress.mcp.host` is set,
so an existing deployment is unaffected until you add it. The agent then
connects at `http://mcp.colony.dev.lan/mcp`.

The MCP endpoint has no transport-level auth of its own — it is protected
entirely by the per-request Colony token. Keep the hostname resolvable on
the LAN only (e.g. via Pi-hole), as you would for the backend.
