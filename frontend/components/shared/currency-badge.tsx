import { Chip } from "@heroui/react";
import type { CurrencyCode } from "@/helpers/types";

export function CurrencyBadge({ currency }: { currency: CurrencyCode }) {
  return (
    <Chip
      color={currency === "USD" ? "accent" : "warning"}
      size="sm"
      variant="soft"
    >
      {currency}
    </Chip>
  );
}
