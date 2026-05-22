"use client";
import { useEffect, useState } from "react";
import type { ApiToken, ApiTokenWithSecret } from "@/helpers/types";
import { formatDate } from "@/helpers/formatters";
import { getApiTokens, addApiToken, removeApiToken } from "./actions";

// ── Notebook action button ────────────────────────────────────────────────────

const iconBtn: React.CSSProperties = {
  fontFamily: "var(--font-hand)",
  fontSize: 12,
  fontWeight: 600,
  background: "transparent",
  border: "1px solid var(--btn-cancel-border, #c0b090)",
  borderRadius: 4,
  padding: "3px 9px",
  cursor: "pointer",
  color: "var(--ink-light)",
  transition: "all 0.14s",
};

const errorText: React.CSSProperties = {
  fontFamily: "var(--font-hand)",
  color: "var(--hl-overdue-border)",
  fontSize: 14,
  marginBottom: 8,
};

// ── Token card ────────────────────────────────────────────────────────────────

function TokenCard({
  token,
  onRevoke,
}: {
  token: ApiToken;
  onRevoke: (t: ApiToken) => void;
}) {
  const expired =
    token.expires_at !== null && new Date(token.expires_at) < new Date();

  return (
    <div className="nb-payment-card">
      <div
        style={{
          width: 44,
          height: 44,
          borderRadius: 10,
          background: "var(--stat-card-bg, rgba(44,74,62,0.08))",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          flexShrink: 0,
        }}
      >
        🔑
      </div>

      <div style={{ flex: 1 }}>
        <div
          style={{
            fontFamily: "var(--font-title)",
            fontSize: 18,
            fontWeight: 700,
            color: "var(--ink)",
          }}
        >
          {token.name}
        </div>
        <div
          style={{
            fontFamily: "var(--font-hand)",
            fontSize: 13,
            color: "var(--ink-light)",
            opacity: 0.65,
            display: "flex",
            gap: 8,
            marginTop: 2,
            flexWrap: "wrap",
          }}
        >
          <span style={{ fontFamily: "monospace" }}>{token.prefix}…</span>
          <span>·</span>
          <span>Created {formatDate(token.created_at)}</span>
          <span>·</span>
          <span>
            {token.last_used_at
              ? `Last used ${formatDate(token.last_used_at)}`
              : "Never used"}
          </span>
          {token.expires_at && (
            <>
              <span>·</span>
              <span
                style={expired ? { color: "var(--hl-overdue-border)" } : {}}
              >
                {expired ? "Expired " : "Expires "}
                {formatDate(token.expires_at)}
              </span>
            </>
          )}
        </div>
      </div>

      <button
        style={{
          ...iconBtn,
          color: "rgba(220,53,69,0.7)",
          border: "1px solid rgba(220,53,69,0.35)",
        }}
        onClick={() => onRevoke(token)}
        title="Revoke this token"
      >
        🗑 Revoke
      </button>
    </div>
  );
}

// ── Create token modal ────────────────────────────────────────────────────────

