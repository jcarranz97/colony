# Frontend Review Skill

You are reviewing **Colony's frontend** (`frontend/` folder) for compliance
with the project's HeroUI v3 component patterns and coding conventions.

## How to Run This Review

1. Get the diff between the current branch and `main`, scoped to `frontend/`:

   ```sh
   git diff main...HEAD -- frontend/
   ```

2. Also list the changed files for context:

   ```sh
   git diff --name-only main...HEAD -- frontend/
   ```

3. For each changed `.tsx` / `.ts` file, read the full file if the diff
   alone is not enough to judge.
4. Apply every rule in the **Pattern Library** below to the changed code.
5. Report findings in the format described in **Output Format**.

---

## Pattern Library

### 1. Dropdown

**When to use:** Any action menu, context menu, or navigation menu triggered
by a button press. Also use for **single-selection** and
**multiple-selection** pickers when the options are a list of actions or
labeled choices rendered in a popover.

**Do NOT use** `Dropdown` for form field value selection where a
label+trigger+value pattern is needed — use `Select` for that
(to be documented separately).

#### 1a. Basic Dropdown (action menu)

```tsx
import { Dropdown, Button, Label, Description, Header, Kbd, Separator } from '@heroui/react';

<Dropdown>
  <Dropdown.Trigger>
    <Button />
  </Dropdown.Trigger>
  <Dropdown.Popover>
    <Dropdown.Menu onAction={(key) => console.log(`Selected: ${key}`)}>
      <Dropdown.Item id="item-id" textValue="Item">
        <Label>Item</Label>
      </Dropdown.Item>
    </Dropdown.Menu>
  </Dropdown.Popover>
</Dropdown>
```

**Rules:**

- Always wrap with `<Dropdown>` root.
- Trigger is `<Dropdown.Trigger>` containing a `<Button>` (or `isIconOnly`
  button).
- Popover is `<Dropdown.Popover>`.
- Menu is `<Dropdown.Menu>` — use `onAction` for action handlers.
- Each item is `<Dropdown.Item id="..." textValue="...">` — both `id` and
  `textValue` are required.
- Item content: `<Label>` for the display text, optionally `<Description>`
  for a subtitle, `<Kbd>` for keyboard shortcut.

#### 1b. Single Selection

```tsx
import type { Selection } from "@heroui/react";
import { Button, Dropdown, Header, Label } from "@heroui/react";
import { useState } from "react";

const [selected, setSelected] = useState<Selection>(new Set(["default-value"]));

<Dropdown>
  <Button variant="secondary">Trigger Label</Button>
  <Dropdown.Popover className="min-w-[256px]">
    <Dropdown.Menu
      selectedKeys={selected}
      selectionMode="single"
      onSelectionChange={setSelected}
    >
      <Dropdown.Section>
        <Header>Section heading</Header>
        <Dropdown.Item id="value1" textValue="Option 1">
          <Dropdown.ItemIndicator />
          <Label>Option 1</Label>
        </Dropdown.Item>
        <Dropdown.Item id="value2" textValue="Option 2">
          <Dropdown.ItemIndicator />
          <Label>Option 2</Label>
        </Dropdown.Item>
      </Dropdown.Section>
    </Dropdown.Menu>
  </Dropdown.Popover>
</Dropdown>
```

**Rules:**

- Use `selectionMode="single"` on `<Dropdown.Menu>`.
- State type is `Selection` (imported from `@heroui/react`), initialized as
  `new Set(["default-id"])`.
- Pass `selectedKeys` + `onSelectionChange` to `<Dropdown.Menu>`.
- Each selectable item must include `<Dropdown.ItemIndicator />` before
  `<Label>`.
- Wrap items in `<Dropdown.Section>` with a `<Header>` when a group label
  is needed.
- **Note:** When used inside a `<Dropdown>`, the trigger button goes
  directly as a child of `<Dropdown>` (not wrapped in `<Dropdown.Trigger>`).
  Both forms are valid; be consistent within a file.

#### 1c. Multiple Selection

Same as single selection but with `selectionMode="multiple"`:

```tsx
<Dropdown.Menu
  selectedKeys={selected}
  selectionMode="multiple"
  onSelectionChange={setSelected}
>
```

#### 1d. Section-Level Selection (mixed modes)

Use separate state per section; apply `selectedKeys` / `selectionMode` /
`onSelectionChange` directly on `<Dropdown.Section>` (not on
`<Dropdown.Menu>`):

```tsx
<Dropdown.Menu>
  {/* Non-selectable actions */}
  <Dropdown.Section>
    <Header>Actions</Header>
    <Dropdown.Item id="cut" textValue="Cut"><Label>Cut</Label></Dropdown.Item>
  </Dropdown.Section>
  <Separator />
  {/* Single-select section */}
  <Dropdown.Section
    selectedKeys={alignment}
    selectionMode="single"
    onSelectionChange={setAlignment}
  >
    <Header>Alignment</Header>
    <Dropdown.Item id="left" textValue="Left">
      <Dropdown.ItemIndicator type="dot" />
      <Label>Left</Label>
    </Dropdown.Item>
  </Dropdown.Section>
  <Separator />
  {/* Multi-select section */}
  <Dropdown.Section
    selectedKeys={styles}
    selectionMode="multiple"
    onSelectionChange={setStyles}
  >
    <Header>Styles</Header>
    <Dropdown.Item id="bold" textValue="Bold">
      <Dropdown.ItemIndicator />
      <Label>Bold</Label>
    </Dropdown.Item>
  </Dropdown.Section>
</Dropdown.Menu>
```

