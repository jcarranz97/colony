"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import type {
  Cycle,
  CycleExpense,
  CycleIncome,
  CycleSummary,
  ExpenseStatus,
  PaymentMethod,
} from "@/helpers/types";
import {
  getCycle,
  getCurrentUserAction,
  fetchSummary,
  getExpenses,
  editExpense,
  getIncomes,
  removeIncome,
  restoreCycleAction,
} from "@/components/cycles/actions";
import { getPaymentMethods } from "@/components/payment-methods/actions";
import {
  CycleDetail,
  RenameCycleModal,
  ConfirmTrashModal,
} from "@/components/cycles";

export default function CycleDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [cycle, setCycle] = useState<Cycle | null>(null);
  const [expenses, setExpenses] = useState<CycleExpense[]>([]);
  const [incomes, setIncomes] = useState<CycleIncome[]>([]);
  const [summary, setSummary] = useState<CycleSummary | null>(null);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  const [renameOpen, setRenameOpen] = useState(false);
  const [trashOpen, setTrashOpen] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [restoreError, setRestoreError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      getCurrentUserAction(),
      getCycle(id),
      fetchSummary(id),
      getExpenses(id),
      getIncomes(id),
      getPaymentMethods(),
    ]).then(([userRes, cycleRes, sumRes, expRes, incRes, pmRes]) => {
      if (cancelled) return;
      if (userRes.success) setIsAdmin(userRes.data.role === "admin");
      if (cycleRes.success) setCycle(cycleRes.data);
      else setNotFound(true);
      if (sumRes.success) setSummary(sumRes.data);
      if (expRes.success) setExpenses(expRes.data.expenses);
      if (incRes.success) setIncomes(incRes.data);
      if (pmRes.success) setPaymentMethods(pmRes.data);
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const handleBack = () => {
    if (window.history.length > 1) router.back();
    else router.push("/cycles");
  };

  const refreshSummary = async () => {
    if (!cycle) return;
    const res = await fetchSummary(cycle.id);
    if (res.success) setSummary(res.data);
  };

  const handleStatusChange = async (
    expenseId: string,
    status: ExpenseStatus,
  ) => {
    if (!cycle) return;
    const expense = expenses.find((e) => e.id === expenseId);
    if (!expense) return;
    setExpenses((prev) =>
      prev.map((e) => (e.id === expenseId ? { ...e, status } : e)),
    );
    const res = await editExpense(cycle.id, expenseId, { status });
    if (!res.success) {
      setExpenses((prev) =>
        prev.map((e) =>
          e.id === expenseId ? { ...e, status: expense.status } : e,
        ),
      );
    } else {
      refreshSummary();
    }
  };

  const handleToggleExpense = async (expenseId: string) => {
    if (!cycle) return;
    const expense = expenses.find((e) => e.id === expenseId);
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
    setExpenses((prev) =>
      prev.map((e) => (e.id === expenseId ? { ...e, status: nextStatus } : e)),
    );
    const res = await editExpense(cycle.id, expenseId, { status: nextStatus });
    if (!res.success) {
      setExpenses((prev) =>
        prev.map((e) =>
          e.id === expenseId ? { ...e, status: expense.status } : e,
        ),
      );
    } else {
      refreshSummary();
    }
  };

  const handleExpenseAdded = (expense: CycleExpense) => {
    setExpenses((prev) => [...prev, expense]);
    refreshSummary();
  };

  const handleExpenseEdited = (updated: CycleExpense) => {
    setExpenses((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
    refreshSummary();
  };

  const handleIncomeAdded = (income: CycleIncome) => {
    setIncomes((prev) => [...prev, income]);
    refreshSummary();
  };

  const handleIncomeEdited = (updated: CycleIncome) => {
    setIncomes((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
    refreshSummary();
  };

  const handleIncomeRemoved = async (incomeId: string) => {
    if (!cycle) return;
    const res = await removeIncome(cycle.id, incomeId);
    if (res.success) {
      setIncomes((prev) => prev.filter((i) => i.id !== incomeId));
      refreshSummary();
    }
  };

  const handleRestore = async () => {
    if (!cycle) return;
    setRestoring(true);
    setRestoreError(null);
    const res = await restoreCycleAction(cycle.id);
    if (res.success) {
      setCycle(res.data);
    } else {
      setRestoreError(res.error.message);
    }
    setRestoring(false);
  };

  if (loading) {
    return (
      <div className="nb-empty">
        <div className="nb-empty-icon">📖</div>
        <div className="nb-empty-text">Loading cycle…</div>
      </div>
    );
  }

  if (notFound || !cycle) {
    return (
      <>
        <div className="nb-page-title">Cycle</div>
        <div className="nb-empty">
          <div className="nb-empty-icon">🔍</div>
          <div className="nb-empty-text">
            This cycle does not exist or you don&apos;t have access.
          </div>
          <button
            className="nb-btn-cancel"
            style={{ marginTop: 16 }}
            onClick={handleBack}
          >
            ← Back to Cycles
          </button>
        </div>
      </>
    );
  }

  const headerActions = (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-end",
        gap: 4,
      }}
    >
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {cycle.active ? (
          <>
            <button
              title="Rename cycle"
              style={{
                background: "transparent",
                border: "1px solid var(--ink-light)",
                borderRadius: 4,
                padding: "3px 10px",
                cursor: "pointer",
                fontFamily: "var(--font-hand)",
                fontSize: 12,
                color: "var(--ink-light)",
                opacity: 0.85,
              }}
              onClick={() => setRenameOpen(true)}
            >
              ✎ Rename
            </button>
            <button
              title="Move cycle to trash"
              style={{
                background: "transparent",
                border: "1px solid rgba(220,53,69,0.4)",
                borderRadius: 4,
                padding: "3px 10px",
                cursor: "pointer",
                fontFamily: "var(--font-hand)",
                fontSize: 12,
                color: "rgba(220,53,69,0.8)",
              }}
              onClick={() => setTrashOpen(true)}
            >
              🗑 Trash
            </button>
          </>
        ) : (
          isAdmin && (
            <button
              title="Restore cycle"
              style={{
                background: "transparent",
                border: "1px solid var(--hl-paid-border, rgba(80,200,100,0.6))",
                borderRadius: 4,
                padding: "3px 10px",
                cursor: "pointer",
                fontFamily: "var(--font-hand)",
                fontSize: 12,
                color: "var(--hl-paid-border, rgba(80,200,100,0.85))",
              }}
              onClick={handleRestore}
              disabled={restoring}
            >
              {restoring ? "Restoring…" : "↩ Restore"}
            </button>
          )
        )}
      </div>
      {restoreError && (
        <p
          style={{
            fontFamily: "var(--font-hand)",
            color: "var(--hl-overdue-border)",
            fontSize: 12,
            margin: 0,
          }}
        >
          {restoreError}
        </p>
      )}
    </div>
  );

  return (
    <>
      <CycleDetail
        cycle={cycle}
        expenses={expenses}
        incomes={incomes}
        summary={summary}
        paymentMethods={paymentMethods}
        headerActions={headerActions}
        onBack={handleBack}
        onToggleExpense={handleToggleExpense}
        onStatusChange={handleStatusChange}
        onExpenseAdded={handleExpenseAdded}
        onExpenseEdited={handleExpenseEdited}
        onIncomeAdded={handleIncomeAdded}
        onIncomeRemoved={handleIncomeRemoved}
        onIncomeEdited={handleIncomeEdited}
      />

      <RenameCycleModal
        isOpen={renameOpen}
        onClose={() => setRenameOpen(false)}
        cycle={cycle}
        onRenamed={(updated) => {
          setCycle(updated);
          setRenameOpen(false);
        }}
      />

      <ConfirmTrashModal
        isOpen={trashOpen}
        onClose={() => setTrashOpen(false)}
        cycle={cycle}
        onConfirmed={() => {
          setTrashOpen(false);
          router.push("/cycles");
        }}
      />
    </>
  );
}