function CreateTokenModal({
  isOpen,
  onClose,
  onCreated,
}: {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (token: ApiTokenWithSecret) => void;
}) {
  const [name, setName] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setName("");
      setExpiresAt("");
      setError(null);
    }
  }, [isOpen]);

  const handleSubmit = async () => {
    if (!name.trim()) {
      setError("Give the token a name.");
      return;
    }
    setSaving(true);
    setError(null);
    const res = await addApiToken({
      name: name.trim(),
      expires_at: expiresAt ? expiresAt : null,
    });
    if (res.success) {
      onCreated(res.data);
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
        <div className="nb-modal-title">New API Token</div>
        <p
          style={{
            fontFamily: "var(--font-hand)",
            fontSize: 14,
            color: "var(--ink-light)",
            marginBottom: 12,
            lineHeight: 1.5,
          }}
        >
          Use API tokens to connect agents and the MCP server to Colony. A token
          acts as you — only your data is reachable with it.
        </p>

        <div className="nb-form-group">
          <label className="nb-form-label">Name</label>
          <input
            className="nb-form-input"
            placeholder="e.g. My MCP, Claude Code laptop"
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoFocus
          />
        </div>

        <div className="nb-form-group">
          <label className="nb-form-label">Expires (optional)</label>
          <input
            className="nb-form-input"
            type="date"
            value={expiresAt}
            onChange={(e) => setExpiresAt(e.target.value)}
          />
        </div>

        {error && <p style={errorText}>{error}</p>}

        <div className="nb-modal-actions">
          <button className="nb-btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button
            className="nb-btn-primary"
            onClick={handleSubmit}
            disabled={saving}
          >
            {saving ? "Creating…" : "Create Token ✓"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── New token secret modal (shown once) ──────────────────────────────────────

function NewTokenModal({
  token,
  onClose,
}: {
  token: ApiTokenWithSecret | null;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!token) return;
    try {
      await navigator.clipboard.writeText(token.token);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  if (!token) return null;

  return (
    <div className="nb-modal-backdrop">
      <div className="nb-modal">
        <div className="nb-modal-title">Token “{token.name}” created</div>
        <p
          style={{
            fontFamily: "var(--font-hand)",
            fontSize: 14,
            color: "var(--ink)",
            marginBottom: 12,
            lineHeight: 1.5,
          }}
        >
          Copy this token now — for your security it is{" "}
          <strong>shown only once</strong> and cannot be retrieved later.
        </p>

        <div
          style={{
            fontFamily: "monospace",
            fontSize: 13,
            background: "var(--stat-card-bg, rgba(44,74,62,0.08))",
            border: "1px solid var(--btn-cancel-border, #c0b090)",
            borderRadius: 6,
            padding: "10px 12px",
            wordBreak: "break-all",
            marginBottom: 12,
            color: "var(--ink)",
          }}
        >
          {token.token}
        </div>

        <div className="nb-modal-actions">
          <button className="nb-btn-cancel" onClick={handleCopy}>
            {copied ? "Copied ✓" : "Copy token"}
          </button>
          <button className="nb-btn-primary" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Confirm revoke modal ──────────────────────────────────────────────────────

function ConfirmRevokeModal({
  token,
  onClose,
  onConfirmed,
}: {
  token: ApiToken | null;
  onClose: () => void;
  onConfirmed: (id: string) => void;
}) {
  const [revoking, setRevoking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (token) setError(null);
  }, [token]);

  const handleConfirm = async () => {
    if (!token) return;
    setRevoking(true);
    setError(null);
    const res = await removeApiToken(token.id);
    if (res.success) {
      onConfirmed(token.id);
      onClose();
    } else {
      setError(res.error.message);
    }
    setRevoking(false);
  };

  if (!token) return null;

  return (
    <div
      className="nb-modal-backdrop"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="nb-modal">
        <button className="nb-modal-close" onClick={onClose}>
          ✕
        </button>
        <div className="nb-modal-title">Revoke token?</div>
        <p
          style={{
            fontFamily: "var(--font-hand)",
            fontSize: 15,
            color: "var(--ink)",
            marginBottom: 8,
            lineHeight: 1.5,
          }}
        >
          <strong>{token.name}</strong> will stop working immediately. Any agent
          or MCP client using it will lose access until you create a new token.
        </p>
        {error && <p style={errorText}>{error}</p>}
        <div className="nb-modal-actions">
          <button className="nb-btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button
            className="nb-btn-danger"
            onClick={handleConfirm}
            disabled={revoking}
          >
            {revoking ? "Revoking…" : "Revoke 🗑"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function ApiTokens() {
  const [tokens, setTokens] = useState<ApiToken[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [newToken, setNewToken] = useState<ApiTokenWithSecret | null>(null);
  const [revokeTarget, setRevokeTarget] = useState<ApiToken | null>(null);

  useEffect(() => {
    getApiTokens().then((res) => {
      if (res.success) setTokens(res.data);
      else setError(res.error.message);
      setLoading(false);
    });
  }, []);

  const handleCreated = (token: ApiTokenWithSecret) => {
    setCreateOpen(false);
    // Store only metadata in the list — keep the secret out of list state.
    const metadata: ApiToken = {
      id: token.id,
      name: token.name,
      prefix: token.prefix,
      last_used_at: token.last_used_at,
      expires_at: token.expires_at,
      active: token.active,
      created_at: token.created_at,
      updated_at: token.updated_at,
    };
    setTokens((prev) => [metadata, ...prev]);
    setNewToken(token);
  };

  const handleRevoked = (id: string) => {
    setTokens((prev) => prev.filter((t) => t.id !== id));
    setRevokeTarget(null);
  };

  if (loading) {
    return (
      <div className="nb-empty">
        <div className="nb-empty-icon">📖</div>
        <div className="nb-empty-text">Loading…</div>
      </div>
    );
  }

  return (
    <>
      <div className="nb-page-title">API Tokens</div>
      <div className="nb-page-subtitle">
        Personal access tokens for agents &amp; the MCP server
      </div>

      {error && <p style={errorText}>{error}</p>}

      {tokens.length > 0 ? (
        <>
          <div className="nb-section-title">🔑 Your tokens</div>
          {tokens.map((t) => (
            <TokenCard key={t.id} token={t} onRevoke={setRevokeTarget} />
          ))}
        </>
      ) : (
        <div className="nb-empty">
          <div className="nb-empty-icon">🔑</div>
          <div className="nb-empty-text">
            No tokens yet — create one to connect an agent to Colony.
          </div>
        </div>
      )}

      <button className="nb-add-btn" onClick={() => setCreateOpen(true)}>
        + New API Token
      </button>

      <CreateTokenModal
        isOpen={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={handleCreated}
      />

      <NewTokenModal token={newToken} onClose={() => setNewToken(null)} />

      <ConfirmRevokeModal
        token={revokeTarget}
        onClose={() => setRevokeTarget(null)}
        onConfirmed={handleRevoked}
      />
    </>
  );
}
