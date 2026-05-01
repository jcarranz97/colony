import { getAuthToken } from "@/actions/auth.action";
import {
  fetchCycles,
  createCycle,
  getCycleSummary,
  fetchCycleExpenses,
  createCycleExpense,
  updateCycleExpense,
} from "@/lib/cycles.api";
import type {
  CreateCycleRequest,
  CreateCycleExpenseRequest,
  UpdateCycleExpenseRequest,
} from "@/helpers/types";

async function token() {
  return (await getAuthToken()) ?? "";
}

export const getCycles = async () => fetchCycles(await token());

export const addCycle = async (payload: CreateCycleRequest) =>
  createCycle(payload, await token());

export const fetchSummary = async (id: string) =>
  getCycleSummary(id, await token());

export const getExpenses = async (cycleId: string) =>
  fetchCycleExpenses(cycleId, await token());

export const addExpense = async (
  cycleId: string,
  payload: CreateCycleExpenseRequest,
) => createCycleExpense(cycleId, payload, await token());

export const editExpense = async (
  cycleId: string,
  expenseId: string,
  payload: UpdateCycleExpenseRequest,
) => updateCycleExpense(cycleId, expenseId, payload, await token());
