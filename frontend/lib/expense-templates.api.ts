import { apiClient } from "./api-client";
import type {
  ExpenseTemplate,
  CreateExpenseTemplateRequest,
  UpdateExpenseTemplateRequest,
} from "@/helpers/types";

export const fetchExpenseTemplates = (token: string) =>
  apiClient<ExpenseTemplate[]>("/expense-templates", { token });

export const createExpenseTemplate = (
  payload: CreateExpenseTemplateRequest,
  token: string,
) =>
  apiClient<ExpenseTemplate>("/expense-templates", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });

export const updateExpenseTemplate = (
  id: string,
  payload: UpdateExpenseTemplateRequest,
  token: string,
) =>
  apiClient<ExpenseTemplate>(`/expense-templates/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    token,
  });

export const deleteExpenseTemplate = (id: string, token: string) =>
  apiClient<void>(`/expense-templates/${id}`, {
    method: "DELETE",
    token,
  });
