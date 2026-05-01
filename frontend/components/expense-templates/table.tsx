"use client";
import { Table } from "@heroui/react";
import { renderCell } from "./render-cell";
import type { ExpenseTemplate } from "@/helpers/types";

const COLUMNS = [
  { key: "name", label: "Name" },
  { key: "amount", label: "Amount" },
  { key: "currency", label: "Currency" },
  { key: "category", label: "Category" },
  { key: "recurrence", label: "Recurrence" },
  { key: "status", label: "Status" },
  { key: "actions", label: "Actions" },
];

interface ExpenseTemplatesTableProps {
  templates: ExpenseTemplate[];
  onEdit: (template: ExpenseTemplate) => void;
  onDeactivate: (template: ExpenseTemplate) => void;
  onActivate: (template: ExpenseTemplate) => void;
}

export function ExpenseTemplatesTable({
  templates,
  onEdit,
  onDeactivate,
  onActivate,
}: ExpenseTemplatesTableProps) {
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
            {templates.map((template) => (
              <Table.Row key={template.id} id={template.id}>
                {COLUMNS.map((col) => (
                  <Table.Cell key={col.key}>
                    {renderCell({
                      template,
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
