"use client";
import { useEffect, useState } from "react";
import type {
  RecurrentIncome,
  PaymentMethod,
  CurrencyCode,
  RecurrenceType,
  RecurrenceConfig,
} from "@/helpers/types";
import {
  getCurrentUserAction,
  getRecurrentIncomes,
  addRecurrentIncome,
  editRecurrentIncome,
  deactivateRecurrentIncome,
  activateRecurrentIncome,
} from "./actions";
import { getPaymentMethods } from "@/components/payment-methods/actions";

// ── Helpers ───────────────────────────────────────────────────────────────────

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
      return `Monthly · day ${c.day_of_month ?? 1}`;
    }
    case "custom": {
      const c = config as { interval?: number; unit?: string };
      return `Every ${c.interval ?? 1} ${c.unit ?? "days"}`;
    }
    default:
      return type;
  }
}

const iconBtn: React.CSSProperties = {
  fontFamily: "var(--font-hand)",
  fontSize: 12,
  fontWeight: 600,
  background: "transparent",
  border: "1px solid var(--btn-cancel-border, #c0b090)",
  borderRadius: 4,
  padding: "3px 9px",
  cursor: "pointer",
  color: "var(--ink-light)",
  transition: "all 0.14s",
};

// ── Income Card ───────────────────────────────────────────────────────────────

function IncomeCard({
  income,
  onEdit,
  onDuplicate,
  onTrash,
}: {
  income: RecurrentIncome;
  onEdit: (i: RecurrentIncome) => void;
  onDuplicate: (i: RecurrentIncome) => void;
  onTrash: (i: RecurrentIncome) => void;
}) {
  return (
    <div className="nb-template-card">
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 16,
          flexShrink: 0,
          background: "var(--stat-card-bg, rgba(44,74,62,0.10))",
        }}
      >
        💰
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontFamily: "var(--font-title)",
            fontSize: 16,
            fontWeight: 700,
            color: "var(--ink)",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {income.description}
        </div>
        <div
          style={{
            fontFamily: "var(--font-hand)",
            fontSize: 12,
            color: "var(--ink-light)",
            opacity: 0.65,
            display: "flex",
            gap: 10,
            flexWrap: "wrap",
            marginTop: 2,
          }}
        >
          <span>
            {fmtRecurrence(income.recurrence_type, income.recurrence_config)}
          </span>
          {income.payment_method && <span>{income.payment_method.name}</span>}
        </div>
      </div>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-end",
          gap: 5,
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-title)",
            fontSize: 16,
            fontWeight: 700,
            color: "var(--ink)",
          }}
        >
          {fmtAmount(income.base_amount, income.currency)}
        </span>
        <span
          className="nb-template-badge nb-badge-fixed"
          style={{
            background: "rgba(44,74,62,0.12)",
            color: "var(--cover-bg)",
          }}
        >
          {income.currency}
        </span>
      </div>

      <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
        <button style={iconBtn} onClick={() => onEdit(income)}>
          Edit
        </button>
        <button
          style={{ ...iconBtn, color: "var(--cover-bg)" }}
          onClick={() => onDuplicate(income)}
          title="Duplicate"
        >
          Duplicate
        </button>
        <button
          style={{
            ...iconBtn,
            color: "rgba(220,53,69,0.7)",
            border: "1px solid rgba(220,53,69,0.35)",
          }}
          onClick={() => onTrash(income)}
          title="Move to trash"
        >
          🗑 Trash
        </button>
      </div>
    </div>
  );
}

// ── Trashed Income Card (admin only) ─────────────────────────────────────────

