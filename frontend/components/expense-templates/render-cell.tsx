import { Button, Chip } from "@heroui/react";
import { AmountDisplay } from "@/components/shared/amount-display";
import { CategoryBadge } from "@/components/shared/category-badge";
import { CurrencyBadge } from "@/components/shared/currency-badge";
import type {
  ExpenseTemplate,
  RecurrenceConfig,
  RecurrenceType,
} from "@/helpers/types";

const DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function formatRecurrence(
  type: RecurrenceType,
  config: RecurrenceConfig,
): string {
  switch (type) {
    case "weekly": {
      const cfg = config as { day_of_week: number };
      return `Weekly on ${DAY_NAMES[cfg.day_of_week] ?? "?"}`;
    }
    case "bi_weekly": {
      const cfg = config as { interval_days: number };
      return `Every ${cfg.interval_days} days`;
    }
    case "monthly": {
      const cfg = config as { day_of_month: number };
      return `Monthly on day ${cfg.day_of_month}`;
    }
    case "custom": {
      const cfg = config as { interval: number; unit: string };
      return `Every ${cfg.interval} ${cfg.unit}`;
    }
    default:
      return type;
  }
}

interface RenderCellProps {
  template: ExpenseTemplate;
  columnKey: string;
  onEdit: (template: ExpenseTemplate) => void;
  onDeactivate: (template: ExpenseTemplate) => void;
  onActivate: (template: ExpenseTemplate) => void;
}

export function renderCell({
  template,
  columnKey,
  onEdit,
  onDeactivate,
  onActivate,
}: RenderCellProps) {
  switch (columnKey) {
    case "name":
      return <span className="font-medium">{template.description}</span>;
    case "amount":
      return (
        <AmountDisplay
          amount={template.base_amount}
          currency={template.currency}
        />
      );
    case "currency":
      return <CurrencyBadge currency={template.currency} />;
    case "category":
      return <CategoryBadge category={template.category} />;
    case "recurrence":
      return (
        <span className="text-sm text-default-600">
          {formatRecurrence(
            template.recurrence_type,
            template.recurrence_config,
          )}
        </span>
      );
    case "status":
      return (
        <Chip
          color={template.active ? "success" : "default"}
          size="sm"
          variant="soft"
        >
          {template.active ? "Active" : "Inactive"}
        </Chip>
      );
    case "actions":
      return (
        <div className="flex gap-2">
          <Button size="sm" variant="ghost" onPress={() => onEdit(template)}>
            Edit
          </Button>
          {template.active ? (
            <Button
              size="sm"
              variant="ghost"
              className="text-danger"
              onPress={() => onDeactivate(template)}
            >
              Deactivate
            </Button>
          ) : (
            <Button
              size="sm"
              variant="ghost"
              className="text-success"
              onPress={() => onActivate(template)}
            >
              Activate
            </Button>
          )}
        </div>
      );
    default:
      return null;
  }
}
