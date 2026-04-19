import { formatAmount } from "@/helpers/formatters";
import type { CurrencyCode } from "@/helpers/types";

export function AmountDisplay({
  amount,
  currency,
}: {
  amount: string | number;
  currency: CurrencyCode;
}) {
  return <span>{formatAmount(amount, currency)}</span>;
}
