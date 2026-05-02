import { getAuthToken } from "@/actions/auth.action";
import {
  fetchRecurrentExpenses,
  createRecurrentExpense,
  updateRecurrentExpense,
  deleteRecurrentExpense,
} from "@/lib/recurrent-expenses.api";
import type {
  CreateRecurrentExpenseRequest,
  UpdateRecurrentExpenseRequest,
} from "@/helpers/types";

async function token() {
  return (await getAuthToken()) ?? "";
}

export const getRecurrentExpenses = async () =>
  fetchRecurrentExpenses(await token());

export const addRecurrentExpense = async (
  payload: CreateRecurrentExpenseRequest,
) => createRecurrentExpense(payload, await token());

export const editRecurrentExpense = async (
  id: string,
  payload: UpdateRecurrentExpenseRequest,
) => updateRecurrentExpense(id, payload, await token());

export const deactivateRecurrentExpense = async (id: string) =>
  deleteRecurrentExpense(id, await token());

export const activateRecurrentExpense = async (id: string) =>
  updateRecurrentExpense(id, { active: true }, await token());
