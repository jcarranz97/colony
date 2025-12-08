# Colony API Specification

!!! warning "**DOCUMENTATION STATUS**"
    This document is used for **initial architecture design and planning** of the Colony API endpoints. Once the FastAPI implementation begins, this documentation will be **deprecated** in favor of the auto-generated OpenAPI/Swagger documentation available at:

    - **Development**: `http://localhost:8000/docs` (Swagger UI)
    - **Development**: `http://localhost:8000/redoc` (ReDoc)
    - **Production**: `https://api.colony.app/docs`

    The purpose of this document is to:
    - Define the overall API structure and endpoints
    - Establish request/response schemas
    - Guide initial development priorities
    - Serve as a reference during the design phase

    **For current API documentation, always refer to the auto-generated FastAPI docs.**

This document defines the REST API endpoints for the Colony expense management application.

## API Overview

- **Base URL**: `https://api.colony.app/v1`
- **Authentication**: Bearer token (JWT)
- **Content-Type**: `application/json`
- **API Version**: v1

## Authentication

All endpoints require authentication except for user registration and login.

```http
Authorization: Bearer <jwt_token>
```

## Global Response Format

### Success Response
```json
{
  "success": true,
  "data": {
    // Response data here
  },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      // Additional error details
    }
  }
}
```

## API Endpoints

### 1. Authentication & Users

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "first_name": "John",
  "last_name": "Doe",
  "preferred_currency": "USD",
  "locale": "en-US"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "preferred_currency": "USD",
      "locale": "en-US",
      "active": true,
      "created_at": "2025-01-01T00:00:00Z"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  },
  "message": "User registered successfully"
}
```

#### POST /auth/login
Authenticate user and get access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  },
  "message": "Login successful"
}
```

#### GET /auth/me
Get current user information.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "preferred_currency": "USD",
      "locale": "en-US",
      "active": true,
      "created_at": "2025-01-01T00:00:00Z"
    }
  }
}
```

### 2. Payment Methods

#### GET /payment-methods
Get all user's payment methods.

**Query Parameters:**

- `active` (boolean, optional): Filter by active status
- `currency` (string, optional): Filter by default currency

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "payment_methods": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "name": "Chase Debit",
        "method_type": "debit",
        "default_currency": "USD",
        "description": "Primary checking account",
        "active": true,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
      }
    ],
    "total": 1
  }
}
```

#### POST /payment-methods
Create a new payment method.

**Request Body:**
```json
{
  "name": "Capital One Credit",
  "method_type": "credit",
  "default_currency": "USD",
  "description": "Rewards credit card"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "payment_method": {
      "id": "123e4567-e89b-12d3-a456-426614174002",
      "name": "Capital One Credit",
      "method_type": "credit",
      "default_currency": "USD",
      "description": "Rewards credit card",
      "active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  },
  "message": "Payment method created successfully"
}
```

#### PUT /payment-methods/{id}
Update an existing payment method.

**Request Body:**
```json
{
  "name": "Chase Debit Updated",
  "description": "Updated description",
  "active": true
}
```

**Response:** `200 OK`

#### DELETE /payment-methods/{id}
Deactivate a payment method (soft delete).

**Response:** `200 OK`

### 3. Expense Templates

#### GET /expense-templates
Get all user's expense templates.

**Query Parameters:**

- `active` (boolean, optional): Filter by active status
- `category` (string, optional): Filter by category (fixed/variable)
- `currency` (string, optional): Filter by currency

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "templates": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174003",
        "description": "Rent",
        "currency": "USD",
        "base_amount": "1200.00",
        "category": "fixed",
        "recurrence_type": "monthly",
        "recurrence_config": {
          "day_of_month": 1
        },
        "reference_date": "2024-12-01",
        "autopay_info": "Auto-pay enabled",
        "active": true,
        "payment_method": {
          "id": "123e4567-e89b-12d3-a456-426614174001",
          "name": "Chase Debit",
          "method_type": "debit"
        },
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
      }
    ],
    "total": 1
  }
}
```

#### POST /expense-templates
Create a new expense template.

**Request Body:**
```json
{
  "description": "Groceries",
  "currency": "USD",
  "payment_method_id": "123e4567-e89b-12d3-a456-426614174001",
  "base_amount": "150.00",
  "category": "variable",
  "recurrence_type": "weekly",
  "recurrence_config": {
    "day_of_week": 6
  },
  "reference_date": "2024-12-21",
  "autopay_info": null
}
```

**Response:** `201 Created`

#### PUT /expense-templates/{id}
Update an expense template.

#### DELETE /expense-templates/{id}
Delete an expense template.

### 4. Cycles

#### GET /cycles
Get all user's cycles.

**Query Parameters:**

- `status` (string, optional): Filter by status (draft/active/completed)
- `limit` (integer, optional): Number of results per page
- `offset` (integer, optional): Number of results to skip

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "cycles": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174004",
        "name": "January 2025 Cycle",
        "start_date": "2025-01-01",
        "end_date": "2025-02-11",
        "income_amount": "5000.00",
        "remaining_balance": "500.00",
        "status": "active",
        "summary": {
          "total_expenses": "4500.00",
          "fixed_expenses": "3000.00",
          "variable_expenses": "1500.00",
          "expense_count": 25,
          "paid_count": 10,
          "pending_count": 15
        },
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
      }
    ],
    "total": 1
  }
}
```

