import { getAuthToken } from "@/actions/auth.action";
import {
  fetchCycles,
  createCycle,
  getCycleSummary,
  fetchCycleExpenses,
  createCycleExpense,
  updateCycleExpense,
  fetchCycleIncomes,
  createCycleIncome,
  updateCycleIncome,
  deleteCycleIncome,
} from "@/lib/cycles.api";
import type {
  CreateCycleRequest,
  CreateCycleExpenseRequest,
  UpdateCycleExpenseRequest,
  CreateCycleIncomeRequest,
  UpdateCycleIncomeRequest,
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
