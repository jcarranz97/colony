import { getAuthToken } from "@/actions/auth.action";
import {
  fetchRecurrentIncomes,
  createRecurrentIncome,
  updateRecurrentIncome,
  deleteRecurrentIncome,
} from "@/lib/recurrent-incomes.api";
import { getCurrentUser } from "@/lib/auth.api";
import type {
  CreateRecurrentIncomeRequest,
  UpdateRecurrentIncomeRequest,
} from "@/helpers/types";

async function token() {
  return (await getAuthToken()) ?? "";
}

export const getCurrentUserAction = async () => getCurrentUser(await token());

export const getRecurrentIncomes = async (includeInactive = false) =>
  fetchRecurrentIncomes(await token(), includeInactive);

export const addRecurrentIncome = async (
  payload: CreateRecurrentIncomeRequest,
) => createRecurrentIncome(payload, await token());

export const editRecurrentIncome = async (
  id: string,
  payload: UpdateRecurrentIncomeRequest,
) => updateRecurrentIncome(id, payload, await token());

export const deactivateRecurrentIncome = async (id: string) =>
  deleteRecurrentIncome(id, await token());

export const activateRecurrentIncome = async (id: string) =>
  updateRecurrentIncome(id, { active: true }, await token());
