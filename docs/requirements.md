# Software Requirements Specification

## 1. Introduction

### 1.1 Purpose
This document specifies the functional and non-functional requirements for Colony, a personal expense management application designed to replace Excel-based expense tracking with automated cycle management.

### 1.2 Scope
Colony will provide users with the ability to:

- Track expenses across multiple currencies (USD, MXN)
- Manage recurring expenses with various patterns
- Create expense cycles (6-week periods)
- Automatically generate expenses for new cycles
- Categorize expenses (Fixed, Variable)
- Track payment methods and account balances
- Generate financial summaries and projections by location and type

### 1.3 Current Workflow
The system replaces a manual Excel-based process where users:

- Track expenses every 6 weeks (3 pay cycles of bi-weekly payments)
- Copy and modify recurring expenses for new periods
- Manage expenses in USD and MXN currencies
- Categorize expenses by type (Fixed/Variable) and implicitly by location via currency
- Generate payment summaries by account/card

## 2. Overall Description

### 2.1 Product Perspective
Colony is a standalone web application consisting of:

- A RESTful API backend (FastAPI) with multi-currency support
- A responsive web frontend (Next.js) with cycle management
- A containerized deployment solution

### 2.2 User Classes
- **Primary User**: Individual managing personal expenses across multiple currencies and accounts
- **Administrator**: System maintainer (for self-hosted instances)

## 3. Functional Requirements

### 3.1 User Authentication
- **FR-001**: Users must be able to create an account
- **FR-002**: Users must be able to log in securely
- **FR-003**: Users must be able to reset their password

### 3.2 Currency Management
- **FR-004**: System must support multiple currencies (USD, MXN)
- **FR-005**: System must track exchange rates for currency conversion
- **FR-006**: System must convert expenses to base currency (USD) for reporting

### 3.3 Payment Method Management
- **FR-007**: Users must be able to create custom payment methods with the following attributes:
    - Name (e.g., "Chase Debit", "Chase Credit", "Capital Credit", "Mexico Cash")
    - Type (Debit, Credit, Cash, Transfer)
    - Default currency (USD or MXN)
    - Active/Inactive status
- **FR-008**: Users must be able to edit existing payment methods
- **FR-009**: Users must be able to deactivate payment methods (soft delete to preserve historical data)
- **FR-010**: Users must be able to assign descriptive names to payment methods
- **FR-011**: Users must be able to specify payment method type (debit, credit, cash, transfer)
- **FR-012**: Users must be able to set a default currency for each payment method
- **FR-013**: System must prevent deletion of payment methods that are used in existing expenses
- **FR-014**: Users must be able to deactivate payment methods to hide them from new expense creation
- **FR-015**: System must provide default payment method templates for common use cases
- **FR-016**: System must validate that payment method and currency combinations are logical
- **FR-017**: Users must be able to view all payment methods (active and inactive)

### 3.4 Expense Template Management
- **FR-018**: Users must be able to create expense templates with the following fields:
    - Description
    - Currency (USD/MXN)
    - Payment Method
    - Amount
    - Category (Fixed/Variable)
    - Recurrence Pattern
    - Auto-pay details (optional)
    - Status
    - Comments
- **FR-019**: System must support recurrence patterns:
    - **Daily**: Specific day of month (1st, 7th, etc.)
    - **Weekly**: Specific day of week (every Saturday)
    - **Bi-weekly**: Every 14 days from start date
    - **Monthly**: Same date each month
    - **Custom**: User-defined intervals
- **FR-020**: Users must be able to edit expense templates
- **FR-021**: Users must be able to delete expense templates
- **FR-022**: Users must be able to view all expense templates
- **FR-023**: Each expense must specify currency and payment method

### 3.5 Cycle Management
- **FR-024**: Users must be able to create expense cycles (6-week periods)
- **FR-025**: System must automatically generate expenses for new cycles based on templates
- **FR-026**: Users must be able to modify generated expenses within a cycle
- **FR-027**: Users must be able to set "Remaining Balance" for each cycle
- **FR-028**: System must track cycle periods with start and end dates
- **FR-029**: Users must be able to view cycle history

### 3.6 Expense Management Within Cycles
- **FR-030**: Users must be able to manually add expenses to a cycle
- **FR-031**: Users must be able to edit cycle expenses
- **FR-032**: Users must be able to delete cycle expenses
- **FR-033**: Users must be able to mark expenses as paid/unpaid
- **FR-034**: System must calculate dates based on recurrence patterns and cycle start date

### 3.7 Expense Categorization
- **FR-035**: System must categorize expenses as:
    - **Fixed Expenses**
    - **Variable Expenses**
- **FR-036**: System must determine expense location based on currency:
    - **USD expenses** = USA-based expenses
    - **MXN expenses** = Mexico-based expenses
