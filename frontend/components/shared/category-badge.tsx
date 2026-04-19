import { Chip } from "@heroui/react";
import type { ExpenseCategory } from "@/helpers/types";

export function CategoryBadge({ category }: { category: ExpenseCategory }) {
  return (
    <Chip
      color={category === "fixed" ? "default" : "success"}
      size="sm"
      variant="soft"
    >
      {category}
    </Chip>
  );
}
