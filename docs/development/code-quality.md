# Code Quality & Standards

Colony maintains high code quality through automated linting, formatting, and pre-commit hooks.

## Pre-commit Hooks

We use [pre-commit](https://pre-commit.com/) to automatically check code quality before commits.

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install the git hook scripts
cd colony
pre-commit install
```

### What Gets Checked

Our pre-commit configuration includes:

#### General Checks (All Files)
- **Trailing whitespace removal**
- **End-of-file fixer** (ensures files end with newline)
- **YAML syntax validation**
- **Large file detection** (prevents accidental commits of large files)
- **Case conflict detection**
- **Merge conflict markers**
- **JSON/TOML syntax validation**

#### Python (Backend)
- **Ruff** - Fast linting and code formatting (replaces Black, isort, and flake8)

#### JavaScript/TypeScript (Frontend)
- **Prettier** - Code formatting for JS, TS, JSON, CSS, and Markdown

#### Docker
- **Hadolint** - Dockerfile linting

#### Markdown
- **markdownlint** - Markdown formatting and style

### Usage

Pre-commit hooks run automatically on `git commit`. You can also run them manually:

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run

```

### Manual Python Code Quality

You can also run ruff manually for development:

```bash
cd backend

# Check and auto-fix linting issues
uv run ruff check . --fix

# Format code
uv run ruff format .

# Run both checks
uv run ruff format . && uv run ruff check . --fix
```

### Bypassing Hooks

In rare cases, you might need to bypass hooks:

```bash
# Bypass all hooks
git commit -m "your message" --no-verify

# Not recommended - only use when absolutely necessary
```

### Configuration Files

Pre-commit uses several configuration files:

- **`.pre-commit-config.yaml`** - Main pre-commit configuration
- **`pyproject.toml`** - Ruff configuration (linting and formatting rules)
- **`.prettierrc`** (if needed) - JavaScript/TypeScript formatting
- **`.markdownlint.json`** (if needed) - Markdown linting rules

## Code Style Guidelines

### Python (Backend)

We follow Python community standards using Ruff:

- **PEP 8** style guide
- **Ruff** for automatic formatting and linting
- **88 character line limit**
- **Type hints** for function signatures
- **Docstrings** for classes and functions

Example:
```python
def calculate_expense_total(expenses: List[Expense]) -> Decimal:
    """Calculate the total amount from a list of expenses.

    Args:
        expenses: List of expense objects

    Returns:
        Total amount as Decimal
    """
    return sum(expense.amount for expense in expenses)
```

### JavaScript/TypeScript (Frontend)

- **Prettier** for consistent formatting
- **ESLint** rules (to be added)
- **2-space indentation**
- **Semicolons required**
- **Single quotes preferred**

Example:
```typescript
interface ExpenseData {
  id: string;
  amount: number;
  category: string;
  date: Date;
}

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount);
};
```

### Documentation

- **Markdown** files should be properly formatted
- **Code blocks** must specify language
- **Links** should be descriptive
- **Headers** should follow hierarchy

## IDE Configuration

### VS Code

Recommended extensions and settings:

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./backend/.venv/bin/python",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### Recommended Extensions

Create `.vscode/extensions.json`:
```json
{
  "recommendations": [
    "ms-python.python",
    "charliermarsh.ruff",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-docker",
    "davidanson.vscode-markdownlint"
  ]
}
```

## Continuous Integration

Pre-commit hooks also run in CI/CD to ensure code quality:

```yaml
# In .github/workflows/ci.yml (future)
- name: Run pre-commit
  uses: pre-commit/action@v3.0.0
```

## Troubleshooting

### Common Issues

**Pre-commit fails on existing files:**
```bash
# Run on all files to fix existing issues
pre-commit run --all-files
```

**Python formatting/linting issues:**
```bash
# Make sure you're in the correct directory
cd backend

# Fix linting issues
uv run ruff check . --fix

# Format code
uv run ruff format .
```

**Node.js formatting issues:**
```bash
cd frontend
npx prettier --write src/
```

### Getting Help

If you encounter issues with code quality tools:

1. Check the tool's documentation
2. Run the tool manually to see detailed error messages
3. Ask in project discussions or issues
