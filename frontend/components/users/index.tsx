"use client";
import { useEffect, useState } from "react";
import type { UserResponse, UserRole } from "@/helpers/types";
import {
  getUsersAction,
  createUserAction,
  updateUserAction,
  deactivateUserAction,
  reactivateUserAction,
} from "./actions";

type CreateForm = {
  username: string;
  password: string;
  first_name: string;
  last_name: string;
  role: UserRole;
};

type EditForm = {
  first_name: string;
  last_name: string;
  role: UserRole;
  active: boolean;
};

const EMPTY_CREATE: CreateForm = {
  username: "",
  password: "",
  first_name: "",
  last_name: "",
  role: "user",
};

export function UsersManager() {
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState<CreateForm>(EMPTY_CREATE);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createLoading, setCreateLoading] = useState(false);

  const [editUser, setEditUser] = useState<UserResponse | null>(null);
  const [editForm, setEditForm] = useState<EditForm>({
    first_name: "",
    last_name: "",
    role: "user",
    active: true,
  });
  const [editError, setEditError] = useState<string | null>(null);
  const [editLoading, setEditLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    const result = await getUsersAction();
    if (result.success) {
      setUsers(result.data);
    } else {
      setError(result.error.message);
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const openEdit = (user: UserResponse) => {
    setEditUser(user);
    setEditForm({
      first_name: user.first_name ?? "",
      last_name: user.last_name ?? "",
      role: user.role,
      active: user.active,
    });
    setEditError(null);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    setCreateLoading(true);
    const result = await createUserAction({
      username: createForm.username,
      password: createForm.password,
      first_name: createForm.first_name || null,
      last_name: createForm.last_name || null,
      role: createForm.role,
    });
    setCreateLoading(false);
    if (result.success) {
      setShowCreate(false);
      setCreateForm(EMPTY_CREATE);
      load();
    } else {
      setCreateError(result.error.message);
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editUser) return;
    setEditError(null);
    setEditLoading(true);
    const result = await updateUserAction(editUser.id, {
      first_name: editForm.first_name || null,
      last_name: editForm.last_name || null,
      role: editForm.role,
      active: editForm.active,
    });
    setEditLoading(false);
    if (result.success) {
      setEditUser(null);
      load();
    } else {
      setEditError(result.error.message);
    }
  };

  const handleToggleActive = async (user: UserResponse) => {
    if (user.active) {
      await deactivateUserAction(user.id);
    } else {
      await reactivateUserAction(user.id);
    }
    load();
  };

  const displayName = (u: UserResponse) => {
    const parts = [u.first_name, u.last_name].filter(Boolean);
    return parts.length > 0 ? parts.join(" ") : u.username;
  };

  return (
    <div>
      <h1 className="nb-page-title">Users</h1>
      <p className="nb-page-subtitle">Manage application users and roles</p>

      <button className="nb-add-btn" onClick={() => setShowCreate(true)}>
        + Add User
      </button>

      {loading && <p className="nb-empty">Loading users…</p>}
      {error && (
        <p className="nb-empty" style={{ color: "red" }}>
          {error}
        </p>
      )}

      {!loading && users.length === 0 && (
        <p className="nb-empty">No users found.</p>
      )}

      {users.map((user) => (
        <div key={user.id} className="nb-payment-card">
          <div style={{ flex: 1 }}>
            <strong>{displayName(user)}</strong>
            {user.first_name || user.last_name ? (
              <span style={{ marginLeft: 8, opacity: 0.6, fontSize: "0.9em" }}>
                @{user.username}
              </span>
            ) : null}
            <span
              style={{
                marginLeft: 8,
                fontSize: "0.75em",
                padding: "2px 6px",
                borderRadius: 4,
                background:
                  user.role === "admin" ? "var(--cover-bg)" : "#e0e0e0",
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
                  marginLeft: 6,
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
          <div style={{ display: "flex", gap: 8 }}>
            <button
              className="nb-btn-cancel"
              onClick={() => openEdit(user)}
              style={{ fontSize: "0.85em" }}
            >
              Edit
            </button>
            <button
              className={user.active ? "nb-btn-cancel" : "nb-btn-primary"}
              onClick={() => handleToggleActive(user)}
              style={{ fontSize: "0.85em" }}
            >
              {user.active ? "Deactivate" : "Reactivate"}
            </button>
          </div>
        </div>
      ))}

      {/* Create modal */}
      {showCreate && (
        <div className="nb-modal-backdrop">
          <div className="nb-modal">
            <h2 className="nb-modal-title">Create User</h2>
            <form onSubmit={handleCreate}>
              <div className="nb-form-group">
                <label className="nb-form-label">Username *</label>
                <input
                  className="nb-form-input"
                  value={createForm.username}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, username: e.target.value })
                  }
                  required
                  minLength={3}
                  maxLength={50}
                />
              </div>
              <div className="nb-form-group">
                <label className="nb-form-label">Password *</label>
                <input
                  className="nb-form-input"
                  type="password"
                  value={createForm.password}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, password: e.target.value })
                  }
                  required
                  minLength={8}
                />
              </div>
              <div className="nb-form-row">
                <div className="nb-form-group">
                  <label className="nb-form-label">First Name</label>
                  <input
                    className="nb-form-input"
                    value={createForm.first_name}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        first_name: e.target.value,
                      })
                    }
                  />
                </div>
                <div className="nb-form-group">
                  <label className="nb-form-label">Last Name</label>
                  <input
                    className="nb-form-input"
                    value={createForm.last_name}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        last_name: e.target.value,
                      })
                    }
                  />
                </div>
              </div>
              <div className="nb-form-group">
                <label className="nb-form-label">Role</label>
                <select
                  className="nb-form-select"
                  value={createForm.role}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      role: e.target.value as UserRole,
                    })
                  }
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
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
                    setCreateForm(EMPTY_CREATE);
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

      {/* Edit modal */}
      {editUser && (
        <div className="nb-modal-backdrop">
          <div className="nb-modal">
            <h2 className="nb-modal-title">Edit User — {editUser.username}</h2>
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
                    setEditUser(null);
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
    </div>
  );
}
