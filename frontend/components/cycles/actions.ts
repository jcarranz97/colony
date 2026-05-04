import { getAuthToken } from "@/actions/auth.action";
import {
  fetchCycles,
  createCycle,
  updateCycle,
  deleteCycle,
  restoreCycle,
  getCycleSummary,
  fetchCycleExpenses,
  createCycleExpense,
  updateCycleExpense,
  fetchCycleIncomes,
  createCycleIncome,
  updateCycleIncome,
  deleteCycleIncome,
} from "@/lib/cycles.api";
import { getCurrentUser } from "@/lib/auth.api";
import type {
  CreateCycleRequest,
  UpdateCycleRequest,
  CreateCycleExpenseRequest,
  UpdateCycleExpenseRequest,
  CreateCycleIncomeRequest,
  UpdateCycleIncomeRequest,
} from "@/helpers/types";

async function token() {
  return (await getAuthToken()) ?? "";
}

export const getCycles = async (includeInactive = false) =>
  fetchCycles(await token(), includeInactive);

export const getCurrentUserAction = async () => getCurrentUser(await token());

export const addCycle = async (payload: CreateCycleRequest) =>
  createCycle(payload, await token());

export const editCycle = async (id: string, payload: UpdateCycleRequest) =>
  updateCycle(id, payload, await token());

export const removeCycle = async (id: string) => deleteCycle(id, await token());

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

export const getIncomes = async (cycleId: string) =>
  fetchCycleIncomes(cycleId, await token());

export const addIncome = async (
  cycleId: string,
  payload: CreateCycleIncomeRequest,
) => createCycleIncome(cycleId, payload, await token());

export const editIncome = async (
  cycleId: string,
  incomeId: string,
  payload: UpdateCycleIncomeRequest,
) => updateCycleIncome(cycleId, incomeId, payload, await token());

export const removeIncome = async (cycleId: string, incomeId: string) =>
  deleteCycleIncome(cycleId, incomeId, await token());

export const restoreCycleAction = async (id: string) =>
  restoreCycle(id, await token());
