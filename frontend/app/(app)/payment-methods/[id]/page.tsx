"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import type {
  PaymentMethod,
  PaymentMethodType,
  UserResponse,
} from "@/helpers/types";
import { formatPaymentMethodName } from "@/helpers/formatters";
import {
  getCurrentUserAction,
  getPaymentMethod,
  editPaymentMethod,
  activatePaymentMethod,
} from "@/components/payment-methods/actions";
import {
  MethodModal,
  ConfirmTrashModal,
  type MethodForm,
} from "@/components/payment-methods";
import {
  ActivityFeed,
  ActivityFilter,
  CommentComposer,
} from "@/components/activity";

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

export default function PaymentMethodDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [method, setMethod] = useState<PaymentMethod | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [currentUser, setCurrentUser] = useState<UserResponse | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [trashOpen, setTrashOpen] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [restoreError, setRestoreError] = useState<string | null>(null);
  const [activityRefresh, setActivityRefresh] = useState(0);
  const [activityMode, setActivityMode] = useState<"all" | "comments">("all");

  useEffect(() => {
    let cancelled = false;
    Promise.all([getCurrentUserAction(), getPaymentMethod(id)]).then(
      ([userRes, methodRes]) => {
        if (cancelled) return;
        if (userRes.success) {
          setIsAdmin(userRes.data.role === "admin");
          setCurrentUser(userRes.data);
        }
        if (methodRes.success) setMethod(methodRes.data);
        else setNotFound(true);
        setLoading(false);
      },
    );
    return () => {
      cancelled = true;
    };
  }, [id]);

  const handleBack = () => {
    if (window.history.length > 1) router.back();
    else router.push("/payment-methods");
  };

  const handleEditSave = async (form: MethodForm): Promise<string | null> => {
    if (!method) return null;
    const payload = {
      ...form,
      last_4_digits: form.last_4_digits.trim() || null,
    };
    const res = await editPaymentMethod(method.id, payload);
    if (res.success) {
      setMethod(res.data);
      setEditOpen(false);
      return null;
    }
    return res.error.message;
  };

  const handleRestore = async () => {
    if (!method) return;
    setRestoring(true);
    setRestoreError(null);
    const res = await activatePaymentMethod(method.id);
    if (res.success) {
      setMethod({ ...method, active: true });
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

  if (notFound || !method) {
    return (
      <>
        <div className="nb-page-title">Payment Method</div>
        <div className="nb-empty">
          <div className="nb-empty-icon">🔍</div>
          <div className="nb-empty-text">
            This payment method does not exist or you don&apos;t have access.
          </div>
          <button
            className="nb-btn-cancel"
            style={{ marginTop: 16 }}
            onClick={handleBack}
          >
            ← Back to Payment Methods
          </button>
        </div>
      </>
    );
  }

  return (
    <>
      <button className="nb-back-btn" onClick={handleBack}>
        ← Back to payment methods
      </button>

      <div className="nb-page-title">{formatPaymentMethodName(method)}</div>
      <div className="nb-page-subtitle">Payment method details</div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          marginBottom: 24,
          padding: "16px 18px",
          border: "1px solid var(--paper-line, rgba(140,140,140,0.25))",
          borderRadius: 8,
          background: "var(--paper-bg, transparent)",
        }}
      >
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: 12,
            background: "var(--stat-card-bg, rgba(44,74,62,0.08))",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 28,
            flexShrink: 0,
          }}
        >
          {METHOD_ICON[method.method_type]}
        </div>
        <div style={{ flex: 1 }}>
          <div
            style={{
              fontFamily: "var(--font-hand)",
              fontSize: 13,
              color: "var(--ink-light)",
              opacity: 0.7,
            }}
          >
            {METHOD_LABEL[method.method_type]} · {method.default_currency}
            {method.last_4_digits ? ` · •••• ${method.last_4_digits}` : ""}
          </div>
          {!method.active && (
            <span
              style={{
                display: "inline-block",
                marginTop: 6,
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
          <strong>Name:</strong> {method.name}
        </div>
        <div>
          <strong>Type:</strong> {METHOD_LABEL[method.method_type]}
        </div>
        <div>
          <strong>Default currency:</strong> {method.default_currency}
        </div>
        {method.last_4_digits && (
          <div>
            <strong>Last 4 digits:</strong> {method.last_4_digits}
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
        {method.active ? (
          <>
            <button
              className="nb-btn-primary"
              onClick={() => setEditOpen(true)}
            >
              Edit
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
      <ActivityFilter mode={activityMode} onChange={setActivityMode} />
      <CommentComposer
        entityType="payment_method"
        entityId={method.id}
        onPosted={() => setActivityRefresh((n) => n + 1)}
      />
      <ActivityFeed
        scope={{
          kind: "entity",
          entityType: "payment_method",
          entityId: method.id,
        }}
        mode={activityMode}
        currentUser={currentUser}
        refreshKey={activityRefresh}
        onCommentMutated={() => setActivityRefresh((n) => n + 1)}
      />

      <MethodModal
        isOpen={editOpen}
        title="Edit Payment Method"
        initial={{
          name: method.name,
          method_type: method.method_type,
          default_currency: method.default_currency,
          last_4_digits: method.last_4_digits ?? "",
        }}
        onClose={() => setEditOpen(false)}
        onSave={handleEditSave}
      />

      <ConfirmTrashModal
        isOpen={trashOpen}
        onClose={() => setTrashOpen(false)}
        method={method}
        onConfirmed={() => {
          setTrashOpen(false);
          router.push("/payment-methods");
        }}
      />
    </>
  );
}
