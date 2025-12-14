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

## Response Format

### Success Responses
API endpoints return data directly without wrapper objects. HTTP status codes indicate success or failure.

### Error Responses
All errors follow a consistent format:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      // Additional error details if applicable
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
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "preferred_currency": "USD",
  "locale": "en-US",
  "active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

#### POST /auth/login
Authenticate user and get access token.

**Request Body (Form Data):**
```
username=user@example.com
password=securePassword123
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### GET /auth/me
Get current user information.

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "preferred_currency": "USD",
  "locale": "en-US",
  "active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

#### PUT /auth/me
Update current user information.

**Request Body:**
```json
{
  "first_name": "John Updated",
  "last_name": "Doe Updated",
  "preferred_currency": "MXN",
  "locale": "es-MX"
}
```

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "first_name": "John Updated",
  "last_name": "Doe Updated",
  "preferred_currency": "MXN",
  "locale": "es-MX",
  "active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T12:30:00Z"
}
```

#### PUT /auth/me/password
Update current user password.

**Request Body:**
```json
{
  "current_password": "oldPassword123",
  "new_password": "newSecurePassword456"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password updated successfully"
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
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Chase Debit",
    "method_type": "debit",
    "default_currency": "USD",
    "description": "Primary checking account",
    "active": true,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  },
  {
    "id": "123e4567-e89b-12d3-a456-426614174002",
    "name": "Capital One Credit",
    "method_type": "credit",
    "default_currency": "USD",
    "description": "Rewards credit card",
    "active": true,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
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
  "id": "123e4567-e89b-12d3-a456-426614174002",
  "name": "Capital One Credit",
  "method_type": "credit",
  "default_currency": "USD",
  "description": "Rewards credit card",
  "active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

#### GET /payment-methods/{id}
Get a specific payment method.

**Response:** `200 OK`
```json
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
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001",
  "name": "Chase Debit Updated",
  "method_type": "debit",
  "default_currency": "USD",
  "description": "Updated description",
  "active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T12:30:00Z"
}
```

#### DELETE /payment-methods/{id}
Deactivate a payment method (soft delete).

**Response:** `204 No Content`

### 3. Expense Templates

#### GET /expense-templates
Get all user's expense templates.

**Query Parameters:**
- `active` (boolean, optional): Filter by active status
- `category` (string, optional): Filter by category (fixed/variable)
- `currency` (string, optional): Filter by currency

**Response:** `200 OK`
```json
[
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
]
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
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174004",
  "description": "Groceries",
  "currency": "USD",
  "base_amount": "150.00",
  "category": "variable",
  "recurrence_type": "weekly",
  "recurrence_config": {
    "day_of_week": 6
  },
  "reference_date": "2024-12-21",
  "autopay_info": null,
  "active": true,
  "payment_method": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Chase Debit",
    "method_type": "debit"
  },
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

#### GET /expense-templates/{id}
Get a specific expense template.

#### PUT /expense-templates/{id}
Update an expense template.

#### DELETE /expense-templates/{id}
Delete an expense template.

**Response:** `204 No Content`

### 4. Cycles

#### GET /cycles
Get all user's cycles with pagination.

**Query Parameters:**
- `status` (string, optional): Filter by status (draft/active/completed)
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Items per page (default: 20, max: 100)

