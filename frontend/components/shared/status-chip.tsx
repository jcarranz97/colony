import { Chip } from "@heroui/react";
import type { CycleStatus, ExpenseStatus } from "@/helpers/types";

type Status = CycleStatus | ExpenseStatus;

type ChipColor = "accent" | "danger" | "default" | "success" | "warning";

const STATUS_COLOR: Record<Status, ChipColor> = {
  draft: "default",
  active: "accent",
  completed: "success",
  pending: "warning",
  paid: "success",
  overdue: "danger",
  cancelled: "default",
  paid_other: "accent",
  skipped: "default",
};

export function StatusChip({ status }: { status: Status }) {
  return (
    <Chip color={STATUS_COLOR[status]} size="sm" variant="soft">
      {status}
    </Chip>
  );
}
