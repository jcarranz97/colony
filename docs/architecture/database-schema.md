# Database Schema

Colony uses PostgreSQL for reliable financial data management with ACID transactions and complex relationship queries.

## Database Choice: PostgreSQL

- **ACID Compliance**: Essential for financial data integrity
- **Complex Queries**: Supports advanced reporting and analytics
- **JSON Support**: Flexible configuration storage (recurrence patterns)
- **Decimal Precision**: Accurate financial calculations
- **Mature Ecosystem**: Well-supported with excellent tooling

## Schema Overview

```mermaid
erDiagram
    users ||--o{ payment_methods : owns
    users ||--o{ expense_templates : creates
    users ||--o{ cycles : manages
    cycles ||--o{ cycle_expenses : contains
    expense_templates ||--o{ cycle_expenses : generates
    payment_methods ||--o{ expense_templates : uses
    payment_methods ||--o{ cycle_expenses : uses

    users {
        uuid id PK
        string email UK
        string password_hash
        string first_name
        string last_name
        string preferred_currency
        string locale
        boolean active
        timestamp created_at
        timestamp updated_at
    }

    payment_methods {
        uuid id PK
        uuid user_id FK
        string name
        string method_type
        string default_currency
        string description
        boolean active
        timestamp created_at
        timestamp updated_at
    }

    expense_templates {
        uuid id PK
        uuid user_id FK
        uuid payment_method_id FK
        string description
        string currency
        decimal base_amount
        string category
        string recurrence_type
        json recurrence_config
        date reference_date
        string autopay_info
        boolean active
        timestamp created_at
        timestamp updated_at
    }

    cycles {
        uuid id PK
        uuid user_id FK
        date start_date
        date end_date
        decimal income_amount
        decimal remaining_balance
        string status
        string name
        timestamp created_at
        timestamp updated_at
    }

    cycle_expenses {
        uuid id PK
        uuid cycle_id FK
        uuid template_id FK
        uuid payment_method_id FK
        string description
        string currency
        decimal amount
        decimal amount_usd
        date due_date
        string category
        string autopay_info
        string status
        string comments
        boolean paid
        timestamp paid_at
        timestamp created_at
        timestamp updated_at
    }

    exchange_rates {
        uuid id PK
        string from_currency
        string to_currency
        decimal rate
        date rate_date
        timestamp created_at
    }
```

## Global Types

Before creating tables, we define custom types that ensure data consistency across the schema:

```sql
-- ===========================================
-- GLOBAL ENUMS (Create these first)
-- ===========================================

-- Supported currencies (ISO 4217 codes)
CREATE TYPE currency_code AS ENUM ('USD', 'MXN');

-- Payment method types
CREATE TYPE payment_method_type AS ENUM ('debit', 'credit', 'cash', 'transfer');

-- Expense categorization
CREATE TYPE expense_category AS ENUM ('fixed', 'variable');

-- Template recurrence patterns
CREATE TYPE recurrence_type AS ENUM ('weekly', 'bi_weekly', 'monthly', 'custom');

-- Cycle lifecycle states
CREATE TYPE cycle_status AS ENUM ('draft', 'active', 'completed');

-- Individual expense states
CREATE TYPE expense_status AS ENUM ('pending', 'paid', 'cancelled', 'overdue');
```

### ENUM Descriptions

| Type | Values | Description |
|------|--------|-------------|
| `currency_code` | `USD`, `MXN` | ISO 4217 currency codes for supported currencies |
| `payment_method_type` | `debit`, `credit`, `cash`, `transfer` | Types of payment methods available |
| `expense_category` | `fixed`, `variable` | Expense categorization for budgeting |
| `recurrence_type` | `weekly`, `bi_weekly`, `monthly`, `custom` | How often template expenses recur |
| `cycle_status` | `draft`, `active`, `completed` | Lifecycle state of expense cycles |
| `expense_status` | `pending`, `paid`, `cancelled`, `overdue` | Current state of individual expenses |

## Table Definitions

