import { getAuthToken } from "@/actions/auth.action";
import {
  fetchExpenseTemplates,
  createExpenseTemplate,
  updateExpenseTemplate,
  deleteExpenseTemplate,
} from "@/lib/expense-templates.api";
import type {
  CreateExpenseTemplateRequest,
  UpdateExpenseTemplateRequest,
} from "@/helpers/types";

async function token() {
  return (await getAuthToken()) ?? "";
}

export const getExpenseTemplates = async () =>
  fetchExpenseTemplates(await token());

export const addExpenseTemplate = async (
  payload: CreateExpenseTemplateRequest,
) => createExpenseTemplate(payload, await token());

export const editExpenseTemplate = async (
  id: string,
  payload: UpdateExpenseTemplateRequest,
) => updateExpenseTemplate(id, payload, await token());

export const deactivateExpenseTemplate = async (id: string) =>
  deleteExpenseTemplate(id, await token());

export const activateExpenseTemplate = async (id: string) =>
  updateExpenseTemplate(id, { active: true }, await token());
