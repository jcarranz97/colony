"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import type { UserResponse, UserRole } from "@/helpers/types";
import {
  getUserAction,
  updateUserAction,
  deactivateUserAction,
  reactivateUserAction,
} from "@/components/users/actions";
import { CopyIdButton, type EditForm } from "@/components/users";

export default function UserDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const [editOpen, setEditOpen] = useState(false);
  const [editForm, setEditForm] = useState<EditForm>({
    first_name: "",
    last_name: "",
    role: "user",
    active: true,
  });
  const [editError, setEditError] = useState<string | null>(null);
  const [editLoading, setEditLoading] = useState(false);

  const [toggleLoading, setToggleLoading] = useState(false);
  const [toggleError, setToggleError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getUserAction(id).then((res) => {
      if (cancelled) return;
      if (res.success) setUser(res.data);
      else setNotFound(true);
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const handleBack = () => {
    if (window.history.length > 1) router.back();
    else router.push("/users");
  };

  const openEdit = () => {
    if (!user) return;
    setEditForm({
      first_name: user.first_name ?? "",
      last_name: user.last_name ?? "",
      role: user.role,
      active: user.active,
    });
    setEditError(null);
    setEditOpen(true);
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    setEditError(null);
    setEditLoading(true);
    const result = await updateUserAction(user.id, {
      first_name: editForm.first_name || null,
      last_name: editForm.last_name || null,
      role: editForm.role,
      active: editForm.active,
    });
    setEditLoading(false);
    if (result.success) {
      setUser(result.data);
      setEditOpen(false);
    } else {
      setEditError(result.error.message);
    }
  };

  const handleToggleActive = async () => {
    if (!user) return;
    setToggleLoading(true);
    setToggleError(null);
    if (user.active) {
      const result = await deactivateUserAction(user.id);
      setToggleLoading(false);
      if (result.success) setUser({ ...user, active: false });
      else setToggleError(result.error.message);
    } else {
      const result = await reactivateUserAction(user.id);
      setToggleLoading(false);
      if (result.success) setUser(result.data);
      else setToggleError(result.error.message);
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

  if (notFound || !user) {
    return (
      <>
        <div className="nb-page-title">User</div>
        <div className="nb-empty">
          <div className="nb-empty-icon">🔍</div>
          <div className="nb-empty-text">
            This user does not exist or you don&apos;t have access.
          </div>
          <button
            className="nb-btn-cancel"
            style={{ marginTop: 16 }}
            onClick={handleBack}
          >
            ← Back to Users
          </button>
        </div>
      </>
    );
  }

  const displayName = () => {
    const parts = [user.first_name, user.last_name].filter(Boolean);
    return parts.length > 0 ? parts.join(" ") : user.username;
  };

  return (
    <>
      <button className="nb-back-btn" onClick={handleBack}>
        ← Back to users
      </button>

      <div className="nb-page-title">{displayName()}</div>
      <div className="nb-page-subtitle">@{user.username}</div>

      <div
        style={{
          display: "flex",
          gap: 8,
          alignItems: "center",
          marginBottom: 24,
          marginTop: 8,
          flexWrap: "wrap",
        }}
      >
        <span
          style={{
            fontSize: "0.75em",
            padding: "2px 8px",
            borderRadius: 4,
            background: user.role === "admin" ? "var(--cover-bg)" : "#e0e0e0",
            color: user.role === "admin" ? "var(--cover-accent)" : "#555",
            fontWeight: 600,
            textTransform: "uppercase",
          }}
        >
          {user.role}
        </span>
        {!user.active && (
          <span
            style={{
              fontSize: "0.75em",
              padding: "2px 8px",
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
          <strong>Username:</strong> {user.username}
        </div>
        <div>
          <strong>First name:</strong> {user.first_name ?? "—"}
        </div>
        <div>
          <strong>Last name:</strong> {user.last_name ?? "—"}
        </div>
        <div>
          <strong>Role:</strong> {user.role}
        </div>
        <div>
          <strong>Status:</strong> {user.active ? "Active" : "Inactive"}
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            marginTop: 4,
          }}
        >
          <strong>User ID:</strong>
          <code
            style={{
              fontSize: 12,
              background: "rgba(0,0,0,0.04)",
              padding: "2px 6px",
              borderRadius: 3,
            }}
          >
            {user.id}
          </code>
          <CopyIdButton id={user.id} />
        </div>
      </div>

      {toggleError && (
        <p
          style={{
            fontFamily: "var(--font-hand)",
            color: "var(--hl-overdue-border)",
            fontSize: 14,
            marginBottom: 12,
          }}
        >
          {toggleError}
        </p>
      )}

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button className="nb-btn-primary" onClick={openEdit}>
          Edit
        </button>
        <button
          className={user.active ? "nb-btn-cancel" : "nb-btn-primary"}
          onClick={handleToggleActive}
          disabled={toggleLoading}
        >
          {toggleLoading
            ? "Working…"
            : user.active
              ? "Deactivate"
              : "Reactivate"}
        </button>
      </div>

      {editOpen && (
        <div className="nb-modal-backdrop">
          <div className="nb-modal">
            <h2 className="nb-modal-title">Edit User — {user.username}</h2>
            <form onSubmit={handleEdit}>
              <div className="nb-form-row">
                <div className="nb-form-group">
                  <label className="nb-form-label">First Name</label>
                  <input
                    className="nb-form-input"
                    value={editForm.first_name}
                    onChange={(e) =>
                      setEditForm({ ...editForm, first_name: e.target.value })
                    }
                  />
                </div>
                <div className="nb-form-group">
                  <label className="nb-form-label">Last Name</label>
                  <input
                    className="nb-form-input"
                    value={editForm.last_name}
                    onChange={(e) =>
                      setEditForm({ ...editForm, last_name: e.target.value })
                    }
                  />
                </div>
              </div>
              <div className="nb-form-group">
                <label className="nb-form-label">Role</label>
                <select
                  className="nb-form-select"
                  value={editForm.role}
                  onChange={(e) =>
                    setEditForm({
                      ...editForm,
                      role: e.target.value as UserRole,
                    })
                  }
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="nb-form-group">
                <label className="nb-form-label">Status</label>
                <select
                  className="nb-form-select"
                  value={editForm.active ? "active" : "inactive"}
                  onChange={(e) =>
                    setEditForm({
                      ...editForm,
                      active: e.target.value === "active",
                    })
                  }
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
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
    </>
  );
}