### Users
Primary user accounts for the application.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    preferred_currency currency_code DEFAULT 'USD',  -- Uses global ENUM
    locale VARCHAR(10) DEFAULT 'en-US',
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(active);
```

### Payment Methods
User-defined payment methods (cards, accounts, cash).

```sql
CREATE TABLE payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    method_type payment_method_type NOT NULL,        -- Uses global ENUM
    default_currency currency_code NOT NULL,         -- Uses global ENUM
    description TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_user_payment_method_name UNIQUE(user_id, name)
);

CREATE INDEX idx_payment_methods_user_id ON payment_methods(user_id);
CREATE INDEX idx_payment_methods_active ON payment_methods(active);
```

### Expense Templates
Reusable templates for recurring expenses.

```sql
CREATE TABLE expense_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    payment_method_id UUID NOT NULL REFERENCES payment_methods(id),
    description VARCHAR(255) NOT NULL,
    currency currency_code NOT NULL,
    base_amount DECIMAL(10,2) NOT NULL CHECK (base_amount > 0),
    category expense_category NOT NULL,
    recurrence_type recurrence_type NOT NULL,
    recurrence_config JSONB NOT NULL DEFAULT '{}',
    reference_date DATE NOT NULL,  -- Last known occurrence (e.g., "1/12/2025 - last insurance bill")
    autopay_info TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_expense_templates_user_id ON expense_templates(user_id);
CREATE INDEX idx_expense_templates_active ON expense_templates(active);
CREATE INDEX idx_expense_templates_category ON expense_templates(category);
```

### Cycles
6-week expense management periods.

```sql
CREATE TABLE cycles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    income_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    remaining_balance DECIMAL(10,2) NOT NULL DEFAULT 0,
    status cycle_status DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_cycle_dates CHECK (end_date > start_date),
    CONSTRAINT unique_user_cycle_name UNIQUE(user_id, name)
);

CREATE INDEX idx_cycles_user_id ON cycles(user_id);
CREATE INDEX idx_cycles_status ON cycles(status);
CREATE INDEX idx_cycles_dates ON cycles(start_date, end_date);
```

### Cycle Expenses
Individual expenses within a cycle.

```sql
CREATE TABLE cycle_expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id UUID NOT NULL REFERENCES cycles(id) ON DELETE CASCADE,
    template_id UUID REFERENCES expense_templates(id),
    payment_method_id UUID NOT NULL REFERENCES payment_methods(id),
    description VARCHAR(255) NOT NULL,
    currency currency_code NOT NULL,
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    amount_usd DECIMAL(10,2) NOT NULL CHECK (amount_usd > 0),
    due_date DATE NOT NULL,
    category expense_category NOT NULL,
    autopay_info TEXT,
    status expense_status DEFAULT 'pending',
    comments TEXT,
    paid BOOLEAN DEFAULT false,
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cycle_expenses_cycle_id ON cycle_expenses(cycle_id);
CREATE INDEX idx_cycle_expenses_template_id ON cycle_expenses(template_id);
CREATE INDEX idx_cycle_expenses_due_date ON cycle_expenses(due_date);
CREATE INDEX idx_cycle_expenses_status ON cycle_expenses(status);
CREATE INDEX idx_cycle_expenses_paid ON cycle_expenses(paid);
```

### Exchange Rates
Currency conversion rates for financial calculations.

```sql
CREATE TABLE exchange_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_currency currency_code NOT NULL,
    to_currency currency_code NOT NULL,
    rate DECIMAL(10,6) NOT NULL CHECK (rate > 0),
    rate_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_currency_date UNIQUE(from_currency, to_currency, rate_date)
);

CREATE INDEX idx_exchange_rates_currencies ON exchange_rates(from_currency, to_currency);
CREATE INDEX idx_exchange_rates_date ON exchange_rates(rate_date);
```

## Relationship Details

### User → Payment Methods (1:N)
- Users can have multiple payment methods
- Payment methods belong to one user
- Soft delete preserves historical data

### User → Expense Templates (1:N)
- Users create multiple templates
- Templates define recurring expense patterns
- Templates reference payment methods

### User → Cycles (1:N)
- Users manage multiple 6-week cycles
- Each cycle has defined start/end dates
- Cycles track income and remaining balance

### Cycle → Cycle Expenses (1:N)
- Each cycle contains multiple expenses
- Expenses can be generated from templates
- Manual expenses allowed within cycles

### Template → Cycle Expenses (1:N)
- Templates can generate multiple expenses across cycles
- Relationship tracks which template generated each expense
- Optional relationship (manual expenses have NULL template_id)

## Recurrence Configuration Schema

The `recurrence_config` JSONB field stores type-specific configuration for calculating expense occurrences. The schema varies based on the `recurrence_type`.

### Weekly Recurrence

For expenses that occur on a specific day of the week (e.g., every Saturday for groceries).

```json
{
  "day_of_week": 6
}
```

**Schema:**
- `day_of_week` (integer, required): Day of the week (0=Sunday, 1=Monday, ..., 6=Saturday)

**Examples:**
```json
// Every Saturday (groceries)
{
  "day_of_week": 6
}