function TrashedIncomeCard({
  income,
  onRestore,
  restoring,
}: {
  income: RecurrentIncome;
  onRestore: (i: RecurrentIncome) => void;
  restoring: boolean;
}) {
  return (
    <div
      style={{
        border: "1px dashed rgba(180,180,180,0.5)",
        borderRadius: 6,
        padding: "10px 14px",
        background: "rgba(180,180,180,0.07)",
        opacity: 0.7,
        display: "flex",
        alignItems: "center",
        gap: 12,
        marginBottom: 8,
      }}
    >
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 14,
          flexShrink: 0,
          background: "rgba(180,180,180,0.15)",
        }}
      >
        💰
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontFamily: "var(--font-title)",
            fontSize: 15,
            color: "var(--ink)",
            textDecoration: "line-through",
            opacity: 0.55,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {income.description}
        </div>
        <div
          style={{
            fontFamily: "var(--font-hand)",
            fontSize: 12,
            color: "var(--ink-light)",
            opacity: 0.45,
          }}
        >
          {fmtAmount(income.base_amount, income.currency)}
        </div>
      </div>
      <span
        style={{
          fontFamily: "var(--font-hand)",
          fontSize: 11,
          background: "rgba(180,180,180,0.28)",
          color: "var(--ink-light)",
          borderRadius: 3,
          padding: "2px 8px",
          flexShrink: 0,
        }}
      >
        trashed
      </span>
      <button
        style={{
          fontFamily: "var(--font-hand)",
          fontSize: 12,
          fontWeight: 600,
          background: "transparent",
          border: "1px solid var(--hl-paid-border, rgba(80,200,100,0.6))",
          borderRadius: 4,
          padding: "3px 10px",
          cursor: "pointer",
          color: "var(--hl-paid-border, rgba(80,200,100,0.8))",
          flexShrink: 0,
        }}
        onClick={() => onRestore(income)}
        disabled={restoring}
      >
        ↩ Restore
      </button>
    </div>
  );
}

// ── Confirm Trash Modal ───────────────────────────────────────────────────────

