import { apiClient } from "./api-client";
import type {
  Cycle,
  CyclesListResponse,
  CreateCycleRequest,
  UpdateCycleRequest,
  CycleSummary,
  CycleExpense,
  CycleExpensesResponse,
  CreateCycleExpenseRequest,
  UpdateCycleExpenseRequest,
  CycleIncome,
  CreateCycleIncomeRequest,
  UpdateCycleIncomeRequest,
} from "@/helpers/types";

export const fetchCycles = (token: string) =>
  apiClient<CyclesListResponse>("/cycles", { token });

export const createCycle = (payload: CreateCycleRequest, token: string) =>
  apiClient<Cycle>("/cycles", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });

export const updateCycle = (
  id: string,
  payload: UpdateCycleRequest,
  token: string,
) =>
  apiClient<Cycle>(`/cycles/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    token,
  });

export const deleteCycle = (id: string, token: string) =>
  apiClient<void>(`/cycles/${id}`, {
    method: "DELETE",
    token,
  });

export const getCycleSummary = (id: string, token: string) =>
  apiClient<CycleSummary>(`/cycles/${id}/summary`, { token });

export const fetchCycleExpenses = (
  cycleId: string,
  token: string,
  params?: Record<string, string>,
) => {
  const query = params ? "?" + new URLSearchParams(params).toString() : "";
  return apiClient<CycleExpensesResponse>(
    `/cycles/${cycleId}/expenses${query}`,
    { token },
  );
};

export const createCycleExpense = (
  cycleId: string,
  payload: CreateCycleExpenseRequest,
  token: string,
) =>
  apiClient<CycleExpense>(`/cycles/${cycleId}/expenses`, {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });

export const updateCycleExpense = (
  cycleId: string,
  expenseId: string,
  payload: UpdateCycleExpenseRequest,
  token: string,
) =>
  apiClient<CycleExpense>(`/cycles/${cycleId}/expenses/${expenseId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    token,
  });

export const deleteCycleExpense = (
  cycleId: string,
  expenseId: string,
  token: string,
) =>
  apiClient<void>(`/cycles/${cycleId}/expenses/${expenseId}`, {
    method: "DELETE",
    token,
  });

export const fetchCycleIncomes = (cycleId: string, token: string) =>
  apiClient<CycleIncome[]>(`/cycles/${cycleId}/incomes`, { token });

export const createCycleIncome = (
  cycleId: string,
  payload: CreateCycleIncomeRequest,
  token: string,
) =>
  apiClient<CycleIncome>(`/cycles/${cycleId}/incomes`, {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });

export const updateCycleIncome = (
  cycleId: string,
  incomeId: string,
  payload: UpdateCycleIncomeRequest,
  token: string,
) =>
  apiClient<CycleIncome>(`/cycles/${cycleId}/incomes/${incomeId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    token,
  });

export const deleteCycleIncome = (
  cycleId: string,
  incomeId: string,
  token: string,
) =>
  apiClient<void>(`/cycles/${cycleId}/incomes/${incomeId}`, {
    method: "DELETE",
    token,
  });