// Every Tuesday (therapy appointment)
{
  "day_of_week": 2
}
```

**Calculation Logic:**
1. Find the first occurrence of `day_of_week` on or after cycle start date
2. Generate weekly occurrences until cycle end date
3. Reference date is used to validate the pattern matches historical data

### Bi-Weekly Recurrence

For expenses that occur every 14 days, typically aligned with pay cycles.

```json
{
  "interval_days": 14
}
```

**Schema:**
- `interval_days` (integer, required): Number of days between occurrences (typically 14)

**Examples:**
```json
// Every 14 days (bi-weekly paycheck deductions)
{
  "interval_days": 14
}

// Every 10 days (custom medication refill)
{
  "interval_days": 10
}
```

**Calculation Logic:**
1. Start from reference date
2. Add/subtract `interval_days` to find occurrences within cycle period
3. Generate all dates that fall within cycle start/end dates

### Monthly Recurrence

For expenses that occur on the same day each month (e.g., rent, utilities).

```json
{
  "day_of_month": 15
}
```

**Schema:**
- `day_of_month` (integer, required): Day of the month (1-31)
- `handle_month_end` (boolean, optional): How to handle months with fewer days (default: false)

**Examples:**
```json
// 1st of every month (rent)
{
  "day_of_month": 1
}

// 15th of every month (credit card payment)
{
  "day_of_month": 15
}

// Last day of month (salary)
{
  "day_of_month": 31,
  "handle_month_end": true
}
```

**Calculation Logic:**
1. For each month that overlaps with cycle period
2. Use `day_of_month` as the occurrence date
3. If `handle_month_end` is true and `day_of_month` > days in month, use last day of month
4. Skip months where the calculated date is outside cycle period

### Custom Recurrence

For complex patterns like quarterly, semi-annual, or irregular intervals.

```json
{
  "interval": 3,
  "unit": "months",
  "day_of_month": 15
}
```

**Schema:**
- `interval` (integer, required): Number of units between occurrences
- `unit` (string, required): Time unit - one of: "days", "weeks", "months", "years"
- `day_of_month` (integer, optional): Specific day for month/year units (1-31)
- `month_of_year` (integer, optional): Specific month for year units (1-12)
- `day_of_week` (integer, optional): Specific day for week units (0-6)

**Examples:**
```json
// Every 3 months on the 15th (quarterly insurance)
{
  "interval": 3,
  "unit": "months",
  "day_of_month": 15
}

// Every 2 months on the 1st (bi-monthly subscription)
{
  "interval": 2,
  "unit": "months",
  "day_of_month": 1
}

// Every 6 months on the 1st (semi-annual payment)
{
  "interval": 6,
  "unit": "months",
  "day_of_month": 1
}

// Every 45 days (custom interval)
{
  "interval": 45,
  "unit": "days"
}

// Annually on January 1st (yearly subscription)
{
  "interval": 1,
  "unit": "years",
  "day_of_month": 1,
  "month_of_year": 1
}

// Every 3 weeks on Wednesday
{
  "interval": 3,
  "unit": "weeks",
  "day_of_week": 3
}
```

**Calculation Logic:**
1. Start from reference date
2. Calculate interval based on unit:
   - `days`: Add/subtract `interval` days
   - `weeks`: Add/subtract `interval * 7` days, optionally align to `day_of_week`
   - `months`: Add/subtract `interval` months, use `day_of_month` if specified
   - `years`: Add/subtract `interval` years, use `month_of_year` and `day_of_month` if specified
3. Generate all occurrences that fall within cycle period

## Implementation Examples

### Python Calculation Functions

```python
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Any