function ConfirmTrashModal({
  isOpen,
  onClose,
  income,
  onConfirmed,
}: {
  isOpen: boolean;
  onClose: () => void;
  income: RecurrentIncome | null;
  onConfirmed: (id: string) => void;
}) {
  const [trashing, setTrashing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) setError(null);
  }, [isOpen]);

  const handleConfirm = async () => {
    if (!income) return;
    setTrashing(true);
    setError(null);
    const res = await deactivateRecurrentIncome(income.id);
    if (res.success) {
      onConfirmed(income.id);
      onClose();
    } else {
      setError(res.error.message);
    }
    setTrashing(false);
  };

  if (!isOpen || !income) return null;

  return (
    <div
      className="nb-modal-backdrop"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="nb-modal">
        <button className="nb-modal-close" onClick={onClose}>
          ✕
        </button>
        <div className="nb-modal-title">Move to Trash?</div>
        <p
          style={{
            fontFamily: "var(--font-hand)",
            fontSize: 15,
            color: "var(--ink)",
            marginBottom: 8,
            lineHeight: 1.5,
          }}
        >
          <strong>{income.description}</strong> will be deactivated and moved to
          trash. It will no longer generate incomes in new cycles. Contact your
          admin if you need it restored.
        </p>
        {error && (
          <p
            style={{
              fontFamily: "var(--font-hand)",
              color: "var(--hl-overdue-border)",
              fontSize: 14,
              marginBottom: 8,
            }}
          >
            {error}
          </p>
        )}
        <div className="nb-modal-actions">
          <button className="nb-btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button
            className="nb-btn-danger"
            onClick={handleConfirm}
            disabled={trashing}
          >
            {trashing ? "Moving…" : "Move to Trash 🗑"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Recurrence config sub-fields ──────────────────────────────────────────────

function RecurrenceFields({
  type,
  config,
  onChange,
}: {
  type: RecurrenceType;
  config: Record<string, unknown>;
  onChange: (c: Record<string, unknown>) => void;
}) {
  switch (type) {
    case "weekly":
      return (
        <div className="nb-form-group">
          <label className="nb-form-label">Day of week</label>
          <select
            className="nb-form-select"
            value={(config.day_of_week as number) ?? 1}
            onChange={(e) =>
              onChange({ day_of_week: parseInt(e.target.value) })
            }
          >
            {DAY_NAMES.map((d, i) => (
              <option key={i} value={i}>
                {d}
              </option>
            ))}
          </select>
        </div>
      );
    case "bi_weekly":
      return (
        <div className="nb-form-group">
          <label className="nb-form-label">Interval (days)</label>
          <input
            className="nb-form-input"
            type="number"
            min={1}
            value={(config.interval_days as number) ?? 14}
            onChange={(e) =>
              onChange({ interval_days: parseInt(e.target.value) })
            }
          />
        </div>
      );
    case "monthly":
      return (
        <div className="nb-form-group">
          <label className="nb-form-label">Day of month</label>
          <input
            className="nb-form-input"
            type="number"
            min={1}
            max={31}
            value={(config.day_of_month as number) ?? 1}
            onChange={(e) =>
              onChange({ day_of_month: parseInt(e.target.value) })
            }
          />
        </div>
      );
    case "custom":
      return (
        <div className="nb-form-row">
          <div className="nb-form-group">
            <label className="nb-form-label">Interval</label>
            <input
              className="nb-form-input"
              type="number"
              min={1}
              value={(config.interval as number) ?? 1}
              onChange={(e) =>
                onChange({ ...config, interval: parseInt(e.target.value) })
              }
            />
          </div>
          <div className="nb-form-group">
            <label className="nb-form-label">Unit</label>
            <select
              className="nb-form-select"
              value={(config.unit as string) ?? "days"}
              onChange={(e) => onChange({ ...config, unit: e.target.value })}
            >
              <option value="days">days</option>
              <option value="weeks">weeks</option>
              <option value="months">months</option>
            </select>
          </div>
        </div>
      );
    default:
      return null;
  }
}

// ── Income Modal (Add / Edit) ─────────────────────────────────────────────────

interface IncomeForm {
  description: string;
  base_amount: string;
  currency: CurrencyCode;
  recurrence_type: RecurrenceType;
  recurrence_config: Record<string, unknown>;
  reference_date: string;
  payment_method_id: string;
}

const DEFAULT_CONFIG: Record<RecurrenceType, Record<string, unknown>> = {
  weekly: { day_of_week: 1 },
  bi_weekly: { interval_days: 14 },
  monthly: { day_of_month: 1 },
  custom: { interval: 1, unit: "days" },
};

function IncomeModal({
  isOpen,
  title,
  initial,
  paymentMethods,
  onClose,
  onSave,
}: {
  isOpen: boolean;
  title: string;
  initial: IncomeForm;
  paymentMethods: PaymentMethod[];
  onClose: () => void;
  onSave: (form: IncomeForm) => Promise<string | null>;
}) {
  const [form, setForm] = useState<IncomeForm>(initial);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setForm(initial);
      setError(null);
    }
  }, [isOpen]);

  const set = <K extends keyof IncomeForm>(k: K, v: IncomeForm[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const handleRecurrenceTypeChange = (rt: RecurrenceType) => {
    setForm((f) => {
      const config =
        rt === "monthly"
          ? { day_of_month: new Date(f.reference_date).getUTCDate() }
          : (DEFAULT_CONFIG[rt] ?? {});
      return { ...f, recurrence_type: rt, recurrence_config: config };
    });
  };

  const handleReferenceDateChange = (dateStr: string) => {
    setForm((f) => {
      const updated: IncomeForm = { ...f, reference_date: dateStr };
      if (f.recurrence_type === "monthly") {
        updated.recurrence_config = {
          ...f.recurrence_config,
          day_of_month: new Date(dateStr).getUTCDate(),
        };
      }
      return updated;
    });
  };

  const handleSubmit = async () => {
    if (
      !form.description.trim() ||
      !form.base_amount ||
      !form.payment_method_id
    )
      return;
    setSaving(true);
    const err = await onSave(form);
    if (err) setError(err);
    setSaving(false);
  };

  if (!isOpen) return null;

  return (
    <div
      className="nb-modal-backdrop"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className="nb-modal"
        style={{ width: 480 }}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="nb-modal-close" onClick={onClose}>
          ✕
        </button>
        <div className="nb-modal-title">{title}</div>

        <div className="nb-form-group">
          <label className="nb-form-label">Name</label>
          <input
            className="nb-form-input"
            placeholder="e.g. Salary"
            value={form.description}
            onChange={(e) => set("description", e.target.value)}
          />
        </div>

        <div className="nb-form-row">
          <div className="nb-form-group">
            <label className="nb-form-label">Amount</label>
            <input
              className="nb-form-input"
              type="number"
              placeholder="0.00"
              value={form.base_amount}
              onChange={(e) => set("base_amount", e.target.value)}
            />
          </div>
          <div className="nb-form-group">
            <label className="nb-form-label">Currency</label>
            <select
              className="nb-form-select"
              value={form.currency}
              onChange={(e) => set("currency", e.target.value as CurrencyCode)}
            >
              <option value="USD">USD</option>
              <option value="MXN">MXN</option>
            </select>
          </div>
        </div>

        <div className="nb-form-row">
          <div className="nb-form-group">
            <label className="nb-form-label">Recurrence</label>
            <select
              className="nb-form-select"
              value={form.recurrence_type}
              onChange={(e) =>
                handleRecurrenceTypeChange(e.target.value as RecurrenceType)
              }
            >
              <option value="weekly">Weekly</option>
              <option value="bi_weekly">Bi-weekly</option>
              <option value="monthly">Monthly</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          <div className="nb-form-group">
            <label className="nb-form-label">Start date</label>
            <input
              className="nb-form-input"
              type="date"
              value={form.reference_date}
              onChange={(e) => handleReferenceDateChange(e.target.value)}
            />
          </div>
        </div>

        <RecurrenceFields
          type={form.recurrence_type}
          config={form.recurrence_config}
          onChange={(c) => set("recurrence_config", c)}
        />

        <div className="nb-form-group">
          <label className="nb-form-label">Payment method</label>
          <select
            className="nb-form-select"
            value={form.payment_method_id}
            onChange={(e) => set("payment_method_id", e.target.value)}
          >
            <option value="">— select —</option>
            {paymentMethods
              .filter((m) => m.active)
              .map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} — {m.method_type}
                </option>
              ))}
          </select>
        </div>

        {error && (
          <p
            style={{
              fontFamily: "var(--font-hand)",
              color: "var(--hl-overdue-border)",
              fontSize: 14,
              marginBottom: 8,
            }}
          >
            {error}
          </p>
        )}

        <div className="nb-modal-actions">
          <button className="nb-btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button
            className="nb-btn-primary"
            onClick={handleSubmit}
            disabled={saving}
          >
            {saving ? "Saving…" : "Save ✓"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

const BLANK_FORM: IncomeForm = {
  description: "",
  base_amount: "",
  currency: "USD",
  recurrence_type: "monthly",
  recurrence_config: { day_of_month: 1 },
  reference_date: new Date().toISOString().split("T")[0],
  payment_method_id: "",
};

function incomeToForm(i: RecurrentIncome): IncomeForm {
  return {
    description: i.description,
    base_amount: i.base_amount,
    currency: i.currency,
    recurrence_type: i.recurrence_type,
    recurrence_config: i.recurrence_config as Record<string, unknown>,
    reference_date: i.reference_date,
    payment_method_id: i.payment_method?.id ?? "",
  };
}

export function Incomes() {
  const [incomes, setIncomes] = useState<RecurrentIncome[]>([]);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [addInitial, setAddInitial] = useState<IncomeForm>(BLANK_FORM);
  const [editTarget, setEditTarget] = useState<RecurrentIncome | null>(null);
  const [trashTarget, setTrashTarget] = useState<RecurrentIncome | null>(null);
  const [restoringId, setRestoringId] = useState<string | null>(null);
  const [restoreError, setRestoreError] = useState<string | null>(null);

  useEffect(() => {
    getCurrentUserAction().then(async (userRes) => {
      const admin = userRes.success && userRes.data.role === "admin";
      setIsAdmin(admin);
      const [iRes, mRes] = await Promise.all([
        getRecurrentIncomes(admin),
        getPaymentMethods(),
      ]);
      if (iRes.success) setIncomes(iRes.data);
      if (mRes.success) setPaymentMethods(mRes.data);
      setLoading(false);
    });
  }, []);

  const activeIncomes = incomes.filter((i) => i.active);
  const trashedIncomes = incomes.filter((i) => !i.active);

  const handleTrashed = (id: string) => {
    setIncomes((prev) =>
      prev.map((i) => (i.id === id ? { ...i, active: false } : i)),
    );
    setTrashTarget(null);
  };

  const handleRestore = async (income: RecurrentIncome) => {
    setRestoringId(income.id);
    setRestoreError(null);
    const res = await activateRecurrentIncome(income.id);
    if (res.success) {
      setIncomes((prev) =>
        prev.map((i) => (i.id === income.id ? { ...i, active: true } : i)),
      );
    } else {
      setRestoreError(res.error.message);
    }
    setRestoringId(null);
  };

  const handleDuplicate = (income: RecurrentIncome) => {
    setAddInitial({
      ...incomeToForm(income),
      description: `Copy of ${income.description}`,
    });
    setAddOpen(true);
  };

  const handleAdd = async (form: IncomeForm): Promise<string | null> => {
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
      setIncomes((prev) => [res.data, ...prev]);
      setAddOpen(false);
      return null;
    }
    return res.error.message;
  };

  const handleEdit = async (form: IncomeForm): Promise<string | null> => {
    if (!editTarget) return null;
    const res = await editRecurrentIncome(editTarget.id, {
      description: form.description,
      base_amount: form.base_amount,
      currency: form.currency,
      recurrence_type: form.recurrence_type,
      recurrence_config: form.recurrence_config as RecurrenceConfig,
      reference_date: form.reference_date,
      payment_method_id: form.payment_method_id,
    });
    if (res.success) {
      setIncomes((prev) =>
        prev.map((i) => (i.id === editTarget.id ? res.data : i)),
      );
      setEditTarget(null);
      return null;
    }
    return res.error.message;
  };

  if (loading) {
    return (
      <div className="nb-empty">
        <div className="nb-empty-icon">📖</div>
        <div className="nb-empty-text">Loading…</div>
      </div>
    );
  }

  return (
    <>
      <div className="nb-page-title">Recurrent Incomes</div>
      <div className="nb-page-subtitle">
        Recurring income sources that auto-populate new cycles
      </div>

      <div
        style={{
          fontFamily: "var(--font-hand)",
          fontSize: 13,
          color: "var(--ink-light)",
          opacity: 0.5,
          marginBottom: 18,
        }}
      >
        {activeIncomes.length} active
        {isAdmin && ` · ${trashedIncomes.length} trashed`}
      </div>

      {activeIncomes.length > 0 && (
        <>
          <div className="nb-section-title">✓ Active</div>
          {activeIncomes.map((i) => (
            <IncomeCard
              key={i.id}
              income={i}
              onEdit={setEditTarget}
              onDuplicate={handleDuplicate}
              onTrash={setTrashTarget}
            />
          ))}
        </>
      )}

      {incomes.length === 0 && (
        <div className="nb-empty">
          <div className="nb-empty-icon">💰</div>
          <div className="nb-empty-text">
            No recurrent incomes yet — add one to get started!
          </div>
        </div>
      )}

      <button
        className="nb-add-btn"
        onClick={() => {
          setAddInitial(BLANK_FORM);
          setAddOpen(true);
        }}
      >
        + New Recurrent Income
      </button>

      {/* Trashed section (admin only) */}
      {isAdmin && trashedIncomes.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <div
            className="nb-section-title"
            style={{ opacity: 0.55, marginBottom: 12 }}
          >
            🗑 Trashed Recurrent Incomes
          </div>
          {restoreError && (
            <p
              style={{
                fontFamily: "var(--font-hand)",
                color: "var(--hl-overdue-border)",
                fontSize: 14,
                marginBottom: 10,
              }}
            >
              {restoreError}
            </p>
          )}
          {trashedIncomes.map((i) => (
            <TrashedIncomeCard
              key={i.id}
              income={i}
              onRestore={handleRestore}
              restoring={restoringId === i.id}
            />
          ))}
        </div>
      )}

      <IncomeModal
        isOpen={addOpen}
        title={
          addInitial.description.startsWith("Copy of")
            ? "Duplicate Income"
            : "New Recurrent Income"
        }
        initial={addInitial}
        paymentMethods={paymentMethods}
        onClose={() => setAddOpen(false)}
        onSave={handleAdd}
      />

      <IncomeModal
        isOpen={!!editTarget}
        title="Edit Recurrent Income"
        initial={editTarget ? incomeToForm(editTarget) : BLANK_FORM}
        paymentMethods={paymentMethods}
        onClose={() => setEditTarget(null)}
        onSave={handleEdit}
      />

      <ConfirmTrashModal
        isOpen={trashTarget !== null}
        onClose={() => setTrashTarget(null)}
        income={trashTarget}
        onConfirmed={handleTrashed}
      />
    </>
  );
}
