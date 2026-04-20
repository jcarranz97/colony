"use client";
import { Table } from "@heroui/react";
import { renderCell } from "./render-cell";
import type { PaymentMethod } from "@/helpers/types";

const COLUMNS = [
  { key: "name", label: "Name" },
  { key: "type", label: "Type" },
  { key: "currency", label: "Currency" },
  { key: "status", label: "Status" },
  { key: "actions", label: "Actions" },
];

interface PaymentMethodsTableProps {
  methods: PaymentMethod[];
  onEdit: (method: PaymentMethod) => void;
  onDeactivate: (method: PaymentMethod) => void;
  onActivate: (method: PaymentMethod) => void;
}

export function PaymentMethodsTable({
  methods,
  onEdit,
  onDeactivate,
  onActivate,
}: PaymentMethodsTableProps) {
  return (
    <Table.Root>
      <Table.ScrollContainer>
        <Table.Content>
          <Table.Header>
            {COLUMNS.map((col) => (
              <Table.Column key={col.key} isRowHeader={col.key === "name"}>
                {col.label}
              </Table.Column>
            ))}
          </Table.Header>
          <Table.Body>
            {methods.map((method) => (
              <Table.Row key={method.id} id={method.id}>
                {COLUMNS.map((col) => (
                  <Table.Cell key={col.key}>
                    {renderCell({
                      method,
                      columnKey: col.key,
                      onEdit,
                      onDeactivate,
                      onActivate,
                    })}
                  </Table.Cell>
                ))}
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Content>
      </Table.ScrollContainer>
    </Table.Root>
  );
}
