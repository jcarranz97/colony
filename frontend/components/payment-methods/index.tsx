"use client";
import { useEffect, useState } from "react";
import { Button } from "@heroui/react";
import { PaymentMethodsTable } from "./table";
import { AddPaymentMethod } from "./add-payment-method";
import { EditPaymentMethod } from "./edit-payment-method";
import { ConfirmModal } from "@/components/shared/confirm-modal";
import { EmptyState } from "@/components/shared/empty-state";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import {
  getPaymentMethods,
  deactivatePaymentMethod,
  activatePaymentMethod,
} from "./actions";
import type { PaymentMethod } from "@/helpers/types";

export function PaymentMethods() {
  const [methods, setMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<PaymentMethod | null>(null);
  const [deactivateTarget, setDeactivateTarget] =
    useState<PaymentMethod | null>(null);
  const [deactivating, setDeactivating] = useState(false);
  const [activateTarget, setActivateTarget] = useState<PaymentMethod | null>(
    null,
  );
  const [activating, setActivating] = useState(false);

  useEffect(() => {
    getPaymentMethods().then((res) => {
      if (res.success) setMethods(res.data);
      setLoading(false);
    });
  }, []);

  const handleCreated = (method: PaymentMethod) => {
    setMethods((prev) => [method, ...prev]);
  };

  const handleUpdated = (updated: PaymentMethod) => {
    setMethods((prev) => prev.map((m) => (m.id === updated.id ? updated : m)));
  };

  const handleActivate = async () => {
    if (!activateTarget) return;
    setActivating(true);
    const result = await activatePaymentMethod(activateTarget.id);
    if (result.success) {
      setMethods((prev) =>
        prev.map((m) =>
          m.id === activateTarget.id ? { ...m, active: true } : m,
        ),
      );
    }
    setActivating(false);
    setActivateTarget(null);
  };

  const handleDeactivate = async () => {
    if (!deactivateTarget) return;
    setDeactivating(true);
    const result = await deactivatePaymentMethod(deactivateTarget.id);
    if (result.success) {
      setMethods((prev) =>
        prev.map((m) =>
          m.id === deactivateTarget.id ? { ...m, active: false } : m,
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
          <h1 className="text-2xl font-bold">Payment Methods</h1>
          <p className="text-sm text-default-500 mt-1">
            Manage your cards and accounts
          </p>
        </div>
        <Button variant="primary" onPress={() => setAddOpen(true)}>
          Add Payment Method
        </Button>
      </div>

      {loading ? (
        <LoadingSkeleton rows={4} />
      ) : methods.length === 0 ? (
        <EmptyState
          message="No payment methods yet. Add one to get started."
          icon="💳"
        />
      ) : (
        <PaymentMethodsTable
          methods={methods}
          onEdit={(m) => setEditTarget(m)}
          onDeactivate={(m) => setDeactivateTarget(m)}
          onActivate={(m) => setActivateTarget(m)}
        />
      )}

      <AddPaymentMethod
        isOpen={addOpen}
        onClose={() => setAddOpen(false)}
        onCreated={handleCreated}
      />

      <EditPaymentMethod
        method={editTarget}
        isOpen={!!editTarget}
        onClose={() => setEditTarget(null)}
        onUpdated={handleUpdated}
      />

      <ConfirmModal
        isOpen={!!deactivateTarget}
        onClose={() => setDeactivateTarget(null)}
        onConfirm={handleDeactivate}
        title="Deactivate Payment Method"
        message={`Are you sure you want to deactivate "${deactivateTarget?.name}"? It will be hidden from new expenses.`}
        isLoading={deactivating}
      />

      <ConfirmModal
        isOpen={!!activateTarget}
        onClose={() => setActivateTarget(null)}
        onConfirm={handleActivate}
        title="Activate Payment Method"
        message={`Activate "${activateTarget?.name}"? It will become available for new expenses.`}
        isLoading={activating}
      />
    </div>
  );
}