**Response:** `200 OK`
```json
{
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
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 1,
    "pages": 1
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
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174005",
  "name": "February 2025 Cycle",
  "start_date": "2025-02-12",
  "end_date": "2025-03-25",
  "income_amount": "5200.00",
  "remaining_balance": "5200.00",
  "status": "draft",
  "summary": {
    "total_expenses": "0.00",
    "fixed_expenses": "0.00",
    "variable_expenses": "0.00",
    "expense_count": 0,
    "paid_count": 0,
    "pending_count": 0
  },
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

#### GET /cycles/{id}
Get a specific cycle with detailed information.

**Response:** `200 OK`
```json
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
```

#### PUT /cycles/{id}
Update a cycle.

**Request Body:**
```json
{
  "name": "January 2025 Cycle Updated",
  "income_amount": "5500.00",
  "status": "active"
}
```

**Response:** `200 OK`

#### DELETE /cycles/{id}
Delete a cycle and all associated expenses.

**Response:** `204 No Content`

### 5. Cycle Expenses

#### GET /cycles/{cycle_id}/expenses
Get all expenses for a specific cycle.

**Query Parameters:**
- `status` (string, optional): Filter by status (pending/paid/cancelled/overdue)
- `category` (string, optional): Filter by category (fixed/variable)
- `currency` (string, optional): Filter by currency
- `payment_method_id` (string, optional): Filter by payment method
- `comment_search` (string, optional): Search within comment text
- `include_comments` (boolean, optional): Include current comment with each expense (default: false)

**Response:** `200 OK`
```json
{
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
      "current_comment": {
        "text": "Rent increased by $100 due to annual lease adjustment",
        "created_at": "2025-01-01T07:30:00Z"
      },
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
  "summary": {
    "total_amount_usd": "1200.00",
    "fixed_amount": "1200.00",
    "variable_amount": "0.00",
    "paid_amount": "1200.00",
    "pending_amount": "0.00",
    "total_count": 1
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
  "initial_comment": "Unexpected car repair - transmission issue"
}
```

**Response:** `201 Created`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174006",
  "description": "Emergency car repair",
  "currency": "USD",
  "amount": "350.00",
  "amount_usd": "350.00",
  "due_date": "2025-01-15",
  "category": "variable",
  "status": "pending",
  "paid": false,
  "paid_at": null,
  "current_comment": {
    "text": "Unexpected car repair - transmission issue",
    "created_at": "2025-01-01T00:00:00Z"
  },
  "autopay_info": null,
  "template_id": null,
  "payment_method": {
    "id": "123e4567-e89b-12d3-a456-426614174002",
    "name": "Capital One Credit",
    "method_type": "credit"
  },
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

#### GET /cycles/{cycle_id}/expenses/{expense_id}
Get a specific expense with comment history.

**Query Parameters:**
- `include_comment_history` (boolean, optional): Include full comment history (default: true)

**Response:** `200 OK`
```json
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
  "current_comment": {
    "text": "Rent increased by $100 due to annual lease adjustment",
    "created_at": "2025-01-01T07:30:00Z"
  },
  "comment_history": [
    {
      "id": "comment-uuid-2",
      "text": "Rent increased by $100 due to annual lease adjustment",
      "created_at": "2025-01-01T07:30:00Z"
    },
    {
      "id": "comment-uuid-1",
      "text": "Standard rent payment",
      "created_at": "2024-12-15T10:00:00Z"
    }
  ],
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
```

#### PUT /cycles/{cycle_id}/expenses/{expense_id}
Update an expense. If you want to add a comment along with the update, use the comments endpoint separately or include `update_comment`.

**Request Body:**
```json
{
  "amount": "1300.00",
  "paid": true,
  "paid_at": "2025-01-01T14:30:00Z",
  "update_comment": "Amount increased for January due to utility cost adjustment"
}
```

**Response:** `200 OK`
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174005",
  "description": "Rent",
  "currency": "USD",
  "amount": "1300.00",
  "amount_usd": "1300.00",
  "due_date": "2025-01-01",
  "category": "fixed",
  "status": "paid",
  "paid": true,
  "paid_at": "2025-01-01T14:30:00Z",
  "current_comment": {
    "text": "Amount increased for January due to utility cost adjustment",
    "created_at": "2025-01-01T14:30:00Z"
  },
  "autopay_info": "Auto-pay enabled",
  "template_id": "123e4567-e89b-12d3-a456-426614174003",
  "payment_method": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Chase Debit",
    "method_type": "debit"
  },
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T14:30:00Z"
}
```

#### DELETE /cycles/{cycle_id}/expenses/{expense_id}
Delete an expense from a cycle.

**Response:** `204 No Content`

### 6. Expense Comments

#### POST /cycles/{cycle_id}/expenses/{expense_id}/comments
Add a comment to an expense.

**Request Body:**
```json
{
  "text": "This expense won't apply in March - vacation month"
}
```

**Response:** `201 Created`
```json
{
  "id": "comment-uuid-3",
  "text": "This expense won't apply in March - vacation month",
  "created_at": "2025-01-20T14:45:00Z"
}
```

#### GET /cycles/{cycle_id}/expenses/{expense_id}/comments
Get all comments for an expense.

**Query Parameters:**
- `limit` (integer, optional): Maximum number of comments to return (default: 50)
- `offset` (integer, optional): Number of comments to skip (default: 0)

**Response:** `200 OK`
```json
{
  "comments": [
    {
      "id": "comment-uuid-3",
      "text": "This expense won't apply in March - vacation month",
      "created_at": "2025-01-20T14:45:00Z"
    },
    {
      "id": "comment-uuid-2",
      "text": "Amount increased for January due to utility cost adjustment",
      "created_at": "2025-01-15T10:30:00Z"
    },
    {
      "id": "comment-uuid-1",
      "text": "Standard rent payment",
      "created_at": "2024-12-15T10:00:00Z"
    }
  ],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 3,
    "has_more": false
  }
}
```

#### PUT /cycles/{cycle_id}/expenses/{expense_id}/comments/{comment_id}
Update a specific comment.

**Request Body:**
```json
{
  "text": "This expense won't apply in March - vacation month (updated)"
}
```

**Response:** `200 OK`
```json
{
  "id": "comment-uuid-3",
  "text": "This expense won't apply in March - vacation month (updated)",
  "created_at": "2025-01-20T14:45:00Z"
}
```

#### DELETE /cycles/{cycle_id}/expenses/{expense_id}/comments/{comment_id}
Delete a specific comment.

**Response:** `204 No Content`

### 7. Reports & Analytics

#### GET /cycles/{cycle_id}/summary
Get detailed cycle summary and analytics.

**Response:** `200 OK`
```json
{
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
  },
  "comment_insights": {
    "total_comments": 42,
    "expenses_with_comments": 18,
    "recent_comment_activity": 7
  }
}
```

#### GET /cycles/{cycle_id}/expenses/search
Advanced expense search within a cycle.

**Query Parameters:**
- `q` (string, optional): General search query (searches description and comments)
- `comment_search` (string, optional): Search specifically within comment text
- `status` (string, optional): Filter by status
- `category` (string, optional): Filter by category
- `amount_min` (decimal, optional): Minimum amount filter
- `amount_max` (decimal, optional): Maximum amount filter
- `due_date_from` (date, optional): Due date range start
- `due_date_to` (date, optional): Due date range end
- `payment_method_id` (string, optional): Filter by payment method
- `has_comments` (boolean, optional): Filter expenses with/without comments

**Response:** `200 OK`
```json
{
  "expenses": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174005",
      "description": "Rent",
      "amount": "1200.00",
      "due_date": "2025-01-01",
      "status": "paid",
      "current_comment": {
        "text": "Rent increased by $100 due to annual lease adjustment",
        "created_at": "2025-01-01T07:30:00Z"
      },
      "comment_match": "annual lease adjustment"
    }
  ],
  "summary": {
    "total_found": 1,
    "total_amount": "1200.00"
  }
}
```

#### GET /reports/cycles-comparison
Compare multiple cycles.

**Query Parameters:**
- `cycle_ids` (array, required): Comma-separated cycle IDs
- `metrics` (array, optional): Specific metrics to compare

**Response:** `200 OK`
```json
{
  "cycles": [
    {
      "cycle": {
        "id": "123e4567-e89b-12d3-a456-426614174004",
        "name": "January 2025 Cycle"
      },
      "metrics": {
        "total_expenses": "4500.00",
        "fixed_expenses": "3000.00",
        "variable_expenses": "1500.00",
        "comment_activity": 42
      }
    }
  ],
  "comparison": {
    "average_total": "4500.00",
    "trends": {
      "expenses": "stable",
      "comment_activity": "increasing"
    }
  }
}
```

### 8. System Endpoints

#### GET /enums
Get all system enums for form validation.

**Response:** `200 OK`
```json
{
  "currency_codes": ["USD", "MXN"],
  "payment_method_types": ["debit", "credit", "cash", "transfer"],
  "expense_categories": ["fixed", "variable"],
  "recurrence_types": ["weekly", "bi_weekly", "monthly", "custom"],
  "cycle_statuses": ["draft", "active", "completed"],
  "expense_statuses": ["pending", "paid", "cancelled", "overdue"]
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
  "rates": [
    {
      "from_currency": "MXN",
      "to_currency": "USD",
      "rate": "0.050000",
      "rate_date": "2025-01-01"
    }
  ]
}
```

#### GET /health
System health check.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "colony-api",
  "version": "1.0.0",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

## Comments System

The comments system uses a dedicated table for full history tracking without any legacy JSONB fields.

### Comment Features

#### Comment Structure
- **Text-only**: Simple text comments (1-2000 characters)
- **Full history**: Complete audit trail in dedicated table
- **Chronological order**: Comments ordered by creation timestamp
- **Full-text search**: PostgreSQL advanced text search

#### Current Comment Display
The API shows the "current comment" by returning the most recent comment for each expense when requested:

```json
{
  "current_comment": {
    "text": "Most recent comment text",
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

### Comment API Features

#### Adding Comments
- **During expense creation**: Use `initial_comment` field
- **During expense updates**: Use `update_comment` field (adds new comment)
- **Standalone comments**: Use dedicated comments endpoint

#### Comment Search
- **Full-text search**: Search within comment text across all expenses
- **Contextual search**: Find expenses based on comment content
- **Date-based filtering**: Find comments within time periods

#### Comment Analytics
- **Comment insights**: Track comment activity per cycle
- **Activity indicators**: Identify expenses with high comment activity
- **Search highlighting**: Show matching text in search results

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `USER_NOT_FOUND` | 404 | User not found |
| `USER_ALREADY_EXISTS` | 409 | User already exists |
| `INVALID_CREDENTIALS` | 401 | Invalid email or password |
| `INVALID_TOKEN` | 401 | Invalid or expired token |
| `INACTIVE_USER` | 403 | User account is inactive |
| `INCORRECT_PASSWORD` | 400 | Current password is incorrect |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource not found |
| `RESOURCE_CONFLICT` | 409 | Resource conflict (e.g., duplicate name) |
| `COMMENT_NOT_FOUND` | 404 | Comment not found |
| `COMMENT_TOO_LONG` | 400 | Comment exceeds maximum length (2000 characters) |
| `CURRENCY_CONVERSION_ERROR` | 422 | Failed to convert currency |
| `CYCLE_GENERATION_ERROR` | 422 | Failed to generate cycle expenses |
| `INTERNAL_SERVER_ERROR` | 500 | Server error |

## HTTP Status Codes

- `200 OK` - Successful GET, PUT requests
- `201 Created` - Successful POST requests (resource created)
- `204 No Content` - Successful DELETE requests
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required or invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict
- `422 Unprocessable Entity` - Validation error or business logic error
- `500 Internal Server Error` - Server error

## Rate Limiting

- **Authenticated requests**: 1000 requests per hour
- **Authentication endpoints**: 10 requests per minute
- **Report generation**: 100 requests per hour
- **Comment endpoints**: 200 requests per hour

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
- Comments: 1-2000 characters

### Comments
- **Text**: 1-2000 characters, required
- **Search queries**: Maximum 100 characters
- **Comment history**: Preserved indefinitely

## API Usage Examples

### Working with Comments

#### Adding Comments During Expense Creation
```javascript
// Create expense with initial comment
const expense = await fetch(`/api/v1/cycles/${cycleId}/expenses`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
  },
  body: JSON.stringify({
    description: 'Car insurance',
    amount: '150.00',
    due_date: '2025-01-15',
    category: 'fixed',
    payment_method_id: paymentMethodId,
    initial_comment: 'Rate increased due to coverage upgrade'
  })
});
```

#### Adding Comments During Expense Updates
```javascript
// Update expense and add comment
const response = await fetch(`/api/v1/cycles/${cycleId}/expenses/${expenseId}`, {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
  },
  body: JSON.stringify({
    amount: '1350.00',
    paid: true,
    update_comment: 'Amount increased due to inflation adjustment'
  })
});
```

#### Adding Standalone Comments
```javascript
// Add a comment without changing the expense
const commentResponse = await fetch(`/api/v1/cycles/${cycleId}/expenses/${expenseId}/comments`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
  },
  body: JSON.stringify({
    text: 'This expense might be delayed due to banking issues'
  })
});
```

#### Searching Expenses by Comments
```javascript
// Search for expenses with specific comment content
const searchResponse = await fetch(
  `/api/v1/cycles/${cycleId}/expenses?comment_search=inflation&include_comments=true`,
  {
    headers: {
      'Authorization': 'Bearer ' + token
    }
  }
);
```

#### Advanced Expense Search
```javascript
// Advanced search with multiple criteria
const advancedSearchResponse = await fetch(
  `/api/v1/cycles/${cycleId}/expenses/search?` + new URLSearchParams({
    comment_search: 'increase adjustment',
    amount_min: '100.00',
    has_comments: 'true',
    status: 'pending'
  }),
  {
    headers: {
      'Authorization': 'Bearer ' + token
    }
  }
);
```

### Complete Workflow Example

```javascript
// 1. Create cycle
const cycle = await fetch(`/api/v1/cycles`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
  },
  body: JSON.stringify({
    name: 'February 2025 Cycle',
    start_date: '2025-02-01',
    end_date: '2025-03-14',
    income_amount: '5000.00'
  })
});

