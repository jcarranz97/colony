"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import type {
  HouseholdResponse,
  HouseholdMemberResponse,
} from "@/helpers/types";
import {
  listHouseholdsAction,
  createHouseholdAction,
  getHouseholdMembersAction,
  addHouseholdMemberAction,
  removeHouseholdMemberAction,
} from "./actions";

// ── Member panel ──────────────────────────────────────────────────────────────

export function MemberPanel({
  household,
  onClose,
}: {
  household: HouseholdResponse;
  onClose: () => void;
}) {
  const [members, setMembers] = useState<HouseholdMemberResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [addUserId, setAddUserId] = useState("");
  const [addError, setAddError] = useState<string | null>(null);
  const [addLoading, setAddLoading] = useState(false);

  const loadMembers = async () => {
    setLoading(true);
    const res = await getHouseholdMembersAction(household.id);
    if (res.success) setMembers(res.data);
    setLoading(false);
  };

  useEffect(() => {
    loadMembers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [household.id]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddError(null);
    setAddLoading(true);
    const res = await addHouseholdMemberAction(household.id, {
      user_id: addUserId.trim(),
    });
    setAddLoading(false);
    if (res.success) {
      setAddUserId("");
      loadMembers();
    } else {
      setAddError(res.error.message);
    }
  };

  const handleRemove = async (userId: string) => {
    await removeHouseholdMemberAction(household.id, userId);
    loadMembers();
  };

  const displayName = (m: HouseholdMemberResponse) => {
    const parts = [m.first_name, m.last_name].filter(Boolean);
    return parts.length > 0 ? parts.join(" ") : m.username;
  };

  return (
    <div className="nb-modal-backdrop" onClick={onClose}>
      <div className="nb-modal" onClick={(e) => e.stopPropagation()}>
        <h2 className="nb-modal-title">Members — {household.name}</h2>

        {loading && (
          <p
            style={{
              fontFamily: "var(--font-hand)",
              color: "var(--ink-light)",
            }}
          >
            Loading…
          </p>
        )}

        {members.map((m) => (
          <div
            key={m.id}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "6px 0",
              borderBottom: "1px solid rgba(0,0,0,0.06)",
            }}
          >
            <div
              style={{ flex: 1, fontFamily: "var(--font-hand)", fontSize: 15 }}
            >
              {displayName(m)}
              <span
                style={{
                  marginLeft: 6,
                  fontSize: "0.75em",
                  color: "var(--ink-light)",
                }}
              >
                @{m.username}
              </span>
            </div>
            <button
              className="nb-btn-cancel"
              style={{ fontSize: "0.8em" }}
              onClick={() => handleRemove(m.id)}
            >
              Remove
            </button>
          </div>
        ))}

        {!loading && members.length === 0 && (
          <p className="nb-empty" style={{ padding: "12px 0" }}>
            No members yet.
          </p>
        )}

        <div
          className="nb-section-title"
          style={{ marginTop: 16, marginBottom: 8, fontSize: 13 }}
        >
          Add Member by User ID
        </div>
        <form onSubmit={handleAdd}>
          <div className="nb-form-group">
            <label className="nb-form-label">User ID (UUID)</label>
            <input
              className="nb-form-input"
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              value={addUserId}
              onChange={(e) => setAddUserId(e.target.value)}
              required
            />
          </div>
          {addError && (
            <p style={{ color: "red", fontSize: "0.85em" }}>{addError}</p>
          )}
          <div className="nb-modal-actions">
            <button type="button" className="nb-btn-cancel" onClick={onClose}>
              Close
            </button>
            <button
              type="submit"
              className="nb-btn-primary"
              disabled={addLoading}
            >
              {addLoading ? "Adding…" : "Add"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function HouseholdsManager() {
  const [households, setHouseholds] = useState<HouseholdResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showCreate, setShowCreate] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createError, setCreateError] = useState<string | null>(null);
  const [createLoading, setCreateLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    const res = await listHouseholdsAction();
    if (res.success) {
      setHouseholds(res.data);
    } else {
      setError(res.error.message);
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    setCreateLoading(true);
    const res = await createHouseholdAction({ name: createName.trim() });
    setCreateLoading(false);
    if (res.success) {
      setShowCreate(false);
      setCreateName("");
      load();
    } else {
      setCreateError(res.error.message);
    }
  };

  return (
    <div>
      <h1 className="nb-page-title">Households</h1>
      <p className="nb-page-subtitle">Manage households and their members</p>

      <button className="nb-add-btn" onClick={() => setShowCreate(true)}>
        + Add Household
      </button>

      {loading && <p className="nb-empty">Loading households…</p>}
      {error && (
        <p className="nb-empty" style={{ color: "red" }}>
          {error}
        </p>
      )}
      {!loading && households.length === 0 && (
        <p className="nb-empty">No households found.</p>
      )}

      {households.map((h) => (
        <Link
          key={h.id}
          href={`/households/${h.id}`}
          className="nb-payment-card"
          style={{
            textDecoration: "none",
            color: "inherit",
            cursor: "pointer",
          }}
        >
          <div style={{ flex: 1 }}>
            <strong>{h.name}</strong>
            {!h.active && (
              <span
                style={{
                  marginLeft: 8,
                  fontSize: "0.75em",
                  padding: "2px 6px",
                  borderRadius: 4,
                  background: "rgba(240,80,70,0.15)",
                  color: "#c0392b",
                  fontWeight: 600,
                }}
              >
                INACTIVE
              </span>
            )}
          </div>
          <span
            style={{
              fontFamily: "var(--font-hand)",
              fontSize: 12,
              fontWeight: 600,
              color: "var(--ink-light)",
              pointerEvents: "none",
            }}
          >
            Open →
          </span>
        </Link>
      ))}

      {/* Create modal */}
      {showCreate && (
        <div className="nb-modal-backdrop">
          <div className="nb-modal">
            <h2 className="nb-modal-title">Create Household</h2>
            <form onSubmit={handleCreate}>
              <div className="nb-form-group">
                <label className="nb-form-label">Name *</label>
                <input
                  className="nb-form-input"
                  value={createName}
                  onChange={(e) => setCreateName(e.target.value)}
                  required
                  maxLength={100}
                />
              </div>
              {createError && (
                <p style={{ color: "red", fontSize: "0.85em" }}>
                  {createError}
                </p>
              )}
              <div className="nb-modal-actions">
                <button
                  type="button"
                  className="nb-btn-cancel"
                  onClick={() => {
                    setShowCreate(false);
                    setCreateName("");
                    setCreateError(null);
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="nb-btn-primary"
                  disabled={createLoading}
                >
                  {createLoading ? "Creating…" : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
