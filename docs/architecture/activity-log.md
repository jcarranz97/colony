# Activity Log & Comments

Colony tracks two complementary kinds of history on every domain entity:

- **Activity log** — system-generated, append-only events (e.g.
  `created`, `marked_paid`, `updated`).
- **Comments** — user-authored, Markdown-bodied notes, editable by the
  author and soft-deletable by the author or any admin.

Both share a polymorphic shape: an `entity_type` enum + `entity_id` UUID
pair pointing at the target row. This lets the same two tables cover
payment methods, recurrent expenses, recurrent incomes, cycles, cycle
expenses, and cycle incomes without a fan-out of per-entity tables.

## Data model

### `activity_log`

| column          | type           | notes                                          |
| --------------- | -------------- | ---------------------------------------------- |
| `id`            | UUID PK        |                                                |
| `household_id`  | UUID FK        | households.id, ON DELETE CASCADE               |
| `entity_type`   | VARCHAR(40)    | `payment_method`, `cycle`, etc.                |
| `entity_id`     | UUID           | refs the entity GUID; no DB-level FK           |
| `cycle_id`      | UUID FK NULL   | cycles.id, denormalized for cycle-feed queries |
| `actor_user_id` | UUID FK        | users.id                                       |
| `action`        | VARCHAR(40)    | `created` / `updated` / `marked_paid` / …      |
| `changes`       | JSONB          | `{field: {"from": old, "to": new}}`            |
| `created_at`    | TIMESTAMP      | from BaseModel                                 |

Indexes:

- `(household_id, created_at DESC)`
- `(entity_type, entity_id, created_at DESC)`
- `(cycle_id, created_at DESC)`
- `(actor_user_id, created_at DESC)`

The table is treated as append-only. The `active` column (inherited
from `BaseModel`) is always `True` — soft-delete semantics don't apply
to an audit trail.

### `comments`

| column           | type           | notes                                |
| ---------------- | -------------- | ------------------------------------ |
| `id`             | UUID PK        |                                      |
| `household_id`   | UUID FK        | households.id, ON DELETE CASCADE     |
| `entity_type`    | VARCHAR(40)    | same enum as activity_log            |
| `entity_id`      | UUID           | polymorphic ref                      |
| `cycle_id`       | UUID FK NULL   | denormalized                         |
| `author_user_id` | UUID FK        | users.id                             |
| `body`           | TEXT           | raw Markdown (no server sanitization) |
| `edited_at`      | TIMESTAMP NULL | NULL until first edit                |
| `active`         | BOOLEAN        | soft-delete flag (BaseModel)         |

Indexes match activity_log but include `WHERE active`.

## Polymorphic targets (`EntityType`)

| value                | commentable | tracked in activity log |
| -------------------- | ----------- | ----------------------- |
| `payment_method`     | yes         | yes                     |
| `recurrent_expense`  | yes         | yes                     |
| `recurrent_income`   | yes         | yes                     |
| `cycle`              | yes         | yes                     |
| `cycle_expense`      | yes         | yes                     |
| `cycle_income`       | yes         | yes                     |
| `comment`            | no          | derivative events only  |

Recurrent expense edits are recorded **only on the source template**
(not propagated to existing cycle expenses generated from it). This
matches the user expectation that editing the template should not
silently rewrite historical receipts.

## Actions

| action             | typical entity types                       |
| ------------------ | ------------------------------------------ |
| `created`          | every entity                               |
| `updated`          | every entity (diff lives in `changes`)     |
| `deactivated`      | every entity (soft delete)                 |
| `reactivated`      | every entity (admin restore)               |
| `marked_paid`      | cycle_expense                              |
| `marked_unpaid`    | cycle_expense                              |
| `status_changed`   | cycle_expense (cancelled/skipped/etc.)     |
| `completed`        | cycle (status transition → `completed`)    |
| `commented`        | recorded when a comment is added           |
| `comment_edited`   | recorded when an author edits their body   |
| `comment_deleted`  | recorded when a comment is soft-deleted    |

For lifecycle events (`commented`, `comment_edited`, `comment_deleted`),
the activity row carries the parent entity's `entity_type` + `entity_id`
so a single feed query returns the comment alongside everything else
that happened.

## Write path

Each domain's service module calls
`activity_service.record(...)` after applying its mutation (and after
`db.flush()` to populate generated IDs). The activity row is committed
in the same transaction as the underlying change — there's no
out-of-band queue, so failed mutations never leave an orphan activity
row.

The `compute_diff(before, after)` helper in
`backend/app/activity/helpers.py` produces the `changes` JSONB. It
serializes UUIDs, dates, decimals, and enums to JSON-safe values so the
diff can be stored and rendered without further conversion.

## Read path

| endpoint                                    | filters                                       |
| ------------------------------------------- | --------------------------------------------- |
| `GET /api/v1/activity?entity_type=…&entity_id=…` | one entity's timeline                     |
| `GET /api/v1/activity?cycle_id=…`           | every event tied to a cycle                   |
| `GET /api/v1/comments?entity_type=…&entity_id=…` | one entity's comments                     |
| `GET /api/v1/comments?cycle_id=…`           | every comment inside a cycle                  |
| `POST /api/v1/comments`                     | author becomes `current_user`                 |
| `PATCH /api/v1/comments/{id}`               | author only                                   |
| `DELETE /api/v1/comments/{id}`              | author or admin (soft-delete)                 |

Calling `GET /api/v1/activity/` without a scope returns an empty list
on purpose — we never expose the household-wide activity log via a
single request, to avoid accidentally leaking the full timeline.

## Permissions

- Reading activity / comments: any user in the household sees
  everything in the household. Cross-household isolation is enforced in
  the service layer via the `household_id` filter.
- Creating a comment: any authenticated household member.
- Editing a comment: only the comment's author.
- Deleting a comment: author OR a user with `role == "admin"`.

## Markdown rendering

Comments are stored verbatim. The frontend uses `react-markdown` with
`remark-gfm` (tables, strikethrough, autolinks). Raw HTML is
intentionally not rendered (no `rehype-raw`), so comments cannot embed
arbitrary HTML or scripts.

## Scaling notes

- The compound indexes keep all common queries (entity feed, cycle
  feed) at O(log n) regardless of table size.
- For a personal-finance app the activity_log table is expected to
  grow slowly. If it ever reaches a few million rows, the next steps
  are: monthly partitioning, or a background job that archives rows
  older than N months to cold storage.
- Comments are also expected to stay small. No pagination ceiling
  beyond the `MAX_PAGE_SIZE` (200) defined in
  `backend/app/activity/constants.py`.
