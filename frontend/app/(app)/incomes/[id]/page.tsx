"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import type {
  PaymentMethod,
  RecurrentIncome,
  RecurrenceConfig,
  RecurrenceType,
} from "@/helpers/types";
import { formatPaymentMethodName } from "@/helpers/formatters";
import {
  getCurrentUserAction,
  getRecurrentIncome,
  addRecurrentIncome,
  editRecurrentIncome,
  activateRecurrentIncome,
} from "@/components/incomes/actions";
import { getPaymentMethods } from "@/components/payment-methods/actions";
import {
  IncomeModal,
  ConfirmTrashModal,
  incomeToForm,
  type IncomeForm,
} from "@/components/incomes";

const DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function fmtAmount(amount: string, currency: string): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(parseFloat(amount));
}

function fmtRecurrence(type: RecurrenceType, config: RecurrenceConfig): string {
  switch (type) {
    case "weekly": {
      const c = config as { day_of_week?: number };
      return `Weekly on ${DAY_NAMES[c.day_of_week ?? 1] ?? "?"}`;
    }
    case "bi_weekly": {
      const c = config as { interval_days?: number };
      return `Every ${c.interval_days ?? 14} days`;
    }
    case "monthly": {
      const c = config as { day_of_month?: number };
      return `Monthly on day ${c.day_of_month ?? 1}`;
    }
    case "custom": {
      const c = config as { interval?: number; unit?: string };
      return `Every ${c.interval ?? 1} ${c.unit ?? "days"}`;
    }
    default:
      return type;
  }
}