#### POST /cycles
Create a new cycle.

**Request Body:**
```json
{
  "name": "February 2025 Cycle",
  "start_date": "2025-02-12",
  "end_date": "2025-03-25",
  "income_amount": "5200.00",
  "remaining_balance": "0.00",
  "generate_from_templates": true
}
```

**Response:** `201 Created`

#### GET /cycles/{id}
Get a specific cycle with detailed information.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "cycle": {
      "id": "123e4567-e89b-12d3-a456-426614174004",
      "name": "January 2025 Cycle",
      "start_date": "2025-01-01",
      "end_date": "2025-02-11",
      "income_amount": "5000.00",
      "remaining_balance": "500.00",
      "status": "active",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  }
}
```

#### PUT /cycles/{id}
Update a cycle.

#### DELETE /cycles/{id}
Delete a cycle and all associated expenses.

### 5. Cycle Expenses

#### GET /cycles/{cycle_id}/expenses
Get all expenses for a specific cycle.

**Query Parameters:**

- `status` (string, optional): Filter by status (pending/paid/cancelled/overdue)
- `category` (string, optional): Filter by category (fixed/variable)
- `currency` (string, optional): Filter by currency
- `payment_method_id` (string, optional): Filter by payment method

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "expenses": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174005",
        "description": "Rent",
        "currency": "USD",
        "amount": "1200.00",
        "amount_usd": "1200.00",
        "due_date": "2025-01-01",
        "category": "fixed",
        "status": "paid",
        "paid": true,
        "paid_at": "2025-01-01T08:00:00Z",
        "comments": "Paid on time",
        "autopay_info": "Auto-pay enabled",
        "template_id": "123e4567-e89b-12d3-a456-426614174003",
        "payment_method": {
          "id": "123e4567-e89b-12d3-a456-426614174001",
          "name": "Chase Debit",
          "method_type": "debit"
        },
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T08:00:00Z"
      }
    ],
    "total": 1,
    "summary": {
      "total_amount_usd": "1200.00",
      "fixed_amount": "1200.00",
      "variable_amount": "0.00",
      "paid_amount": "1200.00",
      "pending_amount": "0.00"
    }
  }
}
```

#### POST /cycles/{cycle_id}/expenses
Add a manual expense to a cycle.

**Request Body:**
```json
{
  "description": "Emergency car repair",
  "currency": "USD",
  "payment_method_id": "123e4567-e89b-12d3-a456-426614174002",
  "amount": "350.00",
  "due_date": "2025-01-15",
  "category": "variable",
  "comments": "Unexpected expense"
}
```

**Response:** `201 Created`

#### PUT /cycles/{cycle_id}/expenses/{expense_id}
Update an expense.

**Request Body:**
```json
{
  "amount": "375.00",
  "paid": true,
  "paid_at": "2025-01-15T14:30:00Z",
  "comments": "Updated amount and marked as paid"
}
```

**Response:** `200 OK`

#### DELETE /cycles/{cycle_id}/expenses/{expense_id}
Delete an expense from a cycle.

### 6. Reports & Analytics

