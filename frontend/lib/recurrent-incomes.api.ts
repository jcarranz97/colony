import { apiClient } from "./api-client";
import type {
  RecurrentIncome,
  CreateRecurrentIncomeRequest,
  UpdateRecurrentIncomeRequest,
} from "@/helpers/types";

export const fetchRecurrentIncomes = (token: string, includeInactive = false) =>
  apiClient<RecurrentIncome[]>(
    includeInactive
      ? "/recurrent-incomes?include_inactive=true"
      : "/recurrent-incomes",
    { token },
  );

export const createRecurrentIncome = (
  payload: CreateRecurrentIncomeRequest,
  token: string,
) =>
  apiClient<RecurrentIncome>("/recurrent-incomes", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });

export const updateRecurrentIncome = (
  id: string,
  payload: UpdateRecurrentIncomeRequest,
  token: string,
) =>
  apiClient<RecurrentIncome>(`/recurrent-incomes/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    token,
  });

export const deleteRecurrentIncome = (id: string, token: string) =>
  apiClient<void>(`/recurrent-incomes/${id}`, {
    method: "DELETE",
    token,
  });
