// Enums
export type CurrencyCode = "USD" | "MXN";
export type PaymentMethodType = "debit" | "credit" | "cash" | "transfer";
export type ExpenseCategory = "fixed" | "variable";
export type RecurrenceType = "weekly" | "bi_weekly" | "monthly" | "custom";
export type CycleStatus = "draft" | "active" | "completed";
export type ExpenseStatus = "pending" | "paid" | "overdue" | "cancelled";

// Auth
export interface Token {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  preferred_currency: CurrencyCode;
  locale: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UpdateUserRequest {
  first_name?: string;
  last_name?: string;
  preferred_currency?: CurrencyCode;
}

export interface UpdatePasswordRequest {
  current_password: string;
  new_password: string;
}

// Payment Methods
export interface PaymentMethod {
  id: string;
  name: string;
  method_type: PaymentMethodType;
  default_currency: CurrencyCode;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreatePaymentMethodRequest {
  name: string;
  method_type: PaymentMethodType;
  default_currency: CurrencyCode;
}

export interface UpdatePaymentMethodRequest {
  name?: string;
  method_type?: PaymentMethodType;
  default_currency?: CurrencyCode;
  active?: boolean;
}

// Recurrence Config
export type RecurrenceConfig =
  | { day_of_week: number }
  | { interval_days: number }
  | { day_of_month: number; handle_month_end?: boolean }
  | {
      interval: number;
      unit: "days" | "weeks" | "months";
      day_of_month?: number;
    }
  | Record<string, never>;

// Expense Templates
export interface ExpenseTemplate {
  id: string;
  name: string;
  amount: string;
  currency: CurrencyCode;
  category: ExpenseCategory;
  recurrence_type: RecurrenceType;
  recurrence_config: RecurrenceConfig;
  payment_method_id: string | null;
  payment_method?: PaymentMethod;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateExpenseTemplateRequest {
  name: string;
  amount: string;
  currency: CurrencyCode;
  category: ExpenseCategory;
  recurrence_type: RecurrenceType;
  recurrence_config: RecurrenceConfig;
  payment_method_id?: string | null;
}

export interface UpdateExpenseTemplateRequest extends Partial<CreateExpenseTemplateRequest> {}

// Cycles
export interface Cycle {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  status: CycleStatus;
  income: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateCycleRequest {
  name: string;
  start_date: string;
  end_date: string;
  income?: string;
  generate_from_templates?: boolean;
}

export interface UpdateCycleRequest {
  name?: string;
  income?: string;
  status?: CycleStatus;
}

// Cycle Expenses
export interface CycleExpense {
  id: string;
  cycle_id: string;
  name: string;
  amount: string;
  currency: CurrencyCode;
  category: ExpenseCategory;
  status: ExpenseStatus;
  due_date: string | null;
  paid_at: string | null;
  payment_method_id: string | null;
  payment_method?: PaymentMethod;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateCycleExpenseRequest {
  name: string;
  amount: string;
  currency: CurrencyCode;
  category: ExpenseCategory;
  due_date?: string | null;
  payment_method_id?: string | null;
}

export interface UpdateCycleExpenseRequest extends Partial<CreateCycleExpenseRequest> {
  status?: ExpenseStatus;
}

export interface CycleExpensesResponse {
  items: CycleExpense[];
  total: number;
  page: number;
  size: number;
}

// Cycle Summary
export interface PaymentMethodSummary {
  payment_method_id: string;
  payment_method_name: string;
  total: string;
  paid: string;
  pending: string;
  count: number;
}

export interface StatusBreakdown {
  pending: number;
  paid: number;
  overdue: number;
  cancelled: number;
}

export interface CycleSummary {
  cycle_id: string;
  income: string;
  total_expenses: string;
  net_balance: string;
  fixed_expenses: string;
  variable_expenses: string;
  usa_expenses_usd: string;
  mexico_expenses_mxn: string;
  by_payment_method: PaymentMethodSummary[];
  status_breakdown: StatusBreakdown;
}

// API response wrapper
export type ApiResponse<T> =
  | { success: true; data: T }
  | { success: false; error: { code: string; message: string } };
