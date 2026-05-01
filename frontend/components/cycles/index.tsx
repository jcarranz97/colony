"use client";
import { useState, useEffect } from "react";
import type {
  Cycle,
  CycleExpense,
  CycleSummary,
  PaymentMethod,
  ExpenseStatus,
  CurrencyCode,
  ExpenseCategory,
} from "@/helpers/types";
import {
  getCycles,
  addCycle,
  fetchSummary,
  getExpenses,
  addExpense,
  editExpense,
} from "./actions";
import { getPaymentMethods } from "@/components/payment-methods/actions";

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
}: {
  cycle: Cycle;
  summary: CycleSummary | null;
  onOpen: (c: Cycle) => void;
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
        </div>
      </div>

      <div className="nb-cycle-footer">
        <div className="nb-cycle-stat">
          <span className="nb-stat-label">Income</span>
          <span className="nb-stat-value">
            {fmtAmount(cycle.income_amount ?? "0", "USD")}
          </span>
        </div>
        {summary && (
          <>
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
  onEdit,
}: {
  expense: CycleExpense;
  onToggle: (id: string) => void;
  onEdit: (expense: CycleExpense) => void;
}) {
  const statusCls =
    expense.status === "paid"
      ? "nb-paid"
      : expense.status === "overdue"
        ? "nb-overdue"
        : expense.status === "cancelled"
          ? "nb-cancelled"
          : "nb-pending";

  const checkCls =
    expense.status === "paid"
      ? "nb-check-paid"
      : expense.status === "overdue"
        ? "nb-check-overdue"
        : "nb-check-pending";

  return (
    <div
      className={`nb-expense-row ${statusCls}`}
      onClick={() => expense.status !== "cancelled" && onToggle(expense.id)}
    >
      <div className={`nb-expense-check ${checkCls}`}>
        {expense.status === "paid"
          ? "✓"
          : expense.status === "overdue"
            ? "!"
            : ""}
      </div>
      <div className="nb-expense-name">{expense.description}</div>
      {expense.payment_method && (
        <div className="nb-expense-method">{expense.payment_method.name}</div>
      )}
      {expense.due_date && (
        <div className="nb-expense-due">due {fmtDate(expense.due_date)}</div>
      )}
      <div className="nb-expense-amount">
        {fmtAmount(expense.amount, expense.currency)}
      </div>
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

// ── Add Cycle Modal ───────────────────────────────────────────────────────────

interface AddCycleForm {
  name: string;
  start_date: string;
  end_date: string;
  income_amount: string;
  generate_from_templates: boolean;
}

function AddCycleModal({
  isOpen,
  onClose,
  onAdd,
}: {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (c: Cycle) => void;
}) {
  const [form, setForm] = useState<AddCycleForm>({
    name: "",
    start_date: "",
    end_date: "",
    income_amount: "",
    generate_from_templates: true,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof AddCycleForm>(k: K, v: AddCycleForm[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async () => {
    if (!form.name || !form.start_date || !form.end_date || !form.income_amount)
      return;
    setSaving(true);
    setError(null);
    const res = await addCycle({
      name: form.name,
      start_date: form.start_date,
      end_date: form.end_date,
      income_amount: form.income_amount,
      generate_from_templates: form.generate_from_templates,
    });
    if (res.success) {
      onAdd(res.data);
      setForm({
        name: "",
        start_date: "",
        end_date: "",
        income_amount: "",
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

        <div className="nb-form-group">
          <label className="nb-form-label">Expected income (USD)</label>
          <input
            className="nb-form-input"
            type="number"
            placeholder="0.00"
            required
            value={form.income_amount}
            onChange={(e) => set("income_amount", e.target.value)}
          />
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
  category: ExpenseCategory;
  due_date: string;
  payment_method_id: string;
}

function AddExpenseModal({
  isOpen,
  onClose,
  cycleId,
  paymentMethods,
  onAdded,
}: {
  isOpen: boolean;
  onClose: () => void;
  cycleId: string;
  paymentMethods: PaymentMethod[];
  onAdded: (e: CycleExpense) => void;
}) {
  const [form, setForm] = useState<AddExpenseForm>({
    description: "",
    amount: "",
    currency: "USD",
    category: "fixed",
    due_date: "",
    payment_method_id: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof AddExpenseForm>(k: K, v: AddExpenseForm[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async () => {
    if (!form.description || !form.amount) return;
    setSaving(true);
    setError(null);
    const res = await addExpense(cycleId, {
      description: form.description,
      amount: form.amount,
      currency: form.currency,
      category: form.category,
      due_date: form.due_date || null,
      payment_method_id: form.payment_method_id || null,
    });
    if (res.success) {
      onAdded(res.data);
      setForm({
        description: "",
        amount: "",
        currency: "USD",
        category: "fixed",
        due_date: "",
        payment_method_id: "",
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
            <label className="nb-form-label">Due date</label>
            <input
              className="nb-form-input"
              type="date"
              value={form.due_date}
              onChange={(e) => set("due_date", e.target.value)}
            />
          </div>
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
                    {m.name}
                  </option>
                ))}
            </select>
          </div>
        )}

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

// ── Cycle Detail View ─────────────────────────────────────────────────────────

function CycleDetail({
  cycle,
  expenses,
  summary,
  paymentMethods,
  onBack,
  onToggleExpense,
  onExpenseAdded,
  onExpenseEdited,
}: {
  cycle: Cycle;
  expenses: CycleExpense[];
  summary: CycleSummary | null;
  paymentMethods: PaymentMethod[];
  onBack: () => void;
  onToggleExpense: (id: string) => void;
  onExpenseAdded: (e: CycleExpense) => void;
  onExpenseEdited: (updated: CycleExpense) => void;
}) {
  const [addExpenseOpen, setAddExpenseOpen] = useState(false);
  const [editExpenseOpen, setEditExpenseOpen] = useState(false);
  const [editingExpense, setEditingExpense] = useState<CycleExpense | null>(
    null,
  );

  const handleEditExpense = (expense: CycleExpense) => {
    setEditingExpense(expense);
    setEditExpenseOpen(true);
  };

  const fixedExp = expenses.filter((e) => e.category === "fixed");
  const varExp = expenses.filter((e) => e.category === "variable");

  const paid = expenses.filter((e) => e.status === "paid").length;
  const pending = expenses.filter((e) => e.status === "pending").length;
  const overdue = expenses.filter((e) => e.status === "overdue").length;

  const netBalance = summary ? parseFloat(summary.financial.net_balance) : 0;

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
        <div className="nb-summary-item">
          <span className="nb-summary-label">Income</span>
          <span className="nb-summary-value">
            {fmtAmount(cycle.income_amount ?? "0", "USD")}
          </span>
        </div>
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

      {/* Legend */}
      <div className="nb-legend">
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

      {fixedExp.length > 0 && (
        <>
          <div className="nb-section-title">📌 Fixed</div>
          {fixedExp.map((e) => (
            <ExpenseRow
              key={e.id}
              expense={e}
              onToggle={onToggleExpense}
              onEdit={handleEditExpense}
            />
          ))}
        </>
      )}

      {varExp.length > 0 && (
        <>
          <div className="nb-section-title">🛒 Variable</div>
          {varExp.map((e) => (
            <ExpenseRow
              key={e.id}
              expense={e}
              onToggle={onToggleExpense}
              onEdit={handleEditExpense}
            />
          ))}
        </>
      )}

      {expenses.length === 0 && (
        <div className="nb-empty">
          <div className="nb-empty-icon">📝</div>
          <div className="nb-empty-text">
            No expenses yet — add the first one!
          </div>
        </div>
      )}

      {cycle.status !== "completed" && (
        <button className="nb-add-btn" onClick={() => setAddExpenseOpen(true)}>
          + Add expense
        </button>
      )}

      <AddExpenseModal
        isOpen={addExpenseOpen}
        onClose={() => setAddExpenseOpen(false)}
        cycleId={cycle.id}
        paymentMethods={paymentMethods}
        onAdded={onExpenseAdded}
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
    </>
  );
}

// ── Main Cycles Component ─────────────────────────────────────────────────────

export function Cycles() {
  const [cycles, setCycles] = useState<Cycle[]>([]);
  const [summaries, setSummaries] = useState<Record<string, CycleSummary>>({});
  const [selectedCycle, setSelectedCycle] = useState<Cycle | null>(null);
  const [cycleExpenses, setCycleExpenses] = useState<CycleExpense[]>([]);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [expensesLoading, setExpensesLoading] = useState(false);
  const [addCycleOpen, setAddCycleOpen] = useState(false);

  useEffect(() => {
    Promise.all([getCycles(), getPaymentMethods()]).then(
      async ([cyclesRes, methodsRes]) => {
        if (methodsRes.success) setPaymentMethods(methodsRes.data);
        if (cyclesRes.success) {
          const loaded = cyclesRes.data.cycles;
          setCycles(loaded);
          const summaryResults = await Promise.all(
            loaded.map((c) =>
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
    getExpenses(selectedCycle.id).then((res) => {
      if (res.success) setCycleExpenses(res.data.expenses);
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

  const handleOpenCycle = (cycle: Cycle) => {
    setSelectedCycle(cycle);
    setCycleExpenses([]);
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
  };

  const handleToggleExpense = async (expenseId: string) => {
    if (!selectedCycle) return;
    const expense = cycleExpenses.find((e) => e.id === expenseId);
    if (!expense || expense.status === "cancelled") return;

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
        summary={summaries[selectedCycle.id] ?? null}
        paymentMethods={paymentMethods}
        onBack={handleBack}
        onToggleExpense={handleToggleExpense}
        onExpenseAdded={handleExpenseAdded}
        onExpenseEdited={handleExpenseEdited}
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
            />
          ))}
        </div>
      )}

      <button className="nb-add-btn" onClick={() => setAddCycleOpen(true)}>
        + New Cycle
      </button>

      <AddCycleModal
        isOpen={addCycleOpen}
        onClose={() => setAddCycleOpen(false)}
        onAdd={handleCycleAdded}
      />
    </>
  );
}
