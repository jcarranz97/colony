import { Button, Chip } from "@heroui/react";
import { CurrencyBadge } from "@/components/shared/currency-badge";
import type { PaymentMethod, PaymentMethodType } from "@/helpers/types";

const TYPE_LABEL: Record<PaymentMethodType, string> = {
  debit: "Debit",
  credit: "Credit",
  cash: "Cash",
  transfer: "Transfer",
};

interface RenderCellProps {
  method: PaymentMethod;
  columnKey: string;
  onEdit: (method: PaymentMethod) => void;
  onDeactivate: (method: PaymentMethod) => void;
  onActivate: (method: PaymentMethod) => void;
}

export function renderCell({
  method,
  columnKey,
  onEdit,
  onDeactivate,
  onActivate,
}: RenderCellProps) {
  switch (columnKey) {
    case "name":
      return <span className="font-medium">{method.name}</span>;
    case "type":
      return (
        <span className="text-sm text-default-600">
          {TYPE_LABEL[method.method_type]}
        </span>
      );
    case "currency":
      return <CurrencyBadge currency={method.default_currency} />;
    case "status":
      return (
        <Chip
          color={method.active ? "success" : "default"}
          size="sm"
          variant="soft"
        >
          {method.active ? "Active" : "Inactive"}
        </Chip>
      );
    case "actions":
      return (
        <div className="flex gap-2">
          <Button size="sm" variant="ghost" onPress={() => onEdit(method)}>
            Edit
          </Button>
          {method.active ? (
            <Button
              size="sm"
              variant="ghost"
              className="text-danger"
              onPress={() => onDeactivate(method)}
            >
              Deactivate
            </Button>
          ) : (
            <Button
              size="sm"
              variant="ghost"
              className="text-success"
              onPress={() => onActivate(method)}
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
