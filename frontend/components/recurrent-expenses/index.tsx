"use client";
import { useEffect, useState } from "react";
import type {
  RecurrentExpense,
  PaymentMethod,
  CurrencyCode,
  ExpenseCategory,
  RecurrenceType,
  RecurrenceConfig,
} from "@/helpers/types";
import {
  getCurrentUserAction,
  getRecurrentExpenses,
  addRecurrentExpense,
  editRecurrentExpense,
  deactivateRecurrentExpense,
  activateRecurrentExpense,
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

// ── Notebook icon button style ────────────────────────────────────────────────

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

// ── Template Card ─────────────────────────────────────────────────────────────

function TemplateCard({
  template,
  onEdit,
  onDuplicate,
  onTrash,
}: {
  template: RecurrentExpense;
  onEdit: (t: RecurrentExpense) => void;
  onDuplicate: (t: RecurrentExpense) => void;
  onTrash: (t: RecurrentExpense) => void;
}) {
  const isFixed = template.category === "fixed";
  return (
    <div className="nb-template-card">
      {/* Category icon */}
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
          background: isFixed
            ? "var(--stat-card-bg, rgba(44,74,62,0.10))"
            : "var(--add-btn-hover, rgba(201,168,76,0.15))",
        }}
      >
        {isFixed ? "📌" : "🛒"}
      </div>

      {/* Info */}
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
          {template.description}
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
            {fmtRecurrence(
              template.recurrence_type,
              template.recurrence_config,
            )}
          </span>
          {template.payment_method && (
            <span>{template.payment_method.name}</span>
          )}
          {template.autopay && (
            <span style={{ color: "#276838" }}>⚡ Auto-pay enabled</span>
          )}
        </div>
      </div>

      {/* Right side: amount + badges */}
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
          {fmtAmount(template.base_amount, template.currency)}
        </span>
        <div style={{ display: "flex", gap: 4 }}>
          <span
            className={`nb-template-badge ${isFixed ? "nb-badge-fixed" : "nb-badge-variable"}`}
          >
            {template.category}
          </span>
          {template.autopay && (
            <span className="nb-template-badge nb-badge-autopay">autopay</span>
          )}
        </div>
      </div>

      {/* Action buttons */}
      <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
        <button style={iconBtn} onClick={() => onEdit(template)}>
          Edit
        </button>
        <button
          style={{ ...iconBtn, color: "var(--cover-bg)" }}
          onClick={() => onDuplicate(template)}
          title="Duplicate this template"
        >
          Duplicate
        </button>
        <button
          style={{
            ...iconBtn,
            color: "rgba(220,53,69,0.7)",
            border: "1px solid rgba(220,53,69,0.35)",
          }}
          onClick={() => onTrash(template)}
          title="Move to trash"
        >
          🗑 Trash
        </button>
      </div>
    </div>
  );
}

// ── Trashed Template Card (admin only) ────────────────────────────────────────

function TrashedTemplateCard({
  template,
  onRestore,
  restoring,
}: {
  template: RecurrentExpense;
  onRestore: (t: RecurrentExpense) => void;
  restoring: boolean;
}) {
  const isFixed = template.category === "fixed";
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
        {isFixed ? "📌" : "🛒"}
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
          {template.description}
        </div>
        <div
          style={{
            fontFamily: "var(--font-hand)",
            fontSize: 12,
            color: "var(--ink-light)",
            opacity: 0.45,
          }}
        >
          {fmtAmount(template.base_amount, template.currency)} ·{" "}
          {template.category}
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
        onClick={() => onRestore(template)}
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
  template,
  onConfirmed,
}: {
  isOpen: boolean;
  onClose: () => void;
  template: RecurrentExpense | null;
  onConfirmed: (id: string) => void;
}) {
  const [trashing, setTrashing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) setError(null);
  }, [isOpen]);

  const handleConfirm = async () => {
    if (!template) return;
    setTrashing(true);
    setError(null);
    const res = await deactivateRecurrentExpense(template.id);
    if (res.success) {
      onConfirmed(template.id);
      onClose();
    } else {
      setError(res.error.message);
    }
    setTrashing(false);
  };

  if (!isOpen || !template) return null;

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
          <strong>{template.description}</strong> will be deactivated and moved
          to trash. It will no longer generate expenses in new cycles. Contact
          your admin if you need it restored.
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

