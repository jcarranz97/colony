"use client";

import { formatDistanceToNow, parseISO } from "date-fns";
import { useEffect, useState } from "react";

import type {
  ActivityAction,
  ActivityChange,
  ActivityEntry,
  Comment as CommentType,
  CycleExpense,
  CycleIncome,
  EntityType,
  ExpenseStatus,
  UserResponse,
} from "@/helpers/types";

import {
  addComment,
  editComment,
  listActivityForCycle,
  listActivityForEntity,
  removeComment,
} from "./actions";
import { Markdown } from "./markdown";

export type FeedScope =
  | { kind: "entity"; entityType: EntityType; entityId: string }
  | { kind: "cycle"; cycleId: string };

export type FeedMode = "all" | "comments";

interface ActivityFeedProps {
  scope: FeedScope;
  /** Filter mode. Pair with <ActivityFilter> to let users toggle. */
  mode?: FeedMode;
  currentUser: UserResponse | null;
  /** Increment to force a refetch from the parent (e.g. after a write). */
  refreshKey?: number;
  /** Called when the user submits, edits, or deletes a comment. */
  onCommentMutated?: () => void;
  /**
   * Optional already-loaded cycle expenses/incomes used to hydrate the
   * "entity card" preview shown next to cycle_expense / cycle_income
   * activity rows. Falls back to no card when an id isn't in the list
   * (e.g. soft-deleted entities not in the active set).
   */
  expenses?: CycleExpense[];
  incomes?: CycleIncome[];
}

const EXPENSE_STATUS_LABEL: Record<ExpenseStatus, string> = {
  pending: "Pending",
  paid: "Paid",
  overdue: "Overdue",
  cancelled: "Cancelled",
  paid_other: "Paid (other)",
  skipped: "Skipped",
};

const EXPENSE_STATUS_CLASS: Record<ExpenseStatus, string> = {
  pending: "nb-pending",
  paid: "nb-paid",
  overdue: "nb-overdue",
  cancelled: "nb-cancelled",
  paid_other: "nb-paid-other",
  skipped: "nb-skipped",
};

function fmtMoney(amount: string, currency: string): string {
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
    }).format(parseFloat(amount));
  } catch {
    return `${amount} ${currency}`;
  }
}