- **FR-037**: Users must be able to manually override expense categories
- **FR-038**: System must provide category rules based on payment method and description patterns

### 3.8 Financial Reporting and Analytics
- **FR-039**: System must generate cycle summaries showing:
    - Income for the period
    - Fixed expenses total
    - Variable expenses total
    - Mexico expenses total (MXN currency expenses converted to USD)
    - USA expenses total (USD currency expenses)
    - Net balance (Income - Total Expenses)
- **FR-040**: System must generate payment method summaries showing:
    - Amount needed per payment method
    - Amount paid per payment method
    - Amount pending per payment method
- **FR-041**: System must calculate projected balances:
    - "Before Paying"
    - "After Paying"
- **FR-042**: Users must be able to view multi-period summaries (combining multiple cycles)
- **FR-043**: System must support period-over-period comparisons
- **FR-044**: System must provide expense breakdowns by:
    - Category (Fixed vs Variable)
    - Location (USA vs Mexico based on currency)
    - Payment Method
    - Time period

### 3.9 Data Import/Export
- **FR-045**: Users must be able to import existing expense data from Excel/CSV
- **FR-046**: Users must be able to export cycle data to Excel/CSV
- **FR-047**: System must support bulk expense template creation

## 4. Non-Functional Requirements

### 4.1 Performance
- **NFR-001**: Cycle generation must complete within 5 seconds for 50+ expense templates
- **NFR-002**: Currency conversion must be real-time or cached for same-day accuracy
- **NFR-003**: Financial reports must generate within 3 seconds

### 4.2 Security
- **NFR-004**: All financial data must be encrypted at rest
- **NFR-005**: All API endpoints must be authenticated
- **NFR-006**: Passwords must be securely hashed
- **NFR-007**: Data transmission must be encrypted (HTTPS)

### 4.3 Usability
- **NFR-008**: Interface must be responsive across devices
- **NFR-009**: Currency amounts must display with proper formatting ($1,234.56)
- **NFR-010**: Date selection must be intuitive for cycle creation
- **NFR-011**: Bulk operations (cycle generation) must show progress indicators

### 4.4 Reliability
- **NFR-012**: System must handle currency conversion failures gracefully
- **NFR-013**: Data must be automatically backed up
- **NFR-014**: System must prevent duplicate expense generation in cycles

### 4.5 Internationalization
- **NFR-015**: Interface must support English and Spanish languages
- **NFR-016**: Currency formatting must respect locale (USD vs MXN display)
- **NFR-017**: Date formats must be configurable

## 5. Technical Constraints

- Must use FastAPI for backend API
- Must use Next.js for frontend
- Must be containerizable with Docker
- Must work in modern web browsers
- Must support SQLite for development and PostgreSQL for production
- Must integrate with currency exchange rate APIs

## 6. Data Requirements

### 6.1 Expense Template Schema
```
- id: UUID
- description: String (required)
- currency: Enum (USD, MXN)
- payment_method: String (required)
- base_amount: Decimal
- recurrence_type: Enum (daily, weekly, monthly, custom)
- recurrence_config: JSON (day_of_week, day_of_month, interval)
- autopay_info: String (optional)
- category: Enum (fixed, variable)
- active: Boolean
- created_at: DateTime
- updated_at: DateTime
- user_id: UUID (FK)
```

### 6.2 Cycle Schema
```
- id: UUID
- start_date: Date
- end_date: Date
- remaining_balance: Decimal
- income_amount: Decimal
- status: Enum (active, completed, draft)
- created_at: DateTime
- user_id: UUID (FK)
```

### 6.3 Cycle Expense Schema
```
- id: UUID
- cycle_id: UUID (FK)
- template_id: UUID (FK, optional)
- description: String
- currency: Enum (USD, MXN)
- payment_method: String
- amount: Decimal
- amount_usd: Decimal (calculated)
- date: Date
- autopay_info: String
- status: String
- comments: String
- category: Enum (fixed, variable)
- paid: Boolean
- created_at: DateTime
```

### 6.4 Payment Method Schema
```
- id: UUID
- name: String (user-defined, e.g., "Chase Debit", "Capital One Credit")
- type: Enum (debit, credit, cash, transfer)
- default_currency: Enum (USD, MXN)
- description: String (optional, for user notes)
- active: Boolean
- created_at: DateTime
- updated_at: DateTime
- user_id: UUID (FK)
```

## 7. Integration Requirements

### 7.1 Currency Exchange
- **IR-001**: System must integrate with currency exchange API (e.g., Exchange Rates API)
- **IR-002**: Exchange rates must be cached and updated daily
- **IR-003**: Historical exchange rates must be stored for accurate reporting

### 7.2 Future Integrations (Nice to Have)
- **IR-004**: Bank account integration for automatic expense importing
- **IR-005**: Mobile app notifications for upcoming expenses
- **IR-006**: Email reports for cycle summaries
