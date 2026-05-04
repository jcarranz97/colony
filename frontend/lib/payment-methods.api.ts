import { apiClient } from "./api-client";
import type {
  PaymentMethod,
  CreatePaymentMethodRequest,
  UpdatePaymentMethodRequest,
} from "@/helpers/types";

export const fetchPaymentMethods = (token: string, includeInactive = false) =>
  apiClient<PaymentMethod[]>(
    includeInactive
      ? "/payment-methods/?include_inactive=true"
      : "/payment-methods/",
    { token },
  );

export const createPaymentMethod = (
  payload: CreatePaymentMethodRequest,
  token: string,
) =>
  apiClient<PaymentMethod>("/payment-methods/", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });

export const updatePaymentMethod = (
  id: string,
  payload: UpdatePaymentMethodRequest,
  token: string,
) =>
  apiClient<PaymentMethod>(`/payment-methods/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
    token,
  });

export const deletePaymentMethod = (id: string, token: string) =>
  apiClient<void>(`/payment-methods/${id}`, {
    method: "DELETE",
    token,
  });
