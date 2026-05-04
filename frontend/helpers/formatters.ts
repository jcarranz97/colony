import { format, parseISO, addDays } from "date-fns";
import type { CurrencyCode } from "./types";

export function formatPaymentMethodName(method: {
  name: string;
  last_4_digits?: string | null;
}): string {
  return method.last_4_digits
    ? `${method.name} (...${method.last_4_digits})`
    : method.name;
}

export function formatAmount(
  amount: string | number,
  currency: CurrencyCode,
): string {
  const num = typeof amount === "string" ? parseFloat(amount) : amount;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(num);
}

export function formatDate(dateStr: string): string {
  return format(parseISO(dateStr), "MMM d, yyyy");
}

export function formatDateShort(dateStr: string): string {
  return format(parseISO(dateStr), "MMM d");
}

export function computeCycleEndDate(startDate: string): string {
  return addDays(parseISO(startDate), 41).toISOString().split("T")[0];
}
