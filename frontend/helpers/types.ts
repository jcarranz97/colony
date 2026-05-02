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

// Recurrent Expenses
export interface RecurrentExpense {
  id: string;
  description: string;
  base_amount: string;
  currency: CurrencyCode;
  category: ExpenseCategory;
  recurrence_type: RecurrenceType;
  recurrence_config: RecurrenceConfig;
  reference_date: string;
  autopay_info: string | null;
  payment_method: { id: string; name: string; method_type: string } | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateRecurrentExpenseRequest {
  description: string;
  base_amount: string;
  currency: CurrencyCode;
  category: ExpenseCategory;
  recurrence_type: RecurrenceType;
  recurrence_config: RecurrenceConfig;
  reference_date?: string;
  autopay_info?: string | null;
  payment_method_id?: string | null;
}

export interface UpdateRecurrentExpenseRequest extends Partial<CreateRecurrentExpenseRequest> {
  active?: boolean;
}

// Cycles
export interface Cycle {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  status: CycleStatus;
  income_amount: string;
  remaining_balance: string;
  created_at: string;
  updated_at: string;
}

export interface CreateCycleRequest {
  name: string;
  start_date: string;
  end_date: string;
  income_amount: string;
  generate_from_templates?: boolean;
}

export interface UpdateCycleRequest {
  name?: string;
  income_amount?: string;
  status?: CycleStatus;
}

// Cycle Expenses
export interface CycleExpense {
  id: string;
  cycle_id: string;
  description: string;
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
  description: string;
  amount: string;
  currency: CurrencyCode;
  category: ExpenseCategory;
  due_date?: string | null;
  payment_method_id?: string | null;
}

export interface UpdateCycleExpenseRequest extends Partial<CreateCycleExpenseRequest> {
  status?: ExpenseStatus;
  paid?: boolean;
  paid_at?: string | null;
  comments?: string | null;
}

export interface CyclesListResponse {
  cycles: Cycle[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

export interface CycleExpensesResponse {
  expenses: CycleExpense[];
  summary: Record<string, unknown>;
}

// Cycle Summary
export interface StatusBreakdown {
  pending: number;
  paid: number;
  overdue: number;
  cancelled: number;
}

export interface CycleSummaryFinancial {
  total_expenses_usd: string;
  fixed_expenses_usd: string;
  variable_expenses_usd: string;
  usa_expenses_usd: string;
  mexico_expenses_usd: string;
  net_balance: string;
}

export interface CycleSummary {
  cycle: {
    id: string;
    name: string;
    start_date: string;
    end_date: string;
    income_amount: string;
  };
  financial: CycleSummaryFinancial;
  by_payment_method: unknown[];
  by_currency: Record<string, unknown>;
  status_breakdown: StatusBreakdown;
}

// Exchange rates
export interface ExchangeRate {
  id: string;
  from_currency: CurrencyCode;
  to_currency: CurrencyCode;
  rate: number;
  rate_date: string;
  created_at: string;
}

export interface CreateExchangeRateRequest {
  from_currency: CurrencyCode;
  to_currency: CurrencyCode;
  rate: number;
  rate_date: string;
}

export interface UpdateExchangeRateRequest {
  rate: number;
}

// API response wrapper
export type ApiResponse<T> =
  | { success: true; data: T }
  | { success: false; error: { code: string; message: string } };
