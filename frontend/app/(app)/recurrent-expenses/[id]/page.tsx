"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import type {
  PaymentMethod,
  RecurrentExpense,
  RecurrenceConfig,
  RecurrenceType,
  UserResponse,
} from "@/helpers/types";
import { ActivityFeed, CommentComposer } from "@/components/activity";
import { formatPaymentMethodName } from "@/helpers/formatters";
import {
  getCurrentUserAction,
  getRecurrentExpense,
  addRecurrentExpense,
  editRecurrentExpense,
  activateRecurrentExpense,
} from "@/components/recurrent-expenses/actions";
import { getPaymentMethods } from "@/components/payment-methods/actions";
import {
  TemplateModal,
  ConfirmTrashModal,
  templateToForm,
  type TemplateForm,
} from "@/components/recurrent-expenses";

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

export default function RecurrentExpenseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [template, setTemplate] = useState<RecurrentExpense | null>(null);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [currentUser, setCurrentUser] = useState<UserResponse | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [duplicateOpen, setDuplicateOpen] = useState(false);
  const [trashOpen, setTrashOpen] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [restoreError, setRestoreError] = useState<string | null>(null);
  const [activityRefresh, setActivityRefresh] = useState(0);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      getCurrentUserAction(),
      getRecurrentExpense(id),
      getPaymentMethods(),
    ]).then(([userRes, tplRes, pmRes]) => {
      if (cancelled) return;
      if (userRes.success) {
        setIsAdmin(userRes.data.role === "admin");
        setCurrentUser(userRes.data);
      }
      if (tplRes.success) setTemplate(tplRes.data);
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
    else router.push("/recurrent-expenses");
  };

  const handleEditSave = async (form: TemplateForm): Promise<string | null> => {
    if (!template) return null;
    const res = await editRecurrentExpense(template.id, {
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
      setTemplate(res.data);
      setEditOpen(false);
      return null;
    }
    return res.error.message;
  };

  const handleDuplicateSave = async (
    form: TemplateForm,
  ): Promise<string | null> => {
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
      setDuplicateOpen(false);
      router.push(`/recurrent-expenses/${res.data.id}`);
      return null;
    }
    return res.error.message;
  };

  const handleRestore = async () => {
    if (!template) return;
    setRestoring(true);
    setRestoreError(null);
    const res = await activateRecurrentExpense(template.id);
    if (res.success) {
      setTemplate({ ...template, active: true });
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

  if (notFound || !template) {
    return (
      <>
        <div className="nb-page-title">Recurrent Expense</div>
        <div className="nb-empty">
          <div className="nb-empty-icon">🔍</div>
          <div className="nb-empty-text">
            This recurrent expense does not exist or you don&apos;t have access.
          </div>
          <button
            className="nb-btn-cancel"
            style={{ marginTop: 16 }}
            onClick={handleBack}
          >
            ← Back to Recurrent Expenses
          </button>
        </div>
      </>
    );
  }

  const isFixed = template.category === "fixed";

  return (
    <>
      <button className="nb-back-btn" onClick={handleBack}>
        ← Back to recurrent expenses
      </button>

      <div className="nb-page-title">{template.description}</div>
      <div className="nb-page-subtitle">Recurrent expense template</div>

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
            background: isFixed
              ? "var(--stat-card-bg, rgba(44,74,62,0.10))"
              : "var(--add-btn-hover, rgba(201,168,76,0.15))",
          }}
        >
          {isFixed ? "📌" : "🛒"}
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
            {fmtAmount(template.base_amount, template.currency)}
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
              className={`nb-template-badge ${isFixed ? "nb-badge-fixed" : "nb-badge-variable"}`}
            >
              {template.category}
            </span>
            {template.autopay && (
              <span className="nb-template-badge nb-badge-autopay">
                autopay
              </span>
            )}
            {!template.active && (
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
          {fmtRecurrence(template.recurrence_type, template.recurrence_config)}
        </div>
        <div>
          <strong>Start date:</strong> {template.reference_date}
        </div>
        {template.payment_method && (
          <div>
            <strong>Payment method:</strong>{" "}
            {formatPaymentMethodName(template.payment_method)}
          </div>
        )}
        <div>
          <strong>Autopay:</strong> {template.autopay ? "Yes ⚡" : "No"}
        </div>
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
        {template.active ? (
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

      <div className="nb-section-title" style={{ marginTop: 32 }}>
        Activity & Comments
      </div>
      <CommentComposer
        entityType="recurrent_expense"
        entityId={template.id}
        onPosted={() => setActivityRefresh((n) => n + 1)}
      />
      <ActivityFeed
        scope={{
          kind: "entity",
          entityType: "recurrent_expense",
          entityId: template.id,
        }}
        currentUser={currentUser}
        refreshKey={activityRefresh}
        onCommentMutated={() => setActivityRefresh((n) => n + 1)}
      />

      <TemplateModal
        isOpen={editOpen}
        title="Edit Template"
        initial={templateToForm(template)}
        paymentMethods={paymentMethods}
        onClose={() => setEditOpen(false)}
        onSave={handleEditSave}
      />

      <TemplateModal
        isOpen={duplicateOpen}
        title="Duplicate Template"
        initial={{
          ...templateToForm(template),
          description: `Copy of ${template.description}`,
        }}
        paymentMethods={paymentMethods}
        onClose={() => setDuplicateOpen(false)}
        onSave={handleDuplicateSave}
      />

      <ConfirmTrashModal
        isOpen={trashOpen}
        onClose={() => setTrashOpen(false)}
        template={template}
        onConfirmed={() => {
          setTrashOpen(false);
          router.push("/recurrent-expenses");
        }}
      />
    </>
  );
}
