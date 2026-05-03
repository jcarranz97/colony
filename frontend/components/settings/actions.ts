import { getAuthToken } from "@/actions/auth.action";
import {
  fetchExchangeRates,
  createExchangeRate,
  updateExchangeRate,
} from "@/lib/exchange-rates.api";
import { getMyHouseholds, setActiveHousehold } from "@/lib/households.api";
import { getCurrentUser } from "@/lib/auth.api";
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

export const getCurrentUserAction = async () => getCurrentUser(await token());

export const getMyHouseholdsAction = async () => getMyHouseholds(await token());

export const setActiveHouseholdAction = async (householdId: string) =>
  setActiveHousehold(householdId, await token());