// 2. Add expense with initial comment
const expense = await fetch(`/api/v1/cycles/${cycle.id}/expenses`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
  },
  body: JSON.stringify({
    description: 'Car insurance',
    amount: '150.00',
    due_date: '2025-02-15',
    category: 'fixed',
    payment_method_id: paymentMethodId,
    initial_comment: 'Rate increased by $25 due to coverage upgrade'
  })
});

// 3. Add additional comment
await fetch(`/api/v1/cycles/${cycle.id}/expenses/${expense.id}/comments`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
  },
  body: JSON.stringify({
    text: 'Payment scheduled for auto-pay on the 15th'
  })
});

// 4. Mark as paid with update comment
await fetch(`/api/v1/cycles/${cycle.id}/expenses/${expense.id}`, {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
  },
  body: JSON.stringify({
    paid: true,
    paid_at: new Date().toISOString(),
    update_comment: 'Payment processed successfully via auto-pay'
  })
});

// 5. Search for expenses with rate changes
const rateChangeExpenses = await fetch(
  `/api/v1/cycles/${cycle.id}/expenses/search?comment_search=rate increased`,
  {
    headers: { 'Authorization': 'Bearer ' + token }
  }
);

// 6. Get full comment history for an expense
const expenseDetails = await fetch(
  `/api/v1/cycles/${cycle.id}/expenses/${expense.id}?include_comment_history=true`,
  {
    headers: { 'Authorization': 'Bearer ' + token }
  }
);
```
