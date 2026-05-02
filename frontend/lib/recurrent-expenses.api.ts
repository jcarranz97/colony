import { apiClient } from "./api-client";
import type {
  RecurrentExpense,
  CreateRecurrentExpenseRequest,
  UpdateRecurrentExpenseRequest,
} from "@/helpers/types";

export const fetchRecurrentExpenses = (token: string) =>
  apiClient<RecurrentExpense[]>("/recurrent-expenses", { token });

export const createRecurrentExpense = (
  payload: CreateRecurrentExpenseRequest,
  token: string,
) =>
  apiClient<RecurrentExpense>("/recurrent-expenses", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });

export const updateRecurrentExpense = (
  id: string,
  payload: UpdateRecurrentExpenseRequest,
  token: string,
) =>
  apiClient<RecurrentExpense>(`/recurrent-expenses/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    token,
  });

export const deleteRecurrentExpense = (id: string, token: string) =>
  apiClient<void>(`/recurrent-expenses/${id}`, {
    method: "DELETE",
    token,
  });