function fmtShortDate(d: string | null): string {
  if (!d) return "—";
  const dt = new Date(`${d}T12:00:00`);
  return dt.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

const ACTION_LABEL: Record<ActivityAction, string> = {
  created: "created this",
  updated: "updated",
  deactivated: "deleted this",
  reactivated: "restored this",
  marked_paid: "marked as paid",
  marked_unpaid: "marked as unpaid",
  status_changed: "changed status",
  completed: "marked this cycle complete",
  commented: "commented",
  comment_edited: "edited a comment",
  comment_deleted: "deleted a comment",
};

function formatRelative(iso: string): string {
  try {
    // Backend BaseModel stores `created_at` as naive UTC and serializes
    // it without a `Z` suffix (e.g. "2026-05-11T06:30:00"). parseISO
    // would interpret a naive string as LOCAL time, which makes a fresh
    // UTC timestamp look hours in the future. Force-parse as UTC by
    // appending `Z` if the string has no timezone marker.
    const hasTz = /[zZ]|[+-]\d\d:?\d\d$/.test(iso);
    return formatDistanceToNow(parseISO(hasTz ? iso : `${iso}Z`), {
      addSuffix: true,
    });
  } catch {
    return iso;
  }
}

function isDiff(
  v: ActivityChange,
): v is { from: unknown; to: unknown } {
  return typeof v === "object" && v !== null && "from" in v && "to" in v;
}

function renderChanges(changes: Record<string, ActivityChange>): string | null {
  const keys = Object.keys(changes).filter((k) => k !== "comment_id");
  if (keys.length === 0) return null;
  return keys
    .map((k) => {
      const v = changes[k];
      if (isDiff(v)) {
        return `${k}: ${String(v.from ?? "—")} → ${String(v.to ?? "—")}`;
      }
      return `${k}: ${String(v)}`;
    })
    .join(", ");
}

export function ActivityFilter({
  mode,
  onChange,
}: {
  mode: FeedMode;
  onChange: (next: FeedMode) => void;
}) {
  return (
    <div className="nb-activity-filter">
      <button
        type="button"
        className={
          mode === "all" ? "nb-filter-pill nb-pill-selected" : "nb-filter-pill"
        }
        onClick={() => onChange("all")}
      >
        All activity
      </button>
      <button
        type="button"
        className={
          mode === "comments"
            ? "nb-filter-pill nb-pill-selected"
            : "nb-filter-pill"
        }
        onClick={() => onChange("comments")}
      >
        Comments only
      </button>
    </div>
  );
}

export function ActivityFeed({
  scope,
  mode = "all",
  currentUser,
  refreshKey = 0,
  onCommentMutated,
  expenses = [],
  incomes = [],
}: ActivityFeedProps) {
  const [entries, setEntries] = useState<ActivityEntry[]>([]);
  const [comments, setComments] = useState<CommentType[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingBody, setEditingBody] = useState("");

  const isCycleScope = scope.kind === "cycle";
  const entityType = scope.kind === "entity" ? scope.entityType : undefined;
  const entityId = scope.kind === "entity" ? scope.entityId : undefined;
  const cycleId = scope.kind === "cycle" ? scope.cycleId : undefined;

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const activityResponse =
        scope.kind === "entity"
          ? await listActivityForEntity(scope.entityType, scope.entityId)
          : await listActivityForCycle(scope.cycleId);
      if (cancelled) return;
      if (activityResponse.success) setEntries(activityResponse.data);

      // We still pull the comments separately so we can show the full body
      // and offer edit/delete actions inline. The activity row for
      // "commented" only contains a comment_id, not the body.
      const commentsModule = await import("./actions");
      const commentsResponse = await commentsModule.listComments(
        scope.kind === "entity"
          ? { entityType: scope.entityType, entityId: scope.entityId }
          : { cycleId: scope.cycleId },
      );
      if (cancelled) return;
      if (commentsResponse.success) setComments(commentsResponse.data);
      setLoading(false);
    };
    void load();
    return () => {
      cancelled = true;
    };
    // `scope` itself is intentionally NOT in the deps — it's an inline
    // object that gets a fresh reference on every parent render, which
    // would refetch the feed on every keystroke in sibling inputs. The
    // primitive fields below already cover every meaningful change.
    //
    // We also do NOT reset `loading` to true here — that's only true on
    // the initial mount. Refetches after refreshKey bumps swap the data
    // in place, leaving the prior entries on screen until the new ones
    // arrive (which avoids the "Loading activity…" flash on every save
    // or comment post).
  }, [scope.kind, entityType, entityId, cycleId, refreshKey]);

  const handleSaveEdit = async (id: string) => {
    if (!editingBody.trim()) return;
    const res = await editComment(id, { body: editingBody.trim() });
    if (res.success) {
      setComments((prev) => prev.map((c) => (c.id === id ? res.data : c)));
      setEditingId(null);
      setEditingBody("");
      onCommentMutated?.();
    }
  };

  const handleDelete = async (id: string) => {
    const res = await removeComment(id);
    if (res.success) {
      setComments((prev) => prev.filter((c) => c.id !== id));
      onCommentMutated?.();
    }
  };

  const showOnlyComments = mode === "comments";

  if (loading) {
    return <div className="nb-activity-empty">Loading activity…</div>;
  }

  // Merged timeline: index comments by id so "commented" rows render the body.
  const commentById = new Map(comments.map((c) => [c.id, c]));
  // Hydrate cycle_expense / cycle_income rows from the parent-provided lists.
  const expenseById = new Map(expenses.map((e) => [e.id, e]));
  const incomeById = new Map(incomes.map((i) => [i.id, i]));

  const filtered = showOnlyComments
    ? entries.filter((e) => e.action === "commented")
    : entries;

  if (filtered.length === 0) {
    return (
      <div className="nb-activity-empty">
        {showOnlyComments
          ? "No comments yet."
          : isCycleScope
            ? "No activity in this cycle yet."
            : "No activity yet."}
      </div>
    );
  }

  return (
    <div className="nb-activity-feed">
      {filtered.map((entry) => {
        const rawCommentId = entry.changes?.comment_id;
        const commentId =
          typeof rawCommentId === "string" ? rawCommentId : undefined;
        const comment = commentId ? commentById.get(commentId) : undefined;
        const isCommentEvent = entry.action === "commented" && comment;
        const isAuthor = comment && comment.author.id === currentUser?.id;
        const isAdmin = currentUser?.role === "admin";

        return (
          <div className="nb-activity-item" key={entry.id}>
            <div className="nb-activity-avatar">
              {entry.actor.username.slice(0, 1).toUpperCase()}
            </div>
            <div className="nb-activity-content">
              <div className="nb-activity-header">
                <strong>{entry.actor.username}</strong>{" "}
                <span>{ACTION_LABEL[entry.action] ?? entry.action}</span>
                {" · "}
                <span className="nb-activity-time">
                  {formatRelative(entry.created_at)}
                </span>
                {comment?.edited_at && (
                  <span className="nb-activity-edited"> (edited)</span>
                )}
              </div>

              {isCommentEvent && editingId === comment.id ? (
                <div className="nb-comment-edit">
                  <textarea
                    className="nb-comment-input"
                    value={editingBody}
                    onChange={(e) => setEditingBody(e.target.value)}
                  />
                  <div className="nb-modal-actions">
                    <button
                      className="nb-btn-cancel"
                      onClick={() => {
                        setEditingId(null);
                        setEditingBody("");
                      }}
                      type="button"
                    >
                      Cancel
                    </button>
                    <button
                      className="nb-btn-primary"
                      onClick={() => handleSaveEdit(comment.id)}
                      type="button"
                    >
                      Save
                    </button>
                  </div>
                </div>
              ) : isCommentEvent ? (
                <>
                  {entry.entity_type === "cycle_expense" &&
                    expenseById.get(entry.entity_id) && (
                      <ExpenseCard
                        expense={expenseById.get(entry.entity_id)!}
                      />
                    )}
                  {entry.entity_type === "cycle_income" &&
                    incomeById.get(entry.entity_id) && (
                      <IncomeCard income={incomeById.get(entry.entity_id)!} />
                    )}
                  <div className="nb-comment-body">
                    <Markdown source={comment.body} />
                  </div>
                  {(isAuthor || isAdmin) && (
                    <div className="nb-comment-actions">
                      {isAuthor && (
                        <button
                          className="nb-link-btn"
                          onClick={() => {
                            setEditingId(comment.id);
                            setEditingBody(comment.body);
                          }}
                          type="button"
                        >
                          Edit
                        </button>
                      )}
                      <button
                        className="nb-link-btn"
                        onClick={() => handleDelete(comment.id)}
                        type="button"
                      >
                        Delete
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <>
                  {entry.entity_type === "cycle_expense" &&
                    expenseById.get(entry.entity_id) && (
                      <ExpenseCard
                        expense={expenseById.get(entry.entity_id)!}
                      />
                    )}
                  {entry.entity_type === "cycle_income" &&
                    incomeById.get(entry.entity_id) && (
                      <IncomeCard income={incomeById.get(entry.entity_id)!} />
                    )}
                  <div className="nb-activity-changes">
                    {renderChanges(entry.changes)}
                  </div>
                </>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

const CATEGORY_ICON = {
  fixed: "🏠",
  variable: "🛒",
  extra: "🎁",
} as const;

function ExpenseCard({ expense }: { expense: CycleExpense }) {
  const icon = CATEGORY_ICON[expense.category] ?? "🧾";
  return (
    <div className={`nb-activity-card ${EXPENSE_STATUS_CLASS[expense.status]}`}>
      <div className="nb-activity-card-icon">{icon}</div>
      <div className="nb-activity-card-body">
        <div className="nb-activity-card-title">{expense.description}</div>
        <div className="nb-activity-card-meta">
          <span>{fmtMoney(expense.amount, expense.currency)}</span>
          <span> · </span>
          <span>Due {fmtShortDate(expense.due_date)}</span>
          <span> · </span>
          <span>{EXPENSE_STATUS_LABEL[expense.status]}</span>
        </div>
      </div>
    </div>
  );
}

function IncomeCard({ income }: { income: CycleIncome }) {
  return (
    <div className="nb-activity-card">
      <div className="nb-activity-card-icon">💰</div>
      <div className="nb-activity-card-body">
        <div className="nb-activity-card-title">{income.description}</div>
        <div className="nb-activity-card-meta">
          <span>{fmtMoney(income.amount, income.currency)}</span>
          <span> · </span>
          <span>{fmtShortDate(income.income_date)}</span>
        </div>
      </div>
    </div>
  );
}

interface CommentComposerProps {
  entityType: EntityType;
  entityId: string;
  onPosted?: () => void;
}

export function CommentComposer({
  entityType,
  entityId,
  onPosted,
}: CommentComposerProps) {
  const [body, setBody] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!body.trim()) return;
    setSubmitting(true);
    setError(null);
    const res = await addComment({
      entity_type: entityType,
      entity_id: entityId,
      body: body.trim(),
    });
    setSubmitting(false);
    if (res.success) {
      setBody("");
      onPosted?.();
    } else {
      setError(res.error.message);
    }
  };

  return (
    <div className="nb-comment-composer">
      <textarea
        className="nb-comment-input"
        placeholder="Add a comment… Markdown is supported."
        value={body}
        onChange={(e) => setBody(e.target.value)}
        rows={3}
      />
      {error && (
        <p className="nb-comment-error" role="alert">
          {error}
        </p>
      )}
      <div className="nb-modal-actions">
        <button
          className="nb-btn-primary"
          disabled={submitting || !body.trim()}
          onClick={handleSubmit}
          type="button"
        >
          {submitting ? "Posting…" : "Post comment"}
        </button>
      </div>
    </div>
  );
}
