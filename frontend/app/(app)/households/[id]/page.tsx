"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import type { HouseholdResponse } from "@/helpers/types";
import {
  getHouseholdAction,
  updateHouseholdAction,
  deleteHouseholdAction,
} from "@/components/households/actions";
import { MemberPanel } from "@/components/households";

export default function HouseholdDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [household, setHousehold] = useState<HouseholdResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const [editOpen, setEditOpen] = useState(false);
  const [editName, setEditName] = useState("");
  const [editError, setEditError] = useState<string | null>(null);
  const [editLoading, setEditLoading] = useState(false);

  const [membersOpen, setMembersOpen] = useState(false);
  const [deactivating, setDeactivating] = useState(false);
  const [deactivateError, setDeactivateError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getHouseholdAction(id).then((res) => {
      if (cancelled) return;
      if (res.success) setHousehold(res.data);
      else setNotFound(true);
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const handleBack = () => {
    if (window.history.length > 1) router.back();
    else router.push("/households");
  };

  const openEdit = () => {
    if (!household) return;
    setEditName(household.name);
    setEditError(null);
    setEditOpen(true);
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!household) return;
    setEditError(null);
    setEditLoading(true);
    const res = await updateHouseholdAction(household.id, {
      name: editName.trim(),
    });
    setEditLoading(false);
    if (res.success) {
      setHousehold(res.data);
      setEditOpen(false);
    } else {
      setEditError(res.error.message);
    }
  };

  const handleDeactivate = async () => {
    if (!household) return;
    setDeactivating(true);
    setDeactivateError(null);
    const res = await deleteHouseholdAction(household.id);
    setDeactivating(false);
    if (res.success) {
      router.push("/households");
    } else {
      setDeactivateError(res.error.message);
    }
  };

  if (loading) {
    return (
      <div className="nb-empty">
        <div className="nb-empty-icon">📖</div>
        <div className="nb-empty-text">Loading…</div>
      </div>
    );
  }

  if (notFound || !household) {
    return (
      <>
        <div className="nb-page-title">Household</div>
        <div className="nb-empty">
          <div className="nb-empty-icon">🔍</div>
          <div className="nb-empty-text">
            This household does not exist or you don&apos;t have access.
          </div>
          <button
            className="nb-btn-cancel"
            style={{ marginTop: 16 }}
            onClick={handleBack}
          >
            ← Back to Households
          </button>
        </div>
      </>
    );
  }

  return (
    <>
      <button className="nb-back-btn" onClick={handleBack}>
        ← Back to households
      </button>

      <div className="nb-page-title">{household.name}</div>
      <div className="nb-page-subtitle">Household details</div>

      {!household.active && (
        <p
          style={{
            fontFamily: "var(--font-hand)",
            fontSize: 14,
            background: "rgba(240,80,70,0.15)",
            color: "#c0392b",
            padding: "8px 12px",
            borderRadius: 4,
            marginBottom: 16,
          }}
        >
          This household is INACTIVE.
        </p>
      )}

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
          <strong>Name:</strong> {household.name}
        </div>
        <div>
          <strong>Status:</strong> {household.active ? "Active" : "Inactive"}
        </div>
      </div>

      {deactivateError && (
        <p
          style={{
            fontFamily: "var(--font-hand)",
            color: "var(--hl-overdue-border)",
            fontSize: 14,
            marginBottom: 12,
          }}
        >
          {deactivateError}
        </p>
      )}

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button className="nb-btn-primary" onClick={() => setMembersOpen(true)}>
          Members
        </button>
        <button className="nb-btn-cancel" onClick={openEdit}>
          Edit
        </button>
        {household.active && (
          <button
            className="nb-btn-cancel"
            style={{ color: "#c0392b" }}
            onClick={handleDeactivate}
            disabled={deactivating}
          >
            {deactivating ? "Deactivating…" : "Deactivate"}
          </button>
        )}
      </div>

      {editOpen && (
        <div className="nb-modal-backdrop">
          <div className="nb-modal">
            <h2 className="nb-modal-title">Edit Household</h2>
            <form onSubmit={handleEdit}>
              <div className="nb-form-group">
                <label className="nb-form-label">Name *</label>
                <input
                  className="nb-form-input"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  required
                  maxLength={100}
                />
              </div>
              {editError && (
                <p style={{ color: "red", fontSize: "0.85em" }}>{editError}</p>
              )}
              <div className="nb-modal-actions">
                <button
                  type="button"
                  className="nb-btn-cancel"
                  onClick={() => {
                    setEditOpen(false);
                    setEditError(null);
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="nb-btn-primary"
                  disabled={editLoading}
                >
                  {editLoading ? "Saving…" : "Save"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {membersOpen && (
        <MemberPanel
          household={household}
          onClose={() => setMembersOpen(false)}
        />
      )}
    </>
  );
}