// ── Template Modal (Add / Edit) ───────────────────────────────────────────────

interface TemplateForm {
  description: string;
  base_amount: string;
  currency: CurrencyCode;
  category: ExpenseCategory;
  recurrence_type: RecurrenceType;
  recurrence_config: Record<string, unknown>;
  reference_date: string;
  autopay: boolean;
  payment_method_id: string;
}

const DEFAULT_CONFIG: Record<RecurrenceType, Record<string, unknown>> = {
  weekly: { day_of_week: 1 },
  bi_weekly: { interval_days: 14 },
  monthly: { day_of_month: 1 },
  custom: { interval: 1, unit: "days" },
};

function TemplateModal({
  isOpen,
  title,
  initial,
  paymentMethods,
  onClose,
  onSave,
  existingNames,
}: {
  isOpen: boolean;
  title: string;
  initial: TemplateForm;
  paymentMethods: PaymentMethod[];
  onClose: () => void;
  onSave: (form: TemplateForm) => Promise<string | null>;
  existingNames?: string[];
}) {
  const [form, setForm] = useState<TemplateForm>(initial);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setForm(initial);
      setError(null);
    }
  }, [isOpen]);

  const set = <K extends keyof TemplateForm>(k: K, v: TemplateForm[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const nameSuggestions =
    existingNames && form.description.trim().length > 0
      ? existingNames
          .filter((n) =>
            n.toLowerCase().includes(form.description.trim().toLowerCase()),
          )
          .slice(0, 5)
      : [];

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
      const updated: TemplateForm = { ...f, reference_date: dateStr };
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
    if (!form.description.trim() || !form.base_amount) return;
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
            placeholder="e.g. Rent"
            value={form.description}
            onChange={(e) => set("description", e.target.value)}
          />
        </div>

        {nameSuggestions.length > 0 && (
          <div className="nb-similar-items">
            <span>Similar:</span>
            {nameSuggestions.map((n, i) => (
              <span key={i} className="nb-similar-item-chip">
                {n}
              </span>
            ))}
          </div>
        )}

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
            <label className="nb-form-label">Category</label>
            <select
              className="nb-form-select"
              value={form.category}
              onChange={(e) =>
                set("category", e.target.value as ExpenseCategory)
              }
            >
              <option value="fixed">Fixed</option>
              <option value="variable">Variable</option>
            </select>
          </div>
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
        </div>

        <div className="nb-form-row">
          <div className="nb-form-group">
            <label className="nb-form-label">Start date</label>
            <input
              className="nb-form-input"
              type="date"
              value={form.reference_date}
              onChange={(e) => handleReferenceDateChange(e.target.value)}
            />
          </div>
          <div className="nb-form-group">
            <label className="nb-form-label">Payment method</label>
            <select
              className="nb-form-select"
              value={form.payment_method_id}
              onChange={(e) => set("payment_method_id", e.target.value)}
            >
              <option value="">— none —</option>
              {paymentMethods
                .filter((m) => m.active)
                .map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} — {m.method_type}
                  </option>
                ))}
            </select>
          </div>
        </div>

        <RecurrenceFields
          type={form.recurrence_type}
          config={form.recurrence_config}
          onChange={(c) => set("recurrence_config", c)}
        />

        <div className="nb-form-group">
          <label className="nb-form-label">Autopay</label>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              checked={form.autopay}
              onChange={(e) => set("autopay", e.target.checked)}
              style={{
                width: 18,
                height: 18,
                cursor: "pointer",
                accentColor: "var(--cover-bg)",
              }}
            />
            <span
              style={{
                fontFamily: "var(--font-hand)",
                fontSize: 14,
                color: "var(--ink-light)",
              }}
            >
              Enable automatic payment for this expense
            </span>
          </div>
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

