"use client";
import { useEffect, useState } from "react";
import { Button } from "@heroui/react";
import { ExpenseTemplatesTable } from "./table";
import { AddExpenseTemplate } from "./add-expense-template";
import { EditExpenseTemplate } from "./edit-expense-template";
import { ConfirmModal } from "@/components/shared/confirm-modal";
import { EmptyState } from "@/components/shared/empty-state";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import {
  getExpenseTemplates,
  deactivateExpenseTemplate,
  activateExpenseTemplate,
} from "./actions";
import { getPaymentMethods } from "@/components/payment-methods/actions";
import type { ExpenseTemplate, PaymentMethod } from "@/helpers/types";

export function ExpenseTemplates() {
  const [templates, setTemplates] = useState<ExpenseTemplate[]>([]);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<ExpenseTemplate | null>(null);
  const [deactivateTarget, setDeactivateTarget] =
    useState<ExpenseTemplate | null>(null);
  const [deactivating, setDeactivating] = useState(false);
  const [activateTarget, setActivateTarget] = useState<ExpenseTemplate | null>(
    null,
  );
  const [activating, setActivating] = useState(false);

  useEffect(() => {
    Promise.all([getExpenseTemplates(), getPaymentMethods()]).then(
      ([templatesRes, methodsRes]) => {
        if (templatesRes.success) setTemplates(templatesRes.data);
        if (methodsRes.success) setPaymentMethods(methodsRes.data);
        setLoading(false);
      },
    );
  }, []);

  const handleCreated = (template: ExpenseTemplate) => {
    setTemplates((prev) => [template, ...prev]);
  };

  const handleUpdated = (updated: ExpenseTemplate) => {
    setTemplates((prev) =>
      prev.map((t) => (t.id === updated.id ? updated : t)),
    );
  };

  const handleActivate = async () => {
    if (!activateTarget) return;
    setActivating(true);
    const result = await activateExpenseTemplate(activateTarget.id);
    if (result.success) {
      setTemplates((prev) =>
        prev.map((t) =>
          t.id === activateTarget.id ? { ...t, active: true } : t,
        ),
      );
    }
    setActivating(false);
    setActivateTarget(null);
  };

  const handleDeactivate = async () => {
    if (!deactivateTarget) return;
    setDeactivating(true);
    const result = await deactivateExpenseTemplate(deactivateTarget.id);
    if (result.success) {
      setTemplates((prev) =>
        prev.map((t) =>
          t.id === deactivateTarget.id ? { ...t, active: false } : t,
        ),
      );
    }
    setDeactivating(false);
    setDeactivateTarget(null);
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Expense Templates</h1>
          <p className="text-sm text-default-500 mt-1">
            Manage recurring expense templates
          </p>
        </div>
        <Button variant="primary" onPress={() => setAddOpen(true)}>
          Add Template
        </Button>
      </div>

      {loading ? (
        <LoadingSkeleton rows={4} />
      ) : templates.length === 0 ? (
        <EmptyState
          message="No expense templates yet. Add one to get started."
          icon="📋"
        />
      ) : (
        <ExpenseTemplatesTable
          templates={templates}
          onEdit={(t) => setEditTarget(t)}
          onDeactivate={(t) => setDeactivateTarget(t)}
          onActivate={(t) => setActivateTarget(t)}
        />
      )}

      <AddExpenseTemplate
        isOpen={addOpen}
        onClose={() => setAddOpen(false)}
        onCreated={handleCreated}
        paymentMethods={paymentMethods}
      />

      <EditExpenseTemplate
        template={editTarget}
        isOpen={!!editTarget}
        onClose={() => setEditTarget(null)}
        onUpdated={handleUpdated}
        paymentMethods={paymentMethods}
      />

      <ConfirmModal
        isOpen={!!deactivateTarget}
        onClose={() => setDeactivateTarget(null)}
        onConfirm={handleDeactivate}
        title="Deactivate Template"
        message={`Are you sure you want to deactivate "${deactivateTarget?.description}"? It will be excluded from new cycles.`}
        isLoading={deactivating}
      />

      <ConfirmModal
        isOpen={!!activateTarget}
        onClose={() => setActivateTarget(null)}
        onConfirm={handleActivate}
        title="Activate Template"
        message={`Activate "${activateTarget?.description}"? It will be included when generating expenses for new cycles.`}
        isLoading={activating}
      />
    </div>
  );
}