export default function RecurrentIncomeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [income, setIncome] = useState<RecurrentIncome | null>(null);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [duplicateOpen, setDuplicateOpen] = useState(false);
  const [trashOpen, setTrashOpen] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [restoreError, setRestoreError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      getCurrentUserAction(),
      getRecurrentIncome(id),
      getPaymentMethods(),
    ]).then(([userRes, incRes, pmRes]) => {
      if (cancelled) return;
      if (userRes.success) setIsAdmin(userRes.data.role === "admin");
      if (incRes.success) setIncome(incRes.data);
      else setNotFound(true);
      if (pmRes.success) setPaymentMethods(pmRes.data);
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const handleBack = () => {
    if (window.history.length > 1) router.back();
    else router.push("/incomes");
  };

  const handleEditSave = async (form: IncomeForm): Promise<string | null> => {
    if (!income) return null;
    const res = await editRecurrentIncome(income.id, {
      description: form.description,
      base_amount: form.base_amount,
      currency: form.currency,
      recurrence_type: form.recurrence_type,
      recurrence_config: form.recurrence_config as RecurrenceConfig,
      reference_date: form.reference_date,
      payment_method_id: form.payment_method_id,
    });
    if (res.success) {
      setIncome(res.data);
      setEditOpen(false);
      return null;
    }
    return res.error.message;
  };

  const handleDuplicateSave = async (
    form: IncomeForm,
  ): Promise<string | null> => {
    const res = await addRecurrentIncome({
      description: form.description,
      base_amount: form.base_amount,
      currency: form.currency,
      recurrence_type: form.recurrence_type,
      recurrence_config: form.recurrence_config as RecurrenceConfig,
      reference_date: form.reference_date,
      payment_method_id: form.payment_method_id,
    });
    if (res.success) {
      setDuplicateOpen(false);
      router.push(`/incomes/${res.data.id}`);
      return null;
    }
    return res.error.message;
  };

  const handleRestore = async () => {
    if (!income) return;
    setRestoring(true);
    setRestoreError(null);
    const res = await activateRecurrentIncome(income.id);
    if (res.success) {
      setIncome({ ...income, active: true });
    } else {
      setRestoreError(res.error.message);
    }
    setRestoring(false);
  };

  if (loading) {
    return (
      <div className="nb-empty">
        <div className="nb-empty-icon">📖</div>
        <div className="nb-empty-text">Loading…</div>
      </div>
    );
  }

  if (notFound || !income) {
    return (
      <>
        <div className="nb-page-title">Recurrent Income</div>
        <div className="nb-empty">
          <div className="nb-empty-icon">🔍</div>
          <div className="nb-empty-text">
            This recurrent income does not exist or you don&apos;t have access.
          </div>
          <button
            className="nb-btn-cancel"
            style={{ marginTop: 16 }}
            onClick={handleBack}
          >
            ← Back to Recurrent Incomes
          </button>
        </div>
      </>
    );
  }

  return (
    <>
      <button className="nb-back-btn" onClick={handleBack}>
        ← Back to recurrent incomes
      </button>

      <div className="nb-page-title">{income.description}</div>
      <div className="nb-page-subtitle">Recurrent income source</div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          marginBottom: 24,
          padding: "16px 18px",
          border: "1px solid var(--paper-line, rgba(140,140,140,0.25))",
          borderRadius: 8,
        }}
      >
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: "50%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 26,
            flexShrink: 0,
            background: "var(--stat-card-bg, rgba(44,74,62,0.10))",
          }}
        >
          💰
        </div>
        <div style={{ flex: 1 }}>
          <div
            style={{
              fontFamily: "var(--font-title)",
              fontSize: 24,
              fontWeight: 700,
              color: "var(--ink)",
            }}
          >
            {fmtAmount(income.base_amount, income.currency)}
          </div>
          <div
            style={{
              fontFamily: "var(--font-hand)",
              fontSize: 13,
              color: "var(--ink-light)",
              opacity: 0.75,
              marginTop: 4,
              display: "flex",
              gap: 8,
              flexWrap: "wrap",
            }}
          >
            <span
              className="nb-template-badge nb-badge-fixed"
              style={{
                background: "rgba(44,74,62,0.12)",
                color: "var(--cover-bg)",
              }}
            >
              {income.currency}
            </span>
            {!income.active && (
              <span
                style={{
                  fontFamily: "var(--font-hand)",
                  fontSize: 11,
                  background: "rgba(180,180,180,0.28)",
                  color: "var(--ink-light)",
                  borderRadius: 3,
                  padding: "2px 8px",
                }}
              >
                trashed
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="nb-section-title">Details</div>
      <div
        style={{
          fontFamily: "var(--font-hand)",
          fontSize: 14,
          color: "var(--ink)",
          lineHeight: 1.8,
          marginBottom: 24,
        }}
      >
        <div>
          <strong>Recurrence:</strong>{" "}
          {fmtRecurrence(income.recurrence_type, income.recurrence_config)}
        </div>
        <div>
          <strong>Start date:</strong> {income.reference_date}
        </div>
        {income.payment_method && (
          <div>
            <strong>Payment method:</strong>{" "}
            {formatPaymentMethodName(income.payment_method)}
          </div>
        )}
      </div>

      {restoreError && (
        <p
          style={{
            fontFamily: "var(--font-hand)",
            color: "var(--hl-overdue-border)",
            fontSize: 14,
            marginBottom: 12,
          }}
        >
          {restoreError}
        </p>
      )}

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {income.active ? (
          <>
            <button
              className="nb-btn-primary"
              onClick={() => setEditOpen(true)}
            >
              Edit
            </button>
            <button
              className="nb-btn-cancel"
              onClick={() => setDuplicateOpen(true)}
            >
              Duplicate
            </button>
            <button
              className="nb-btn-cancel"
              style={{
                color: "rgba(220,53,69,0.7)",
                border: "1px solid rgba(220,53,69,0.35)",
              }}
              onClick={() => setTrashOpen(true)}
            >
              🗑 Move to Trash
            </button>
          </>
        ) : (
          isAdmin && (
            <button
              className="nb-btn-primary"
              onClick={handleRestore}
              disabled={restoring}
            >
              {restoring ? "Restoring…" : "↩ Restore"}
            </button>
          )
        )}
      </div>

      <IncomeModal
        isOpen={editOpen}
        title="Edit Recurrent Income"
        initial={incomeToForm(income)}
        paymentMethods={paymentMethods}
        onClose={() => setEditOpen(false)}
        onSave={handleEditSave}
      />

      <IncomeModal
        isOpen={duplicateOpen}
        title="Duplicate Recurrent Income"
        initial={{
          ...incomeToForm(income),
          description: `Copy of ${income.description}`,
        }}
        paymentMethods={paymentMethods}
        onClose={() => setDuplicateOpen(false)}
        onSave={handleDuplicateSave}
      />

      <ConfirmTrashModal
        isOpen={trashOpen}
        onClose={() => setTrashOpen(false)}
        income={income}
        onConfirmed={() => {
          setTrashOpen(false);
          router.push("/incomes");
        }}
      />
    </>
  );
}
