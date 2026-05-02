import { apiClient } from "./api-client";
import type {
  ExchangeRate,
  CreateExchangeRateRequest,
  UpdateExchangeRateRequest,
} from "@/helpers/types";

export const fetchExchangeRates = (token: string) =>
  apiClient<ExchangeRate[]>("/exchange-rates/", { token });

export const createExchangeRate = (
  payload: CreateExchangeRateRequest,
  token: string,
) =>
  apiClient<ExchangeRate>("/exchange-rates/", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });

export const updateExchangeRate = (
  id: string,
  payload: UpdateExchangeRateRequest,
  token: string,
) =>
  apiClient<ExchangeRate>(`/exchange-rates/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    token,
  });
