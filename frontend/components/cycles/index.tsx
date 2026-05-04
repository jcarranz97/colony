"use client";
import { useState, useEffect } from "react";
import type {
  Cycle,
  CycleExpense,
  CycleIncome,
  CycleSummary,
  PaymentMethod,
  ExpenseStatus,
  CurrencyCode,
} from "@/helpers/types";
import {
  getCycles,
  addCycle,
  editCycle,
  removeCycle,
  restoreCycleAction,
  fetchSummary,
  getExpenses,
  addExpense,
  editExpense,
  getIncomes,
  addIncome,
  editIncome,
  removeIncome,
  getCurrentUserAction,
} from "./actions";
import { getPaymentMethods } from "@/components/payment-methods/actions";
import { formatPaymentMethodName } from "@/helpers/formatters";

// ── Helpers ──────────────────────────────────────────────────────────────────

function fmtAmount(amount: string | number, currency: string): string {
  const n = typeof amount === "string" ? parseFloat(amount) : amount;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(isNaN(n) ? 0 : n);
}

function fmtDate(d: string | null): string {
  if (!d) return "—";
  const dt = new Date(d + "T12:00:00");
  return dt.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function fmtDateRange(s: string, e: string): string {
  return `${fmtDate(s)} – ${fmtDate(e)}`;
}

// ── Status Pill ───────────────────────────────────────────────────────────────

function StatusPill({ status }: { status: string }) {
  const cls =
    status === "active"
      ? "nb-pill-active"
      : status === "completed"
        ? "nb-pill-completed"
        : "nb-pill-draft";
  return <span className={`nb-status-pill ${cls}`}>{status}</span>;
}

// ── Cycle Card ────────────────────────────────────────────────────────────────

function CycleCard({
  cycle,
  summary,
  onOpen,
  onRename,
  onTrash,
}: {
  cycle: Cycle;
  summary: CycleSummary | null;
  onOpen: (c: Cycle) => void;
  onRename: (c: Cycle) => void;
  onTrash: (c: Cycle) => void;
}) {
  const paid = summary?.status_breakdown.paid ?? 0;
  const overdue = summary?.status_breakdown.overdue ?? 0;
  const total = summary
    ? (summary.status_breakdown.paid ?? 0) +
      (summary.status_breakdown.pending ?? 0) +
      (summary.status_breakdown.overdue ?? 0) +
      (summary.status_breakdown.cancelled ?? 0)
    : 0;
  const pct = total > 0 ? Math.round((paid / total) * 100) : 0;
  const net = summary ? parseFloat(summary.financial.net_balance) : 0;

  return (
    <div
      className={`nb-cycle-card${cycle.status === "active" ? " nb-cycle-active" : ""}`}
    >
      <div className="nb-cycle-header">
        <div>
          <div className="nb-cycle-name">{cycle.name}</div>
          <div className="nb-cycle-dates">
            {fmtDateRange(cycle.start_date, cycle.end_date)}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
          <StatusPill status={cycle.status} />
          <button className="nb-open-btn" onClick={() => onOpen(cycle)}>
            Open →
          </button>
          <button
            title="Rename cycle"
            style={{
              background: "transparent",
              border: "1px solid var(--ink-light)",
              borderRadius: 4,
              padding: "3px 8px",
              cursor: "pointer",
              fontFamily: "var(--font-hand)",
              fontSize: 12,
              color: "var(--ink-light)",
              opacity: 0.7,
            }}
            onClick={(e) => {
              e.stopPropagation();
              onRename(cycle);
            }}
          >
            ✎
          </button>
          <button
            title="Move to trash"
            style={{
              background: "transparent",
              border: "1px solid rgba(220,53,69,0.4)",
              borderRadius: 4,
              padding: "3px 8px",
              cursor: "pointer",
              fontFamily: "var(--font-hand)",
              fontSize: 12,
              color: "rgba(220,53,69,0.7)",
            }}
            onClick={(e) => {
              e.stopPropagation();
              onTrash(cycle);
            }}
          >
            🗑
          </button>
        </div>
      </div>

      <div className="nb-cycle-footer">
        {summary && (
          <>
            <div className="nb-cycle-stat">
              <span className="nb-stat-label">Income</span>
              <span className="nb-stat-value nb-stat-positive">
                {fmtAmount(summary.financial.total_incomes_usd, "USD")}
              </span>
            </div>
            <div className="nb-cycle-stat">
              <span className="nb-stat-label">Expenses</span>
              <span className="nb-stat-value">
                {fmtAmount(summary.financial.total_expenses_usd, "USD")}
              </span>
            </div>
            <div className="nb-cycle-stat">
              <span className="nb-stat-label">Balance</span>
              <span
                className={`nb-stat-value ${net >= 0 ? "nb-stat-positive" : "nb-stat-negative"}`}
              >
                {fmtAmount(Math.abs(net).toString(), "USD")}
                {net < 0 ? " ↓" : " ↑"}
              </span>
            </div>
          </>
        )}
        <div className="nb-progress-wrap">
          <span className="nb-progress-label">
            {paid}/{total} paid · {pct}%
          </span>
          <div className="nb-progress-track">
            <div className="nb-progress-fill" style={{ width: `${pct}%` }} />
          </div>
        </div>
        {overdue > 0 && (
          <div className="nb-overdue-badge">⚠ {overdue} overdue</div>
        )}
      </div>
    </div>
  );
}

// ── Expense Row ───────────────────────────────────────────────────────────────

function ExpenseRow({
  expense,
  onToggle,
  onStatusChange,
  onEdit,
}: {
  expense: CycleExpense;
  onToggle: (id: string) => void;
  onStatusChange: (id: string, status: ExpenseStatus) => void;
  onEdit: (expense: CycleExpense) => void;
}) {
  const statusCls =
    expense.status === "paid"
      ? "nb-paid"
      : expense.status === "overdue"
        ? "nb-overdue"
        : expense.status === "cancelled"
          ? "nb-cancelled"
          : expense.status === "paid_other"
            ? "nb-paid-other"
            : expense.status === "skipped"
              ? "nb-skipped"
              : "nb-pending";

  const checkCls =
    expense.status === "paid"
      ? "nb-check-paid"
      : expense.status === "overdue"
        ? "nb-check-overdue"
        : expense.status === "paid_other"
          ? "nb-check-paid-other"
          : expense.status === "skipped"
            ? "nb-check-skipped"
            : "nb-check-pending";

  const checkIcon =
    expense.status === "paid"
      ? "✓"
      : expense.status === "overdue"
        ? "!"
        : expense.status === "paid_other"
          ? "~"
          : expense.status === "skipped"
            ? "—"
            : "";

  const isLocked =
    expense.status === "cancelled" ||
    expense.status === "paid_other" ||
    expense.status === "skipped";

  const handleOther = (e: React.MouseEvent) => {
    e.stopPropagation();
    const next: ExpenseStatus =
      expense.status === "paid_other" ? "pending" : "paid_other";
    onStatusChange(expense.id, next);
  };

  const handleSkip = (e: React.MouseEvent) => {
    e.stopPropagation();
    const next: ExpenseStatus =
      expense.status === "skipped" ? "pending" : "skipped";
    onStatusChange(expense.id, next);
  };

  return (
    <div
      className={`nb-expense-row ${statusCls}`}
      onClick={() => !isLocked && onToggle(expense.id)}
    >
      <div className={`nb-expense-check ${checkCls}`}>{checkIcon}</div>
      <div
        style={{
          width: 24,
          height: 24,
          borderRadius: "50%",
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background:
            expense.category === "fixed"
              ? "rgba(44,74,62,0.10)"
              : expense.category === "variable"
                ? "rgba(201,168,76,0.15)"
                : "rgba(70,130,180,0.12)",
          fontSize: 12,
        }}
      >
        {expense.category === "fixed"
          ? "📌"
          : expense.category === "variable"
            ? "🛒"
            : "✏️"}
      </div>
      <div className="nb-expense-name">{expense.description}</div>
      {expense.autopay && <div className="nb-expense-autopay">⚡ autopay</div>}
      {expense.payment_method && (
        <div className="nb-expense-method">
          {formatPaymentMethodName(expense.payment_method)}
        </div>
      )}
      {expense.due_date && (
        <div className="nb-expense-due">due {fmtDate(expense.due_date)}</div>
      )}
      <div className="nb-expense-amount">
        {fmtAmount(expense.amount, expense.currency)}
      </div>
      <div style={{ display: "flex", gap: 4, flexShrink: 0 }}>
        <span
          className={`nb-template-badge ${
            expense.category === "fixed"
              ? "nb-badge-fixed"
              : expense.category === "variable"
                ? "nb-badge-variable"
                : "nb-badge-extra"
          }`}
        >
          {expense.category}
        </span>
        {expense.autopay && (
          <span className="nb-template-badge nb-badge-autopay">autopay</span>
        )}
      </div>
      {expense.status !== "cancelled" && (
        <>
          <button
            className={`nb-expense-action-btn nb-btn-other${expense.status === "paid_other" ? " nb-btn-active" : ""}`}
            title={
              expense.status === "paid_other"
                ? "Revert to pending"
                : "Mark as paid by other"
            }
            onClick={handleOther}
          >
            Other
          </button>
          <button
            className={`nb-expense-action-btn nb-btn-skip${expense.status === "skipped" ? " nb-btn-active" : ""}`}
            title={expense.status === "skipped" ? "Revert to pending" : "Skip"}
            onClick={handleSkip}
          >
            Skip
          </button>
        </>
      )}
      <button
        className="nb-expense-edit-btn"
        title="Edit expense"
        onClick={(e) => {
          e.stopPropagation();
          onEdit(expense);
        }}
      >
        ✎
      </button>
    </div>
  );
}

// ── Edit Expense Modal ────────────────────────────────────────────────────────

interface EditExpenseForm {
  amount: string;
  due_date: string;
  comments: string;
}

function EditExpenseModal({
  isOpen,
  onClose,
  expense,
  cycleId,
  onEdited,
}: {
  isOpen: boolean;
  onClose: () => void;
  expense: CycleExpense | null;
  cycleId: string;
  onEdited: (updated: CycleExpense) => void;
}) {
  const [form, setForm] = useState<EditExpenseForm>({
    amount: "",
    due_date: "",
    comments: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (expense) {
      setForm({
        amount: expense.amount,
        due_date: expense.due_date ?? "",
        comments: "",
      });
      setError(null);
    }
  }, [expense]);

  const set = <K extends keyof EditExpenseForm>(k: K, v: EditExpenseForm[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async () => {
    if (!expense || !form.amount) return;
    setSaving(true);
    setError(null);
    const res = await editExpense(cycleId, expense.id, {
      amount: form.amount,
      due_date: form.due_date || null,
      comments: form.comments || null,
    });
    if (res.success) {
      onEdited(res.data);
      onClose();
    } else {
      setError(res.error.message);
    }
    setSaving(false);
  };

  if (!isOpen || !expense) return null;

  return (
    <div
      className="nb-modal-backdrop"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="nb-modal">
        <button className="nb-modal-close" onClick={onClose}>
          ✕
        </button>
        <div className="nb-modal-title">Edit Expense</div>
        <div
          style={{
            fontFamily: "var(--font-hand)",
            color: "var(--ink-light)",
            fontSize: 14,
            marginBottom: 12,
          }}
        >
          {expense.description}
        </div>

        <div className="nb-form-row">
          <div className="nb-form-group">
            <label className="nb-form-label">Amount ({expense.currency})</label>
            <input
              className="nb-form-input"
              type="number"
              placeholder="0.00"
              value={form.amount}
              onChange={(e) => set("amount", e.target.value)}
            />
          </div>
          <div className="nb-form-group">
            <label className="nb-form-label">Due date</label>
            <input
              className="nb-form-input"
              type="date"
              value={form.due_date}
              onChange={(e) => set("due_date", e.target.value)}
            />
          </div>
        </div>

        <div className="nb-form-group">
          <label className="nb-form-label">Comments</label>
          <textarea
            className="nb-form-input"
            placeholder="e.g. price increase this month…"
            rows={2}
            value={form.comments}
            onChange={(e) => set("comments", e.target.value)}
            style={{ resize: "vertical" }}
          />
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

// ── Edit Income Modal ─────────────────────────────────────────────────────────

interface EditIncomeForm {
  amount: string;
  income_date: string;
}

function EditIncomeModal({
  isOpen,
  onClose,
  income,
  cycleId,
  onEdited,
}: {
  isOpen: boolean;
  onClose: () => void;
  income: CycleIncome | null;
  cycleId: string;
  onEdited: (updated: CycleIncome) => void;
}) {
  const [form, setForm] = useState<EditIncomeForm>({
    amount: "",
    income_date: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (income) {
      setForm({ amount: income.amount, income_date: income.income_date ?? "" });
      setError(null);
    }
  }, [income]);

  const set = <K extends keyof EditIncomeForm>(k: K, v: EditIncomeForm[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async () => {
    if (!income || !form.amount) return;
    setSaving(true);
    setError(null);
    const res = await editIncome(cycleId, income.id, {
      amount: form.amount,
      income_date: form.income_date || undefined,
    });
    if (res.success) {
      onEdited(res.data);
      onClose();
    } else {
      setError(res.error.message);
    }
    setSaving(false);
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
        <div className="nb-modal-title">Edit Income</div>
        <div
          style={{
            fontFamily: "var(--font-hand)",
            color: "var(--ink-light)",
            fontSize: 14,
            marginBottom: 12,
          }}
        >
          {income.description}
        </div>
        <div className="nb-form-row">
          <div className="nb-form-group">
            <label className="nb-form-label">Amount ({income.currency})</label>
            <input
              className="nb-form-input"
              type="number"
              placeholder="0.00"
              value={form.amount}
              onChange={(e) => set("amount", e.target.value)}
            />
          </div>
          <div className="nb-form-group">
            <label className="nb-form-label">Income date</label>
            <input
              className="nb-form-input"
              type="date"
              value={form.income_date}
              onChange={(e) => set("income_date", e.target.value)}
            />
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

// ── Rename Cycle Modal ────────────────────────────────────────────────────────

function RenameCycleModal({
  isOpen,
  onClose,
  cycle,
  onRenamed,
}: {
  isOpen: boolean;
  onClose: () => void;
  cycle: Cycle | null;
  onRenamed: (updated: Cycle) => void;
}) {
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (cycle) {
      setName(cycle.name);
      setError(null);
    }
  }, [cycle]);

  const handleSubmit = async () => {
    if (!cycle || !name.trim()) return;
    setSaving(true);
    setError(null);
    const res = await editCycle(cycle.id, { name: name.trim() });
    if (res.success) {
      onRenamed(res.data);
      onClose();
    } else {
      setError(res.error.message);
    }
    setSaving(false);
  };

  if (!isOpen || !cycle) return null;

  return (
    <div
      className="nb-modal-backdrop"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="nb-modal">
        <button className="nb-modal-close" onClick={onClose}>
          ✕
        </button>
        <div className="nb-modal-title">Rename Cycle</div>
        <div className="nb-form-group">
          <label className="nb-form-label">Cycle name</label>
          <input
            className="nb-form-input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            autoFocus
          />
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

// ── Confirm Trash Modal ───────────────────────────────────────────────────────

function ConfirmTrashModal({
  isOpen,
  onClose,
  cycle,
  onConfirmed,
}: {
  isOpen: boolean;
  onClose: () => void;
  cycle: Cycle | null;
  onConfirmed: (cycleId: string) => void;
}) {
  const [trashing, setTrashing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) setError(null);
  }, [isOpen]);

  const handleConfirm = async () => {
    if (!cycle) return;
    setTrashing(true);
    setError(null);
    const res = await removeCycle(cycle.id);
    if (res.success) {
      onConfirmed(cycle.id);
      onClose();
    } else {
      setError(res.error.message);
    }
    setTrashing(false);
  };

  if (!isOpen || !cycle) return null;

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
          <strong>{cycle.name}</strong> will be deactivated and moved to trash.
          Regular users will no longer see it. Contact your admin if you need it
          restored.
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

// ── Add Cycle Modal ───────────────────────────────────────────────────────────

interface AddCycleForm {
  name: string;
  start_date: string;
  end_date: string;
  generate_from_templates: boolean;
}

function AddCycleModal({
  isOpen,
  onClose,
  onAdd,
  existingNames,
}: {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (c: Cycle) => void;
  existingNames: string[];
}) {
  const [form, setForm] = useState<AddCycleForm>({
    name: "",
    start_date: "",
    end_date: "",
    generate_from_templates: true,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof AddCycleForm>(k: K, v: AddCycleForm[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const nameSuggestions =
    form.name.trim().length > 0
      ? existingNames
          .filter((n) =>
            n.toLowerCase().includes(form.name.trim().toLowerCase()),
          )
          .slice(0, 5)
      : [];

  const handleSubmit = async () => {
    if (!form.name || !form.start_date || !form.end_date) return;
    setSaving(true);
    setError(null);
    const res = await addCycle({
      name: form.name,
      start_date: form.start_date,
      end_date: form.end_date,
      generate_from_templates: form.generate_from_templates,
    });
    if (res.success) {
      onAdd(res.data);
      setForm({
        name: "",
        start_date: "",
        end_date: "",
        generate_from_templates: true,
      });
      onClose();
    } else {
      setError(res.error.message);
    }
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
        <div className="nb-modal-title">New Cycle</div>

        <div className="nb-form-group">
          <label className="nb-form-label">Cycle name</label>
          <input
            className="nb-form-input"
            placeholder="e.g. June 2026"
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
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
            <label className="nb-form-label">Start date</label>
            <input
              className="nb-form-input"
              type="date"
              value={form.start_date}
              onChange={(e) => set("start_date", e.target.value)}
            />
          </div>
          <div className="nb-form-group">
            <label className="nb-form-label">End date</label>
            <input
              className="nb-form-input"
              type="date"
              value={form.end_date}
              onChange={(e) => set("end_date", e.target.value)}
            />
          </div>
        </div>

        <label className="nb-form-checkbox">
          <input
            type="checkbox"
            checked={form.generate_from_templates}
            onChange={(e) => set("generate_from_templates", e.target.checked)}
          />
          Auto-populate from active templates
        </label>

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
            {saving ? "Creating…" : "Create ✓"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Add Expense Modal ─────────────────────────────────────────────────────────

interface AddExpenseForm {
  description: string;
  amount: string;
  currency: CurrencyCode;
  due_date: string;
  payment_method_id: string;
  paid: boolean;
}

function AddExpenseModal({
  isOpen,
  onClose,
  cycleId,
  paymentMethods,
  onAdded,
  existingExpenses,
}: {
  isOpen: boolean;
  onClose: () => void;
  cycleId: string;
  paymentMethods: PaymentMethod[];
  onAdded: (e: CycleExpense) => void;
  existingExpenses: CycleExpense[];
}) {
  const [form, setForm] = useState<AddExpenseForm>({
    description: "",
    amount: "",
    currency: "USD",
    due_date: new Date().toISOString().split("T")[0],
    payment_method_id: "",
    paid: false,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof AddExpenseForm>(k: K, v: AddExpenseForm[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const descriptionSuggestions =
    form.description.trim().length > 0
      ? existingExpenses
          .filter((e) =>
            e.description
              .toLowerCase()
              .includes(form.description.trim().toLowerCase()),
          )
          .slice(0, 5)
          .map((e) => e.description)
      : [];

  const handleSubmit = async () => {
    if (!form.description || !form.amount) return;
    setSaving(true);
    setError(null);
    const res = await addExpense(cycleId, {
      description: form.description,
      amount: form.amount,
      currency: form.currency,
      due_date: form.due_date || null,
      payment_method_id: form.payment_method_id || null,
      paid: form.paid,
    });
    if (res.success) {
      onAdded(res.data);
      setForm({
        description: "",
        amount: "",
        currency: "USD",
        due_date: new Date().toISOString().split("T")[0],
        payment_method_id: "",
        paid: false,
      });
      onClose();
    } else {
      setError(res.error.message);
    }
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
        <div className="nb-modal-title">Add Expense</div>

        <div className="nb-form-group">
          <label className="nb-form-label">Description</label>
          <input
            className="nb-form-input"
            placeholder="e.g. Netflix subscription…"
            value={form.description}
            onChange={(e) => set("description", e.target.value)}
          />
        </div>

        {descriptionSuggestions.length > 0 && (
          <div className="nb-similar-items">
            <span>Similar:</span>
            {descriptionSuggestions.map((n, i) => (
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
              value={form.amount}
              onChange={(e) => set("amount", e.target.value)}
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

        <div className="nb-form-group">
          <label className="nb-form-label">Due date</label>
          <input
            className="nb-form-input"
            type="date"
            value={form.due_date}
            onChange={(e) => set("due_date", e.target.value)}
          />
        </div>

        {paymentMethods.length > 0 && (
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
                    {formatPaymentMethodName(m)}
                  </option>
                ))}
            </select>
          </div>
        )}

        <label className="nb-checkbox-label">
          <input
            type="checkbox"
            checked={form.paid}
            onChange={(e) => set("paid", e.target.checked)}
          />
          Already paid
        </label>

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
            {saving ? "Adding…" : "Add ✓"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Add Income Modal ──────────────────────────────────────────────────────────

interface AddIncomeForm {
  description: string;
  amount: string;
  currency: CurrencyCode;
  income_date: string;
  comments: string;
}

function AddIncomeModal({
  isOpen,
  onClose,
  cycleId,
  onAdded,
  existingIncomes,
}: {
  isOpen: boolean;
  onClose: () => void;
  cycleId: string;
  onAdded: (i: CycleIncome) => void;
  existingIncomes: CycleIncome[];
}) {
  const [form, setForm] = useState<AddIncomeForm>({
    description: "",
    amount: "",
    currency: "USD",
    income_date: "",
    comments: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof AddIncomeForm>(k: K, v: AddIncomeForm[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const descriptionSuggestions =
    form.description.trim().length > 0
      ? existingIncomes
          .filter((i) =>
            i.description
              .toLowerCase()
              .includes(form.description.trim().toLowerCase()),
          )
          .slice(0, 5)
          .map((i) => i.description)
      : [];

  const handleSubmit = async () => {
    if (!form.description || !form.amount || !form.income_date) return;
    setSaving(true);
    setError(null);
    const res = await addIncome(cycleId, {
      description: form.description,
      amount: form.amount,
      currency: form.currency,
      income_date: form.income_date,
      comments: form.comments || null,
    });
    if (res.success) {
      onAdded(res.data);
      setForm({
        description: "",
        amount: "",
        currency: "USD",
        income_date: "",
        comments: "",
      });
      onClose();
    } else {
      setError(res.error.message);
    }
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
        <div className="nb-modal-title">Add Income</div>

        <div className="nb-form-group">
          <label className="nb-form-label">Description</label>
          <input
            className="nb-form-input"
            placeholder="e.g. Freelance project…"
            value={form.description}
            onChange={(e) => set("description", e.target.value)}
          />
        </div>

        {descriptionSuggestions.length > 0 && (
          <div className="nb-similar-items">
            <span>Similar:</span>
            {descriptionSuggestions.map((n, i) => (
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
              value={form.amount}
              onChange={(e) => set("amount", e.target.value)}
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

        <div className="nb-form-group">
          <label className="nb-form-label">Income date</label>
          <input
            className="nb-form-input"
            type="date"
            value={form.income_date}
            onChange={(e) => set("income_date", e.target.value)}
          />
        </div>

        <div className="nb-form-group">
          <label className="nb-form-label">Comments (optional)</label>
          <textarea
            className="nb-form-input"
            placeholder="Any notes…"
            rows={2}
            value={form.comments}
            onChange={(e) => set("comments", e.target.value)}
            style={{ resize: "vertical" }}
          />
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
            {saving ? "Adding…" : "Add ✓"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Trashed Cycle Card (admin view) ──────────────────────────────────────────

function TrashedCycleCard({
  cycle,
  onRestore,
}: {
  cycle: Cycle;
  onRestore: (c: Cycle) => void;
}) {
  return (
    <div
      style={{
        border: "1px dashed rgba(180,180,180,0.5)",
        borderRadius: 6,
        padding: "12px 16px",
        background: "rgba(180,180,180,0.08)",
        opacity: 0.75,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
        }}
      >
        <div>
          <div
            style={{
              fontFamily: "var(--font-title)",
              fontSize: 17,
              color: "var(--ink)",
              textDecoration: "line-through",
              opacity: 0.6,
            }}
          >
            {cycle.name}
          </div>
          <div
            style={{
              fontFamily: "var(--font-hand)",
              fontSize: 12,
              color: "var(--ink-light)",
              opacity: 0.5,
              marginTop: 2,
            }}
          >
            {fmtDateRange(cycle.start_date, cycle.end_date)}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
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
            }}
            onClick={() => onRestore(cycle)}
          >
            ↩ Restore
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Cycle Detail View ─────────────────────────────────────────────────────────

function CycleDetail({
  cycle,
  expenses,
  incomes,
  summary,
  paymentMethods,
  onBack,
  onToggleExpense,
  onStatusChange,
  onExpenseAdded,
  onExpenseEdited,
  onIncomeAdded,
  onIncomeRemoved,
  onIncomeEdited,
}: {
  cycle: Cycle;
  expenses: CycleExpense[];
  incomes: CycleIncome[];
  summary: CycleSummary | null;
  paymentMethods: PaymentMethod[];
  onBack: () => void;
  onToggleExpense: (id: string) => void;
  onStatusChange: (id: string, status: ExpenseStatus) => void;
  onExpenseAdded: (e: CycleExpense) => void;
  onExpenseEdited: (updated: CycleExpense) => void;
  onIncomeAdded: (i: CycleIncome) => void;
  onIncomeRemoved: (id: string) => void;
  onIncomeEdited: (updated: CycleIncome) => void;
}) {
  const [addExpenseOpen, setAddExpenseOpen] = useState(false);
  const [editExpenseOpen, setEditExpenseOpen] = useState(false);
  const [editingExpense, setEditingExpense] = useState<CycleExpense | null>(
    null,
  );
  const [addIncomeOpen, setAddIncomeOpen] = useState(false);
  const [editIncomeOpen, setEditIncomeOpen] = useState(false);
  const [editingIncome, setEditingIncome] = useState<CycleIncome | null>(null);

  const handleEditExpense = (expense: CycleExpense) => {
    setEditingExpense(expense);
    setEditExpenseOpen(true);
  };

  const handleEditIncome = (income: CycleIncome) => {
    setEditingIncome(income);
    setEditIncomeOpen(true);
  };

  const fixedExp = expenses.filter((e) => e.category === "fixed");
  const varExp = expenses.filter((e) => e.category === "variable");

  const paid = expenses.filter((e) => e.status === "paid").length;
  const pending = expenses.filter((e) => e.status === "pending").length;
  const overdue = expenses.filter((e) => e.status === "overdue").length;

  const netBalance = summary ? parseFloat(summary.financial.net_balance) : 0;
  const totalIncomes = summary
    ? parseFloat(summary.financial.total_incomes_usd ?? "0")
    : 0;

  return (
    <>
      <div className="nb-detail-header">
        <div>
          <button className="nb-back-btn" onClick={onBack}>
            ← Back to cycles
          </button>
          <div className="nb-page-title" style={{ marginTop: 4 }}>
            {cycle.name}
          </div>
          <div className="nb-page-subtitle">
            {fmtDateRange(cycle.start_date, cycle.end_date)}
          </div>
        </div>
        <StatusPill status={cycle.status} />
      </div>

      {/* Summary strip */}
      <div className="nb-summary-strip">
        {summary && (
          <div className="nb-summary-item">
            <span className="nb-summary-label">Total income</span>
            <span className="nb-summary-value nb-stat-positive">
              {fmtAmount(summary.financial.total_incomes_usd, "USD")}
            </span>
          </div>
        )}
        <div className="nb-summary-item">
          <span className="nb-summary-label">Net balance</span>
          <span
            className={`nb-summary-value ${netBalance >= 0 ? "nb-stat-positive" : "nb-stat-negative"}`}
          >
            {fmtAmount(Math.abs(netBalance).toString(), "USD")}
            {netBalance < 0 ? " ↓" : " ↑"}
          </span>
        </div>
        <div className="nb-summary-item">
          <span className="nb-summary-label">Expenses</span>
          <span className="nb-summary-value">{expenses.length} items</span>
        </div>
        <div className="nb-summary-item">
          <span className="nb-summary-label">Status</span>
          <div className="nb-breakdown">
            <div className="nb-breakdown-item">
              <div
                className="nb-dot"
                style={{ background: "var(--hl-paid-border)" }}
              />
              {paid} paid
            </div>
            <div className="nb-breakdown-item">
              <div
                className="nb-dot"
                style={{ background: "var(--hl-pending-border)" }}
              />
              {pending} pending
            </div>
            {overdue > 0 && (
              <div className="nb-breakdown-item">
                <div
                  className="nb-dot"
                  style={{ background: "var(--hl-overdue-border)" }}
                />
                {overdue} overdue
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Incomes section */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 8,
          marginTop: 16,
        }}
      >
        <div className="nb-section-title" style={{ margin: 0 }}>
          💰 Incomes
        </div>
        {cycle.status !== "completed" && (
          <button
            style={{
              fontFamily: "var(--font-hand)",
              fontSize: 13,
              background: "transparent",
              border: "1px dashed var(--cover-bg)",
              borderRadius: 4,
              padding: "3px 10px",
              cursor: "pointer",
              color: "var(--cover-bg)",
            }}
            onClick={() => setAddIncomeOpen(true)}
          >
            + Add income
          </button>
        )}
      </div>

      {incomes.length > 0 ? (
        incomes.map((income) => (
          <div
            key={income.id}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "6px 10px",
              marginBottom: 4,
              borderRadius: 4,
              background: "rgba(80,200,100,0.10)",
              border: "1px solid rgba(80,200,100,0.25)",
              fontFamily: "var(--font-hand)",
            }}
          >
            <span style={{ fontSize: 14, color: "var(--ink)", flex: 1 }}>
              {income.description}
            </span>
            {income.template_id ? (
              <span
                style={{
                  fontSize: 11,
                  color: "var(--ink-light)",
                  opacity: 0.6,
                  background: "rgba(44,74,62,0.08)",
                  borderRadius: 3,
                  padding: "1px 5px",
                }}
              >
                recurring
              </span>
            ) : (
              <span
                style={{
                  fontSize: 11,
                  color: "var(--ink-light)",
                  opacity: 0.6,
                  background: "rgba(201,168,76,0.12)",
                  borderRadius: 3,
                  padding: "1px 5px",
                }}
              >
                manual
              </span>
            )}
            <span
              style={{ fontSize: 13, color: "var(--ink)", fontWeight: 700 }}
            >
              {fmtAmount(income.amount, income.currency)}
            </span>
            <span
              style={{ fontSize: 12, color: "var(--ink-light)", opacity: 0.55 }}
            >
              {fmtDate(income.income_date)}
            </span>
            {cycle.status !== "completed" && (
              <>
                <button
                  style={{
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                    color: "var(--ink-light)",
                    fontSize: 14,
                    padding: "0 4px",
                    opacity: 0.5,
                  }}
                  title="Edit income"
                  onClick={() => handleEditIncome(income)}
                >
                  ✎
                </button>
                <button
                  style={{
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                    color: "var(--ink-light)",
                    fontSize: 14,
                    padding: "0 4px",
                    opacity: 0.5,
                  }}
                  title="Remove income"
                  onClick={() => onIncomeRemoved(income.id)}
                >
                  ✕
                </button>
              </>
            )}
          </div>
        ))
      ) : (
        <div
          style={{
            fontFamily: "var(--font-hand)",
            fontSize: 13,
            color: "var(--ink-light)",
            opacity: 0.5,
            marginBottom: 12,
          }}
        >
          No incomes yet for this cycle
        </div>
      )}

      {/* Legend */}
      <div className="nb-legend" style={{ marginTop: 16 }}>
        <div className="nb-legend-item">
          <div className="nb-legend-swatch nb-swatch-paid" />
          Paid
        </div>
        <div className="nb-legend-item">
          <div className="nb-legend-swatch nb-swatch-pending" />
          Pending
        </div>
        <div className="nb-legend-item">
          <div className="nb-legend-swatch nb-swatch-overdue" />
          Overdue
        </div>
      </div>

      {/* Expenses section */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 8,
          marginTop: 16,
        }}
      >
        <div className="nb-section-title" style={{ margin: 0 }}>
          💸 Expenses
        </div>
        {cycle.status !== "completed" && (
          <button
            style={{
              fontFamily: "var(--font-hand)",
              fontSize: 13,
              background: "transparent",
              border: "1px dashed var(--cover-bg)",
              borderRadius: 4,
              padding: "3px 10px",
              cursor: "pointer",
              color: "var(--cover-bg)",
            }}
            onClick={() => setAddExpenseOpen(true)}
          >
            + Add expense
          </button>
        )}
      </div>

      {expenses.length > 0 ? (
        expenses.map((e) => (
          <ExpenseRow
            key={e.id}
            expense={e}
            onToggle={onToggleExpense}
            onStatusChange={onStatusChange}
            onEdit={handleEditExpense}
          />
        ))
      ) : (
        <div className="nb-empty">
          <div className="nb-empty-icon">📝</div>
          <div className="nb-empty-text">
            No expenses yet — add the first one!
          </div>
        </div>
      )}

      <AddIncomeModal
        isOpen={addIncomeOpen}
        onClose={() => setAddIncomeOpen(false)}
        cycleId={cycle.id}
        onAdded={onIncomeAdded}
        existingIncomes={incomes}
      />

      <AddExpenseModal
        isOpen={addExpenseOpen}
        onClose={() => setAddExpenseOpen(false)}
        cycleId={cycle.id}
        paymentMethods={paymentMethods}
        onAdded={onExpenseAdded}
        existingExpenses={expenses}
      />

      <EditExpenseModal
        isOpen={editExpenseOpen}
        onClose={() => {
          setEditExpenseOpen(false);
          setEditingExpense(null);
        }}
        expense={editingExpense}
        cycleId={cycle.id}
        onEdited={(updated) => {
          onExpenseEdited(updated);
          setEditExpenseOpen(false);
          setEditingExpense(null);
        }}
      />

      <EditIncomeModal
        isOpen={editIncomeOpen}
        onClose={() => {
          setEditIncomeOpen(false);
          setEditingIncome(null);
        }}
        income={editingIncome}
        cycleId={cycle.id}
        onEdited={(updated) => {
          onIncomeEdited(updated);
          setEditIncomeOpen(false);
          setEditingIncome(null);
        }}
      />
    </>
  );
}

// ── Main Cycles Component ─────────────────────────────────────────────────────

export function Cycles() {
  const [cycles, setCycles] = useState<Cycle[]>([]);
  const [trashedCycles, setTrashedCycles] = useState<Cycle[]>([]);
  const [summaries, setSummaries] = useState<Record<string, CycleSummary>>({});
  const [selectedCycle, setSelectedCycle] = useState<Cycle | null>(null);
  const [cycleExpenses, setCycleExpenses] = useState<CycleExpense[]>([]);
  const [cycleIncomes, setCycleIncomes] = useState<CycleIncome[]>([]);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [expensesLoading, setExpensesLoading] = useState(false);
  const [addCycleOpen, setAddCycleOpen] = useState(false);
  const [renameCycle, setRenameCycle] = useState<Cycle | null>(null);
  const [trashCycle, setTrashCycle] = useState<Cycle | null>(null);

  useEffect(() => {
    Promise.all([getPaymentMethods(), getCurrentUserAction()]).then(
      async ([methodsRes, userRes]) => {
        if (methodsRes.success) setPaymentMethods(methodsRes.data);
        const admin = userRes.success && userRes.data.role === "admin";
        setIsAdmin(admin);

        const cyclesRes = await getCycles(admin);
        if (cyclesRes.success) {
          const all = cyclesRes.data.cycles;
          const active = all.filter((c) => c.active);
          const trashed = all.filter((c) => !c.active);
          setCycles(active);
          if (admin) setTrashedCycles(trashed);

          const summaryResults = await Promise.all(
            active.map((c) =>
              fetchSummary(c.id).then((r) => ({ id: c.id, r })),
            ),
          );
          const map: Record<string, CycleSummary> = {};
          summaryResults.forEach(({ id, r }) => {
            if (r.success) map[id] = r.data;
          });
          setSummaries(map);
        }
        setLoading(false);
      },
    );
  }, []);

  useEffect(() => {
    if (!selectedCycle) return;
    setExpensesLoading(true);
    Promise.all([
      getExpenses(selectedCycle.id),
      getIncomes(selectedCycle.id),
    ]).then(([expRes, incRes]) => {
      if (expRes.success) setCycleExpenses(expRes.data.expenses);
      if (incRes.success) setCycleIncomes(incRes.data);
      setExpensesLoading(false);
    });
  }, [selectedCycle]);

  const handleCycleAdded = async (cycle: Cycle) => {
    setCycles((prev) => [cycle, ...prev]);
    const summaryRes = await fetchSummary(cycle.id);
    if (summaryRes.success) {
      setSummaries((prev) => ({ ...prev, [cycle.id]: summaryRes.data }));
    }
  };

  const handleCycleRenamed = (updated: Cycle) => {
    setCycles((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    if (selectedCycle?.id === updated.id) setSelectedCycle(updated);
    setRenameCycle(null);
  };

  const handleCycleTrashed = (cycleId: string) => {
    const trashed = cycles.find((c) => c.id === cycleId);
    setCycles((prev) => prev.filter((c) => c.id !== cycleId));
    if (trashed && isAdmin) {
      setTrashedCycles((prev) => [{ ...trashed, active: false }, ...prev]);
    }
    setTrashCycle(null);
  };

  const handleCycleRestored = async (cycle: Cycle) => {
    const res = await restoreCycleAction(cycle.id);
    if (res.success) {
      setTrashedCycles((prev) => prev.filter((c) => c.id !== cycle.id));
      setCycles((prev) => [res.data, ...prev]);
      const summaryRes = await fetchSummary(res.data.id);
      if (summaryRes.success) {
        setSummaries((prev) => ({ ...prev, [res.data.id]: summaryRes.data }));
      }
    }
  };

  const handleOpenCycle = (cycle: Cycle) => {
    setSelectedCycle(cycle);
    setCycleExpenses([]);
    setCycleIncomes([]);
  };

  const handleBack = () => {
    if (selectedCycle) {
      fetchSummary(selectedCycle.id).then((r) => {
        if (r.success)
          setSummaries((prev) => ({ ...prev, [selectedCycle.id]: r.data }));
      });
    }
    setSelectedCycle(null);
    setCycleExpenses([]);
    setCycleIncomes([]);
  };

  const handleStatusChange = async (
    expenseId: string,
    status: ExpenseStatus,
  ) => {
    if (!selectedCycle) return;
    const expense = cycleExpenses.find((e) => e.id === expenseId);
    if (!expense) return;

    setCycleExpenses((prev) =>
      prev.map((e) => (e.id === expenseId ? { ...e, status } : e)),
    );

    const res = await editExpense(selectedCycle.id, expenseId, { status });
    if (!res.success) {
      setCycleExpenses((prev) =>
        prev.map((e) =>
          e.id === expenseId ? { ...e, status: expense.status } : e,
        ),
      );
    } else {
      const summaryRes = await fetchSummary(selectedCycle.id);
      if (summaryRes.success) {
        setSummaries((prev) => ({
          ...prev,
          [selectedCycle.id]: summaryRes.data,
        }));
      }
    }
  };

  const handleToggleExpense = async (expenseId: string) => {
    if (!selectedCycle) return;
    const expense = cycleExpenses.find((e) => e.id === expenseId);
    if (
      !expense ||
      expense.status === "cancelled" ||
      expense.status === "paid_other" ||
      expense.status === "skipped"
    )
      return;

    const nextStatus: ExpenseStatus =
      expense.status === "pending" || expense.status === "overdue"
        ? "paid"
        : expense.status === "paid"
          ? "pending"
          : expense.status;

    setCycleExpenses((prev) =>
      prev.map((e) => (e.id === expenseId ? { ...e, status: nextStatus } : e)),
    );

    const res = await editExpense(selectedCycle.id, expenseId, {
      status: nextStatus,
    });
    if (!res.success) {
      setCycleExpenses((prev) =>
        prev.map((e) =>
          e.id === expenseId ? { ...e, status: expense.status } : e,
        ),
      );
    }
  };

  const handleExpenseAdded = (expense: CycleExpense) => {
    setCycleExpenses((prev) => [...prev, expense]);
  };

  const handleExpenseEdited = async (updated: CycleExpense) => {
    setCycleExpenses((prev) =>
      prev.map((e) => (e.id === updated.id ? updated : e)),
    );
    if (selectedCycle) {
      const summaryRes = await fetchSummary(selectedCycle.id);
      if (summaryRes.success) {
        setSummaries((prev) => ({
          ...prev,
          [selectedCycle.id]: summaryRes.data,
        }));
      }
    }
  };

  const handleIncomeEdited = async (updated: CycleIncome) => {
    setCycleIncomes((prev) =>
      prev.map((i) => (i.id === updated.id ? updated : i)),
    );
    if (selectedCycle) {
      const summaryRes = await fetchSummary(selectedCycle.id);
      if (summaryRes.success) {
        setSummaries((prev) => ({
          ...prev,
          [selectedCycle.id]: summaryRes.data,
        }));
      }
    }
  };

  const handleIncomeAdded = async (income: CycleIncome) => {
    setCycleIncomes((prev) => [...prev, income]);
    if (selectedCycle) {
      const summaryRes = await fetchSummary(selectedCycle.id);
      if (summaryRes.success) {
        setSummaries((prev) => ({
          ...prev,
          [selectedCycle.id]: summaryRes.data,
        }));
      }
    }
  };

  const handleIncomeRemoved = async (incomeId: string) => {
    if (!selectedCycle) return;
    const res = await removeIncome(selectedCycle.id, incomeId);
    if (res.success) {
      setCycleIncomes((prev) => prev.filter((i) => i.id !== incomeId));
      const summaryRes = await fetchSummary(selectedCycle.id);
      if (summaryRes.success) {
        setSummaries((prev) => ({
          ...prev,
          [selectedCycle.id]: summaryRes.data,
        }));
      }
    }
  };

  if (loading) {
    return (
      <div className="nb-empty">
        <div className="nb-empty-icon">📖</div>
        <div className="nb-empty-text">Loading cycles…</div>
      </div>
    );
  }

  if (selectedCycle) {
    return expensesLoading ? (
      <div className="nb-empty">
        <div className="nb-empty-icon">📖</div>
        <div className="nb-empty-text">Loading expenses…</div>
      </div>
    ) : (
      <CycleDetail
        cycle={selectedCycle}
        expenses={cycleExpenses}
        incomes={cycleIncomes}
        summary={summaries[selectedCycle.id] ?? null}
        paymentMethods={paymentMethods}
        onBack={handleBack}
        onToggleExpense={handleToggleExpense}
        onStatusChange={handleStatusChange}
        onExpenseAdded={handleExpenseAdded}
        onExpenseEdited={handleExpenseEdited}
        onIncomeAdded={handleIncomeAdded}
        onIncomeRemoved={handleIncomeRemoved}
        onIncomeEdited={handleIncomeEdited}
      />
    );
  }

  return (
    <>
      <div className="nb-page-title">Billing Cycles</div>
      <div className="nb-page-subtitle">
        Track your monthly budgets &amp; expenses
      </div>

      {cycles.length === 0 ? (
        <div className="nb-empty">
          <div className="nb-empty-icon">📅</div>
          <div className="nb-empty-text">
            No cycles yet — create the first one!
          </div>
        </div>
      ) : (
        <div className="nb-cycles-grid">
          {cycles.map((c) => (
            <CycleCard
              key={c.id}
              cycle={c}
              summary={summaries[c.id] ?? null}
              onOpen={handleOpenCycle}
              onRename={setRenameCycle}
              onTrash={setTrashCycle}
            />
          ))}
        </div>
      )}

      <button className="nb-add-btn" onClick={() => setAddCycleOpen(true)}>
        + New Cycle
      </button>

      {isAdmin && trashedCycles.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <div
            className="nb-section-title"
            style={{ opacity: 0.55, marginBottom: 12 }}
          >
            🗑 Trashed Cycles
          </div>
          <div className="nb-cycles-grid">
            {trashedCycles.map((c) => (
              <TrashedCycleCard
                key={c.id}
                cycle={c}
                onRestore={handleCycleRestored}
              />
            ))}
          </div>
        </div>
      )}

      <AddCycleModal
        isOpen={addCycleOpen}
        onClose={() => setAddCycleOpen(false)}
        onAdd={handleCycleAdded}
        existingNames={cycles.map((c) => c.name)}
      />

      <RenameCycleModal
        isOpen={renameCycle !== null}
        onClose={() => setRenameCycle(null)}
        cycle={renameCycle}
        onRenamed={handleCycleRenamed}
      />

      <ConfirmTrashModal
        isOpen={trashCycle !== null}
        onClose={() => setTrashCycle(null)}
        cycle={trashCycle}
        onConfirmed={handleCycleTrashed}
      />
    </>
  );
}
