import { getAuthToken } from "@/actions/auth.action";
import {
  fetchPaymentMethods,
  createPaymentMethod,
  updatePaymentMethod,
  deletePaymentMethod,
} from "@/lib/payment-methods.api";
import type {
  CreatePaymentMethodRequest,
  UpdatePaymentMethodRequest,
} from "@/helpers/types";

async function token() {
  return (await getAuthToken()) ?? "";
}

export const getPaymentMethods = async () => fetchPaymentMethods(await token());

export const addPaymentMethod = async (payload: CreatePaymentMethodRequest) =>
  createPaymentMethod(payload, await token());

export const editPaymentMethod = async (
  id: string,
  payload: UpdatePaymentMethodRequest,
) => updatePaymentMethod(id, payload, await token());

export const deactivatePaymentMethod = async (id: string) =>
  deletePaymentMethod(id, await token());

export const activatePaymentMethod = async (id: string) =>
  updatePaymentMethod(id, { active: true }, await token());
