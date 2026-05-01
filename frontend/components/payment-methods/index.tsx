"use client";
import { useEffect, useState } from "react";
import type {
  PaymentMethod,
  PaymentMethodType,
  CurrencyCode,
} from "@/helpers/types";
import {
  getPaymentMethods,
  addPaymentMethod,
  editPaymentMethod,
  deactivatePaymentMethod,
  activatePaymentMethod,
} from "./actions";

// ── Icon/label maps ───────────────────────────────────────────────────────────

const METHOD_ICON: Record<PaymentMethodType, string> = {
  debit: "🏦",
  credit: "💳",
  cash: "💵",
  transfer: "🔁",
};

const METHOD_LABEL: Record<PaymentMethodType, string> = {
  debit: "Debit",
  credit: "Credit",
  cash: "Cash",
  transfer: "Transfer",
};

// ── Notebook action button ────────────────────────────────────────────────────

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

// ── Payment method card ───────────────────────────────────────────────────────

function PaymentCard({
  method,
  onEdit,
  onToggle,
  toggling,
}: {
  method: PaymentMethod;
  onEdit: (m: PaymentMethod) => void;
  onToggle: (m: PaymentMethod) => void;
  toggling: boolean;
}) {
  return (
    <div
      className="nb-payment-card"
      style={{ opacity: method.active ? 1 : 0.5 }}
    >
      <div
        style={{
          width: 44,
          height: 44,
          borderRadius: 10,
          background: "var(--stat-card-bg, rgba(44,74,62,0.08))",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          flexShrink: 0,
        }}
      >
        {METHOD_ICON[method.method_type]}
      </div>

      <div style={{ flex: 1 }}>
        <div
          style={{
            fontFamily: "var(--font-title)",
            fontSize: 18,
            fontWeight: 700,
            color: "var(--ink)",
          }}
        >
          {method.name}
        </div>
        <div
          style={{
            fontFamily: "var(--font-hand)",
            fontSize: 13,
            color: "var(--ink-light)",
            opacity: 0.65,
            display: "flex",
            gap: 8,
            marginTop: 2,
          }}
        >
          <span>{METHOD_LABEL[method.method_type]}</span>
          <span>·</span>
          <span>{method.default_currency}</span>
        </div>
      </div>

      <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
        <button style={iconBtn} onClick={() => onEdit(method)}>
          Edit
        </button>
        <button
          style={{
            ...iconBtn,
            ...(method.active
              ? { color: "var(--hl-overdue-border)" }
              : { color: "var(--hl-paid-border)" }),
          }}
          onClick={() => onToggle(method)}
          disabled={toggling}
        >
          {method.active ? "Deactivate" : "Activate"}
        </button>
      </div>
    </div>
  );
}

// ── Add / Edit Modal ──────────────────────────────────────────────────────────

interface MethodForm {
  name: string;
  method_type: PaymentMethodType;
  default_currency: CurrencyCode;
}

