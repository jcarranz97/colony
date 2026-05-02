import { getAuthToken } from "@/actions/auth.action";
import {
  fetchExchangeRates,
  createExchangeRate,
  updateExchangeRate,
} from "@/lib/exchange-rates.api";
import type {
  CreateExchangeRateRequest,
  UpdateExchangeRateRequest,
} from "@/helpers/types";

async function token() {
  return (await getAuthToken()) ?? "";
}

export const getExchangeRates = async () => fetchExchangeRates(await token());

export const addExchangeRate = async (payload: CreateExchangeRateRequest) =>
  createExchangeRate(payload, await token());

export const editExchangeRate = async (
  id: string,
  payload: UpdateExchangeRateRequest,
) => updateExchangeRate(id, payload, await token());