**Rules:**

- Use `<Separator />` (imported from `@heroui/react`) between sections.
- For dot-style indicator (radio-like), use
  `<Dropdown.ItemIndicator type="dot" />`.
- For checkmark-style indicator (checkbox-like), use
  `<Dropdown.ItemIndicator />` (no type prop).

#### 1e. With Icons

```tsx
import { SomeIcon } from "@gravity-ui/icons"; // or react-icons

<Dropdown.Item id="delete" textValue="Delete" variant="danger">
  <SomeIcon className="size-4 shrink-0 text-danger" />
  <Label>Delete</Label>
</Dropdown.Item>
```

**Rules:**

- Icon goes before `<Label>` inside the item.
- Danger items use `variant="danger"` on the item.
- Icon classes: `size-4 shrink-0` — always apply `shrink-0` to prevent
  flex-shrink.

#### 1f. With Descriptions

```tsx
<Dropdown.Item id="new-file" textValue="New file">
  <div className="flex h-8 items-start justify-center pt-px">
    <SomeIcon className="size-4 shrink-0 text-muted" />
  </div>
  <div className="flex flex-col">
    <Label>New file</Label>
    <Description>Create a new file</Description>
  </div>
</Dropdown.Item>
```

**Rules:**

- When combining icon + description, wrap the icon in
  `div.flex.h-8.items-start.justify-center.pt-px`.
- Wrap `<Label>` and `<Description>` together in `div.flex.flex-col`.

#### 1g. With Sections and Separators

```tsx
import { Separator } from "@heroui/react";

<Dropdown.Menu>
  <Dropdown.Section>
    <Header>Section A</Header>
    <Dropdown.Item id="..." textValue="..."><Label>...</Label></Dropdown.Item>
  </Dropdown.Section>
  <Separator />
  <Dropdown.Section>
    <Header>Danger zone</Header>
    <Dropdown.Item id="delete" textValue="Delete" variant="danger">
      <Label>Delete</Label>
    </Dropdown.Item>
  </Dropdown.Section>
</Dropdown.Menu>
```

#### 1h. With Submenus

```tsx
<Dropdown.SubmenuTrigger>
  <Dropdown.Item id="parent" textValue="Parent">
    <Label>Parent</Label>
    <Dropdown.SubmenuIndicator />
  </Dropdown.Item>
  <Dropdown.Popover>
    <Dropdown.Menu>
      <Dropdown.Item id="child" textValue="Child"><Label>Child</Label></Dropdown.Item>
    </Dropdown.Menu>
  </Dropdown.Popover>
</Dropdown.SubmenuTrigger>
```

**Rules:**

- `<Dropdown.SubmenuIndicator />` goes after `<Label>` inside the trigger
  item.
- The nested `<Dropdown.Popover>` + `<Dropdown.Menu>` follows the same
  rules recursively.

---

## Common Anti-Patterns to Flag

| Anti-pattern | Correct pattern |
|---|---|
| Native `<select>` for user-facing dropdowns | `Dropdown` with `selectionMode="single"` |
| `<select>` with Tailwind styling | HeroUI `Select` or `Dropdown` |
| Missing `textValue` on `<Dropdown.Item>` | Always add `textValue` |
| Missing `id` on `<Dropdown.Item>` | Always add `id` |
| `<Dropdown.ItemIndicator />` missing | Required for all selectable items |
| `color="danger"` on `<Button>` (invalid prop) | `className="text-danger"` or item `variant="danger"` |
| `Modal.Backdrop` and `Modal.Container` as siblings | Nest `Modal.Container` inside `Modal.Backdrop` |

---

## Output Format

Produce a structured review report with these sections:

### ✅ Compliant

List files/patterns that correctly follow the rules. Be brief.

### ⚠️ Issues Found

For each issue:

- **File:** `path/to/file.tsx` (line N if determinable)
- **Rule violated:** Which pattern rule above
- **Current code:** Short snippet of what's wrong
- **Fix:** Short snippet showing the corrected code

### 📋 Summary

One paragraph: overall compliance level, most common issue, and whether any
violations are blocking (would cause visible bugs) vs. stylistic.

---

## Notes for the Reviewer

- Only review files under `frontend/` in the diff.
- Skip test files, config files (`.env`, `next.config.ts`, etc.), and
  generated files.
- If a pattern is not yet documented in this skill, do not flag it — note
  it as "outside current scope."
- When a file uses a pattern correctly, acknowledge it explicitly so the
  developer knows what to keep doing.
- Be precise: quote actual code from the diff, not generic examples.