#### GET /cycles/{cycle_id}/summary
Get detailed cycle summary and analytics.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "summary": {
      "cycle": {
        "id": "123e4567-e89b-12d3-a456-426614174004",
        "name": "January 2025 Cycle",
        "start_date": "2025-01-01",
        "end_date": "2025-02-11",
        "income_amount": "5000.00"
      },
      "financial": {
        "total_expenses_usd": "4500.00",
        "fixed_expenses_usd": "3000.00",
        "variable_expenses_usd": "1500.00",
        "usa_expenses_usd": "3800.00",
        "mexico_expenses_usd": "700.00",
        "net_balance": "500.00"
      },
      "by_payment_method": [
        {
          "payment_method": {
            "id": "123e4567-e89b-12d3-a456-426614174001",
            "name": "Chase Debit"
          },
          "total_amount": "2500.00",
          "paid_amount": "1500.00",
          "pending_amount": "1000.00",
          "expense_count": 15
        }
      ],
      "by_currency": {
        "USD": {
          "total_amount": "3800.00",
          "expense_count": 20
        },
        "MXN": {
          "total_amount": "14000.00",
          "total_amount_usd": "700.00",
          "expense_count": 5
        }
      },
      "status_breakdown": {
        "pending": 15,
        "paid": 8,
        "overdue": 2,
        "cancelled": 0
      }
    }
  }
}
```

#### GET /reports/cycles-comparison
Compare multiple cycles.

**Query Parameters:**

- `cycle_ids` (array, required): Comma-separated cycle IDs
- `metrics` (array, optional): Specific metrics to compare

**Response:** `200 OK`

### 7. System Endpoints

#### GET /enums
Get all system enums for form validation.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "currency_codes": ["USD", "MXN"],
    "payment_method_types": ["debit", "credit", "cash", "transfer"],
    "expense_categories": ["fixed", "variable"],
    "recurrence_types": ["weekly", "bi_weekly", "monthly", "custom"],
    "cycle_statuses": ["draft", "active", "completed"],
    "expense_statuses": ["pending", "paid", "cancelled", "overdue"]
  }
}
```

#### GET /exchange-rates
Get current exchange rates.

**Query Parameters:**

- `from` (string, optional): Source currency
- `to` (string, optional): Target currency
- `date` (string, optional): Specific date (YYYY-MM-DD)

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "rates": [
      {
        "from_currency": "MXN",
        "to_currency": "USD",
        "rate": "0.050000",
        "rate_date": "2025-01-01"
      }
    ]
  }
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate name) |
| `CURRENCY_CONVERSION_ERROR` | 422 | Failed to convert currency |
| `CYCLE_GENERATION_ERROR` | 422 | Failed to generate cycle expenses |
| `INTERNAL_SERVER_ERROR` | 500 | Server error |

## Rate Limiting

- **Authenticated requests**: 1000 requests per hour
- **Authentication endpoints**: 10 requests per minute
- **Report generation**: 100 requests per hour

## Data Validation Rules

### Currency Amounts
- Must be positive decimal numbers
- Maximum 2 decimal places
- Maximum value: 999,999,999.99

### Dates
- Format: YYYY-MM-DD
- Cycle end_date must be after start_date
- Reference dates can be in the past

### Text Fields
- Description: 1-255 characters
- Name: 1-100 characters
- Comments: 0-1000 characters

## API Usage Examples

### Creating a Complete Expense Cycle

1. **Create Payment Methods** (if not exists)
2. **Create Expense Templates**
3. **Create Cycle** with automatic template generation
4. **Modify Generated Expenses** as needed
5. **Track Payment Status** throughout the cycle
6. **Generate Reports** for analysis

### Example Workflow

```javascript
// 1. Create payment method
const paymentMethod = await fetch('/api/payment-methods', {
  method: 'POST',
  body: JSON.stringify({
    name: 'Chase Debit',
    method_type: 'debit',
    default_currency: 'USD'
  })
});

// 2. Create expense template
const template = await fetch('/api/expense-templates', {
  method: 'POST',
  body: JSON.stringify({
    description: 'Rent',
    currency: 'USD',
    payment_method_id: paymentMethod.data.payment_method.id,
    base_amount: '1200.00',
    category: 'fixed',
    recurrence_type: 'monthly',
    recurrence_config: { day_of_month: 1 },
    reference_date: '2024-12-01'
  })
});

// 3. Create cycle
const cycle = await fetch('/api/cycles', {
  method: 'POST',
  body: JSON.stringify({
    name: 'February 2025 Cycle',
    start_date: '2025-02-01',
    end_date: '2025-03-14',
    income_amount: '5000.00',
    generate_from_templates: true
  })
});

// 4. Get cycle summary
const summary = await fetch(`/api/cycles/${cycle.data.cycle.id}/summary`);
```