def calculate_occurrences(
    recurrence_type: str,
    recurrence_config: Dict[str, Any],
    reference_date: date,
    cycle_start: date,
    cycle_end: date
) -> List[date]:
    """Calculate expense occurrences within a cycle period."""

    if recurrence_type == "weekly":
        return calculate_weekly_occurrences(
            recurrence_config, reference_date, cycle_start, cycle_end
        )
    elif recurrence_type == "bi_weekly":
        return calculate_bi_weekly_occurrences(
            recurrence_config, reference_date, cycle_start, cycle_end
        )
    elif recurrence_type == "monthly":
        return calculate_monthly_occurrences(
            recurrence_config, reference_date, cycle_start, cycle_end
        )
    elif recurrence_type == "custom":
        return calculate_custom_occurrences(
            recurrence_config, reference_date, cycle_start, cycle_end
        )
    else:
        raise ValueError(f"Unknown recurrence type: {recurrence_type}")

def calculate_weekly_occurrences(
    config: Dict[str, Any],
    reference_date: date,
    cycle_start: date,
    cycle_end: date
) -> List[date]:
    """Calculate weekly occurrences."""
    day_of_week = config["day_of_week"]
    occurrences = []

    # Find first occurrence in or after cycle start
    current_date = cycle_start
    days_ahead = (day_of_week - current_date.weekday()) % 7
    current_date += timedelta(days=days_ahead)

    # Generate weekly occurrences
    while current_date <= cycle_end:
        occurrences.append(current_date)
        current_date += timedelta(days=7)

    return occurrences

def calculate_bi_weekly_occurrences(
    config: Dict[str, Any],
    reference_date: date,
    cycle_start: date,
    cycle_end: date
) -> List[date]:
    """Calculate bi-weekly occurrences."""
    interval = config["interval_days"]
    occurrences = []

    # Start from reference date and work backwards/forwards
    current_date = reference_date

    # Go backwards to find start point
    while current_date > cycle_start:
        current_date -= timedelta(days=interval)

    # Go forward to find all occurrences in cycle
    while current_date <= cycle_end:
        if cycle_start <= current_date <= cycle_end:
            occurrences.append(current_date)
        current_date += timedelta(days=interval)

    return occurrences

def calculate_monthly_occurrences(
    config: Dict[str, Any],
    reference_date: date,
    cycle_start: date,
    cycle_end: date
) -> List[date]:
    """Calculate monthly occurrences."""
    day_of_month = config["day_of_month"]
    handle_month_end = config.get("handle_month_end", False)
    occurrences = []

    # Start from first month that overlaps with cycle
    current_month = cycle_start.replace(day=1)

    while current_month <= cycle_end:
        try:
            occurrence_date = current_month.replace(day=day_of_month)
        except ValueError:
            # Handle months with fewer days
            if handle_month_end:
                # Use last day of month
                next_month = current_month + relativedelta(months=1)
                occurrence_date = next_month - timedelta(days=1)
            else:
                # Skip this month
                current_month += relativedelta(months=1)
                continue

        # Check if occurrence falls within cycle
        if cycle_start <= occurrence_date <= cycle_end:
            occurrences.append(occurrence_date)

        current_month += relativedelta(months=1)

    return occurrences

def calculate_custom_occurrences(
    config: Dict[str, Any],
    reference_date: date,
    cycle_start: date,
    cycle_end: date
) -> List[date]:
    """Calculate custom interval occurrences."""
    interval = config["interval"]
    unit = config["unit"]
    occurrences = []

    current_date = reference_date

    # Go backwards to find start point
    while current_date > cycle_start:
        if unit == "days":
            current_date -= timedelta(days=interval)
        elif unit == "weeks":
            current_date -= timedelta(weeks=interval)
        elif unit == "months":
            current_date -= relativedelta(months=interval)
        elif unit == "years":
            current_date -= relativedelta(years=interval)

    # Go forward to find all occurrences in cycle
    while current_date <= cycle_end:
        if cycle_start <= current_date <= cycle_end:
            occurrences.append(current_date)

        # Move to next occurrence
        if unit == "days":
            current_date += timedelta(days=interval)
        elif unit == "weeks":
            current_date += timedelta(weeks=interval)
        elif unit == "months":
            current_date += relativedelta(months=interval)
        elif unit == "years":
            current_date += relativedelta(years=interval)

    return occurrences