type FilterType = "all" | "fixed" | "variable";

const BLANK_FORM: TemplateForm = {
  description: "",
  base_amount: "",
  currency: "USD",
  category: "fixed",
  recurrence_type: "monthly",
  recurrence_config: { day_of_month: 1 },
  reference_date: new Date().toISOString().split("T")[0],
  autopay: false,
  payment_method_id: "",
};

function templateToForm(t: RecurrentExpense): TemplateForm {
  return {
    description: t.description,
    base_amount: t.base_amount,
    currency: t.currency,
    category: t.category,
    recurrence_type: t.recurrence_type,
    recurrence_config: t.recurrence_config as Record<string, unknown>,
    reference_date: t.reference_date,
    autopay: t.autopay,
    payment_method_id: t.payment_method?.id ?? "",
  };
}

export function RecurrentExpenses() {
  const [templates, setTemplates] = useState<RecurrentExpense[]>([]);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterType>("all");
  const [addOpen, setAddOpen] = useState(false);
  const [addInitial, setAddInitial] = useState<TemplateForm>(BLANK_FORM);
  const [editTarget, setEditTarget] = useState<RecurrentExpense | null>(null);
  const [trashTarget, setTrashTarget] = useState<RecurrentExpense | null>(null);
  const [restoringId, setRestoringId] = useState<string | null>(null);
  const [restoreError, setRestoreError] = useState<string | null>(null);

  useEffect(() => {
    getCurrentUserAction().then(async (userRes) => {
      const admin = userRes.success && userRes.data.role === "admin";
      setIsAdmin(admin);
      const [tRes, mRes] = await Promise.all([
        getRecurrentExpenses(admin),
        getPaymentMethods(),
      ]);
      if (tRes.success) setTemplates(tRes.data);
      if (mRes.success) setPaymentMethods(mRes.data);
      setLoading(false);
    });
  }, []);

  const applyFilter = (list: RecurrentExpense[]) =>
    filter === "all" ? list : list.filter((t) => t.category === filter);

  const activeTemplates = applyFilter(templates.filter((t) => t.active));
  const trashedTemplates = applyFilter(templates.filter((t) => !t.active));
  const allActive = templates.filter((t) => t.active);
  const allTrashed = templates.filter((t) => !t.active);

  const handleTrashed = (id: string) => {
    setTemplates((prev) =>
      prev.map((t) => (t.id === id ? { ...t, active: false } : t)),
    );
    setTrashTarget(null);
  };

  const handleRestore = async (template: RecurrentExpense) => {
    setRestoringId(template.id);
    setRestoreError(null);
    const res = await activateRecurrentExpense(template.id);
    if (res.success) {
      setTemplates((prev) =>
        prev.map((t) => (t.id === template.id ? { ...t, active: true } : t)),
      );
    } else {
      setRestoreError(res.error.message);
    }
    setRestoringId(null);
  };

  const handleDuplicate = (template: RecurrentExpense) => {
    setAddInitial({
      ...templateToForm(template),
      description: `Copy of ${template.description}`,
    });
    setAddOpen(true);
  };

  const handleAdd = async (form: TemplateForm): Promise<string | null> => {
    const res = await addRecurrentExpense({
      description: form.description,
      base_amount: form.base_amount,
      currency: form.currency,
      category: form.category,
      recurrence_type: form.recurrence_type,
      recurrence_config: form.recurrence_config as RecurrenceConfig,
      reference_date: form.reference_date,
      autopay: form.autopay,
      payment_method_id: form.payment_method_id || null,
    });
    if (res.success) {
      setTemplates((prev) => [res.data, ...prev]);
      setAddOpen(false);
      return null;
    }
    return res.error.message;
  };

  const handleEdit = async (form: TemplateForm): Promise<string | null> => {
    if (!editTarget) return null;
    const res = await editRecurrentExpense(editTarget.id, {
      description: form.description,
      base_amount: form.base_amount,
      currency: form.currency,
      category: form.category,
      recurrence_type: form.recurrence_type,
      recurrence_config: form.recurrence_config as RecurrenceConfig,
      reference_date: form.reference_date,
      autopay: form.autopay,
      payment_method_id: form.payment_method_id || null,
    });
    if (res.success) {
      setTemplates((prev) =>
        prev.map((t) => (t.id === editTarget.id ? res.data : t)),
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
      <div className="nb-page-title">Recurrent Expenses</div>
      <div className="nb-page-subtitle">
        Recurring expenses that auto-populate new cycles
      </div>

      {/* Filter pills */}
      <div
        style={{
          display: "flex",
          gap: 8,
          marginBottom: 18,
          alignItems: "center",
        }}
      >
        {(["all", "fixed", "variable"] as FilterType[]).map((f) => (
          <button
            key={f}
            className={`nb-filter-pill${filter === f ? " nb-pill-selected" : ""}`}
            onClick={() => setFilter(f)}
          >
            {f === "all" ? "All" : f === "fixed" ? "📌 Fixed" : "🛒 Variable"}
          </button>
        ))}
        <span
          style={{
            fontFamily: "var(--font-hand)",
            fontSize: 13,
            color: "var(--ink-light)",
            opacity: 0.5,
            marginLeft: "auto",
          }}
        >
          {allActive.length} active
          {isAdmin && ` · ${allTrashed.length} trashed`}
        </span>
      </div>

      {/* Active templates */}
      {activeTemplates.length > 0 && (
        <>
          <div className="nb-section-title">✓ Active</div>
          {activeTemplates.map((t) => (
            <TemplateCard
              key={t.id}
              template={t}
              onEdit={setEditTarget}
              onDuplicate={handleDuplicate}
              onTrash={setTrashTarget}
            />
          ))}
        </>
      )}

      {templates.length === 0 && (
        <div className="nb-empty">
          <div className="nb-empty-icon">📋</div>
          <div className="nb-empty-text">
            No templates yet — add one to get started!
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
        + New Template
      </button>

      {/* Trashed section (admin only) */}
      {isAdmin && trashedTemplates.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <div
            className="nb-section-title"
            style={{ opacity: 0.55, marginBottom: 12 }}
          >
            🗑 Trashed Templates
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
          {trashedTemplates.map((t) => (
            <TrashedTemplateCard
              key={t.id}
              template={t}
              onRestore={handleRestore}
              restoring={restoringId === t.id}
            />
          ))}
        </div>
      )}

      {/* Add modal */}
      <TemplateModal
        isOpen={addOpen}
        title={
          addInitial.description && addInitial.description.startsWith("Copy of")
            ? "Duplicate Template"
            : "New Template"
        }
        initial={addInitial}
        paymentMethods={paymentMethods}
        onClose={() => setAddOpen(false)}
        onSave={handleAdd}
        existingNames={templates
          .filter((t) => t.active)
          .map((t) => t.description)}
      />

      {/* Edit modal */}
      <TemplateModal
        isOpen={!!editTarget}
        title="Edit Template"
        initial={editTarget ? templateToForm(editTarget) : BLANK_FORM}
        paymentMethods={paymentMethods}
        onClose={() => setEditTarget(null)}
        onSave={handleEdit}
      />

      {/* Confirm trash modal */}
      <ConfirmTrashModal
        isOpen={trashTarget !== null}
        onClose={() => setTrashTarget(null)}
        template={trashTarget}
        onConfirmed={handleTrashed}
      />
    </>
  );
}