function MethodModal({
  isOpen,
  title,
  initial,
  onClose,
  onSave,
}: {
  isOpen: boolean;
  title: string;
  initial: MethodForm;
  onClose: () => void;
  onSave: (form: MethodForm) => Promise<string | null>;
}) {
  const [form, setForm] = useState<MethodForm>(initial);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setForm(initial);
      setError(null);
    }
  }, [isOpen, initial.name, initial.method_type, initial.default_currency]);

  const set = <K extends keyof MethodForm>(k: K, v: MethodForm[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async () => {
    if (!form.name.trim()) return;
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
      <div className="nb-modal">
        <button className="nb-modal-close" onClick={onClose}>
          ✕
        </button>
        <div className="nb-modal-title">{title}</div>

        <div className="nb-form-group">
          <label className="nb-form-label">Name</label>
          <input
            className="nb-form-input"
            placeholder="e.g. Chase Debit"
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
          />
        </div>

        <div className="nb-form-row">
          <div className="nb-form-group">
            <label className="nb-form-label">Type</label>
            <select
              className="nb-form-select"
              value={form.method_type}
              onChange={(e) =>
                set("method_type", e.target.value as PaymentMethodType)
              }
            >
              <option value="debit">Debit</option>
              <option value="credit">Credit</option>
              <option value="cash">Cash</option>
              <option value="transfer">Transfer</option>
            </select>
          </div>
          <div className="nb-form-group">
            <label className="nb-form-label">Currency</label>
            <select
              className="nb-form-select"
              value={form.default_currency}
              onChange={(e) =>
                set("default_currency", e.target.value as CurrencyCode)
              }
            >
              <option value="USD">USD</option>
              <option value="MXN">MXN</option>
            </select>
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

// ── Main component ────────────────────────────────────────────────────────────

export function PaymentMethods() {
  const [methods, setMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<PaymentMethod | null>(null);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  useEffect(() => {
    getPaymentMethods().then((res) => {
      if (res.success) setMethods(res.data);
      setLoading(false);
    });
  }, []);

  const active = methods.filter((m) => m.active);
  const inactive = methods.filter((m) => !m.active);

  const handleToggle = async (method: PaymentMethod) => {
    setTogglingId(method.id);
    const res = method.active
      ? await deactivatePaymentMethod(method.id)
      : await activatePaymentMethod(method.id);
    if (res.success) {
      setMethods((prev) =>
        prev.map((m) =>
          m.id === method.id ? { ...m, active: !method.active } : m,
        ),
      );
    }
    setTogglingId(null);
  };

  const handleAdd = async (form: MethodForm): Promise<string | null> => {
    const res = await addPaymentMethod(form);
    if (res.success) {
      setMethods((prev) => [res.data, ...prev]);
      setAddOpen(false);
      return null;
    }
    return res.error.message;
  };

  const handleEdit = async (form: MethodForm): Promise<string | null> => {
    if (!editTarget) return null;
    const res = await editPaymentMethod(editTarget.id, form);
    if (res.success) {
      setMethods((prev) =>
        prev.map((m) => (m.id === editTarget.id ? res.data : m)),
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
      <div className="nb-page-title">Payment Methods</div>
      <div className="nb-page-subtitle">
        Cards, accounts &amp; cash used for expenses
      </div>

      {/* Stats strip */}
      <div
        style={{ display: "flex", gap: 12, marginBottom: 24, flexWrap: "wrap" }}
      >
        {[
          { label: "Active methods", value: active.length },
          {
            label: "USD methods",
            value: active.filter((m) => m.default_currency === "USD").length,
          },
          {
            label: "MXN methods",
            value: active.filter((m) => m.default_currency === "MXN").length,
          },
        ].map((stat) => (
          <div key={stat.label} className="nb-payment-stat-card">
            <span className="nb-payment-stat-label">{stat.label}</span>
            <span className="nb-payment-stat-value">{stat.value}</span>
          </div>
        ))}
      </div>

      {/* Active methods */}
      {active.length > 0 && (
        <>
          <div className="nb-section-title">✓ Active</div>
          {active.map((m) => (
            <PaymentCard
              key={m.id}
              method={m}
              onEdit={setEditTarget}
              onToggle={handleToggle}
              toggling={togglingId === m.id}
            />
          ))}
        </>
      )}

      {/* Inactive methods */}
      {inactive.length > 0 && (
        <>
          <div className="nb-section-title" style={{ marginTop: 24 }}>
            ○ Inactive
          </div>
          {inactive.map((m) => (
            <PaymentCard
              key={m.id}
              method={m}
              onEdit={setEditTarget}
              onToggle={handleToggle}
              toggling={togglingId === m.id}
            />
          ))}
        </>
      )}

      {methods.length === 0 && (
        <div className="nb-empty">
          <div className="nb-empty-icon">💳</div>
          <div className="nb-empty-text">
            No payment methods yet — add one to get started!
          </div>
        </div>
      )}

      <button className="nb-add-btn" onClick={() => setAddOpen(true)}>
        + Add Payment Method
      </button>

      {/* Add modal */}
      <MethodModal
        isOpen={addOpen}
        title="Add Payment Method"
        initial={{ name: "", method_type: "debit", default_currency: "USD" }}
        onClose={() => setAddOpen(false)}
        onSave={handleAdd}
      />

      {/* Edit modal */}
      <MethodModal
        isOpen={!!editTarget}
        title="Edit Payment Method"
        initial={
          editTarget
            ? {
                name: editTarget.name,
                method_type: editTarget.method_type,
                default_currency: editTarget.default_currency,
              }
            : { name: "", method_type: "debit", default_currency: "USD" }
        }
        onClose={() => setEditTarget(null)}
        onSave={handleEdit}
      />
    </>
  );
}
