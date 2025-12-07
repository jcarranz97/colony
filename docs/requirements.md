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
- Categorize expenses (Fixed, Variable, Mexico-based)
- Track payment methods and account balances
- Generate financial summaries and projections

### 1.3 Current Workflow
The system replaces a manual Excel-based process where users:
- Track expenses every 6 weeks (3 pay cycles of bi-weekly payments)
- Copy and modify recurring expenses for new periods
- Manage expenses in USD and MXN currencies
- Categorize expenses by type and location
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

### 3.2 Currency and Payment Method Management
- **FR-004**: System must support multiple currencies (USD, MXN)
- **FR-005**: System must track exchange rates for currency conversion
- **FR-006**: Users must be able to define payment methods (Debito Chase, Credito Chase, Credito Capital, Mexico, etc.)
- **FR-007**: Each expense must specify currency and payment method
- **FR-008**: System must convert expenses to base currency (USD) for reporting

### 3.3 Expense Template Management
- **FR-009**: Users must be able to create expense templates with the following fields:
  - Concepto (Description)
  - Moneda (Currency: USD/MXN)
  - Metodo Pago (Payment Method)
  - Costo (Amount)
  - Recurrence Pattern
  - Autopay details (optional)
  - Estado (Status)
  - Comentarios (Comments)
- **FR-010**: System must support recurrence patterns:
  - **Daily**: Specific day of month (1st, 7th, etc.)
  - **Weekly**: Specific day of week (every Saturday)
  - **Bi-weekly**: Every 14 days from start date
  - **Monthly**: Same date each month
  - **Custom**: User-defined intervals
- **FR-011**: Users must be able to edit expense templates
- **FR-012**: Users must be able to delete expense templates
- **FR-013**: Users must be able to view all expense templates

### 3.4 Cycle Management
- **FR-014**: Users must be able to create expense cycles (6-week periods)
- **FR-015**: System must automatically generate expenses for new cycles based on templates
- **FR-016**: Users must be able to modify generated expenses within a cycle
- **FR-017**: Users must be able to set "Debito Restante" (remaining balance) for each cycle
- **FR-018**: System must track cycle periods with start and end dates
- **FR-019**: Users must be able to view cycle history

### 3.5 Expense Management Within Cycles
- **FR-020**: Users must be able to manually add expenses to a cycle
- **FR-021**: Users must be able to edit cycle expenses
- **FR-022**: Users must be able to delete cycle expenses
- **FR-023**: Users must be able to mark expenses as paid/unpaid
- **FR-024**: System must calculate dates based on recurrence patterns and cycle start date

### 3.6 Expense Categorization
- **FR-025**: System must automatically categorize expenses as:
  - **Gastos Fijos** (Fixed Expenses)
  - **Gastos Variables** (Variable Expenses)
  - **Gastos en Mexico** (Mexico Expenses)
- **FR-026**: Users must be able to manually override expense categories
- **FR-027**: System must provide category rules based on payment method and description patterns

### 3.7 Financial Reporting and Analytics
- **FR-028**: System must generate cycle summaries showing:
  - Income (Pago) for the period
  - Fixed expenses total
  - Variable expenses total
  - Mexico expenses total
  - Net balance (Income - Total Expenses)
- **FR-029**: System must generate payment method summaries showing:
  - Amount needed per payment method
  - Amount paid per payment method
  - Amount pending per payment method
- **FR-030**: System must calculate projected balances:
  - "Antes de Pagar" (Before Paying)
  - "Despues de Pagar" (After Paying)
- **FR-031**: Users must be able to view multi-period summaries (combining multiple cycles)
- **FR-032**: System must support period-over-period comparisons

### 3.8 Data Import/Export
- **FR-033**: Users must be able to import existing expense data from Excel/CSV
- **FR-034**: Users must be able to export cycle data to Excel/CSV
- **FR-035**: System must support bulk expense template creation

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
- concepto: String (required)
- moneda: Enum (USD, MXN)
- metodo_pago: String (required)
- costo_base: Decimal
- recurrence_type: Enum (daily, weekly, monthly, custom)
- recurrence_config: JSON (day_of_week, day_of_month, interval)
- autopay_info: String (optional)
- category: Enum (fijo, variable, mexico)
- active: Boolean
- created_at: DateTime
- updated_at: DateTime
```

### 6.2 Cycle Schema
```
- id: UUID
- start_date: Date
- end_date: Date
- debito_restante: Decimal
- income_amount: Decimal
- status: Enum (active, completed, draft)
- created_at: DateTime
```

### 6.3 Cycle Expense Schema
```
- id: UUID
- cycle_id: UUID (FK)
- template_id: UUID (FK, optional)
- concepto: String
- moneda: Enum (USD, MXN)
- metodo_pago: String
- costo: Decimal
- costo_usd: Decimal (calculated)
- fecha: Date
- autopay_info: String
- estado: String
- comentarios: String
- category: Enum (fijo, variable, mexico)
- paid: Boolean
- created_at: DateTime
```

### 6.4 Payment Method Schema
```
- id: UUID
- name: String (Debito Chase, Credito Chase, etc.)
- type: Enum (debit, credit, cash)
- currency: Enum (USD, MXN)
- active: Boolean
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