```

### Validation Schema

```python
from pydantic import BaseModel, validator
from typing import Optional, Literal

class WeeklyConfig(BaseModel):
    day_of_week: int

    @validator('day_of_week')
    def validate_day_of_week(cls, v):
        if not 0 <= v <= 6:
            raise ValueError('day_of_week must be between 0 and 6')
        return v

class BiWeeklyConfig(BaseModel):
    interval_days: int

    @validator('interval_days')
    def validate_interval_days(cls, v):
        if v <= 0:
            raise ValueError('interval_days must be positive')
        return v

class MonthlyConfig(BaseModel):
    day_of_month: int
    handle_month_end: Optional[bool] = False

    @validator('day_of_month')
    def validate_day_of_month(cls, v):
        if not 1 <= v <= 31:
            raise ValueError('day_of_month must be between 1 and 31')
        return v

class CustomConfig(BaseModel):
    interval: int
    unit: Literal["days", "weeks", "months", "years"]
    day_of_month: Optional[int] = None
    month_of_year: Optional[int] = None
    day_of_week: Optional[int] = None

    @validator('interval')
    def validate_interval(cls, v):
        if v <= 0:
            raise ValueError('interval must be positive')
        return v

    @validator('day_of_month')
    def validate_day_of_month(cls, v):
        if v is not None and not 1 <= v <= 31:
            raise ValueError('day_of_month must be between 1 and 31')
        return v

    @validator('month_of_year')
    def validate_month_of_year(cls, v):
        if v is not None and not 1 <= v <= 12:
            raise ValueError('month_of_year must be between 1 and 12')
        return v

    @validator('day_of_week')
    def validate_day_of_week(cls, v):
        if v is not None and not 0 <= v <= 6:
            raise ValueError('day_of_week must be between 0 and 6')
        return v
```

## Key Design Decisions

### 1. Multi-Currency Support
- Native currency storage on each expense
- Automatic USD conversion for reporting
- Historical exchange rate tracking

### 2. Soft Deletes
- `active` flags instead of hard deletes
- Preserves financial audit trails
- Maintains referential integrity

### 3. JSONB for Configuration
- Flexible recurrence pattern storage
- PostgreSQL's JSONB provides indexing and querying
- Schema evolution without migrations

### 4. Temporal Data
- Created/updated timestamps on all tables
- `paid_at` timestamp for expense tracking
- Date-based cycle management

### 5. Constraints and Validation
- Check constraints for positive amounts
- Unique constraints for business rules
- Foreign key cascades for data cleanup

## Sample Queries

### Generate Cycle Summary
```sql
SELECT
    c.name,
    c.income_amount,
    COUNT(ce.id) as total_expenses,
    SUM(ce.amount_usd) as total_amount_usd,
    SUM(CASE WHEN ce.category = 'fixed' THEN ce.amount_usd ELSE 0 END) as fixed_expenses,
    SUM(CASE WHEN ce.category = 'variable' THEN ce.amount_usd ELSE 0 END) as variable_expenses,
    c.income_amount - SUM(ce.amount_usd) as net_balance
FROM cycles c
LEFT JOIN cycle_expenses ce ON c.id = ce.cycle_id
WHERE c.user_id = $1 AND c.id = $2
GROUP BY c.id, c.name, c.income_amount;
```

### Payment Method Summary
```sql
SELECT
    pm.name,
    pm.method_type,
    COUNT(ce.id) as expense_count,
    SUM(ce.amount_usd) as total_amount,
    SUM(CASE WHEN ce.paid THEN ce.amount_usd ELSE 0 END) as paid_amount,
    SUM(CASE WHEN NOT ce.paid THEN ce.amount_usd ELSE 0 END) as pending_amount
FROM payment_methods pm
LEFT JOIN cycle_expenses ce ON pm.id = ce.payment_method_id
WHERE pm.user_id = $1 AND ce.cycle_id = $2
GROUP BY pm.id, pm.name, pm.method_type
ORDER BY total_amount DESC;
```

This schema provides the foundation for all the functional requirements while maintaining data integrity and supporting complex financial reporting.
