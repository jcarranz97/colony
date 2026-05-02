import { getAuthToken } from "@/actions/auth.action";
import {
  fetchRecurrentIncomes,
  createRecurrentIncome,
  updateRecurrentIncome,
  deleteRecurrentIncome,
} from "@/lib/recurrent-incomes.api";
import type {
  CreateRecurrentIncomeRequest,
  UpdateRecurrentIncomeRequest,
} from "@/helpers/types";

async function token() {
  return (await getAuthToken()) ?? "";
}

export const getRecurrentIncomes = async () =>
  fetchRecurrentIncomes(await token());

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
