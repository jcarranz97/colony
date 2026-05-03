"use client";
import { useEffect, useState } from "react";
import type { ExchangeRate, HouseholdResponse } from "@/helpers/types";
import {
  getExchangeRates,
  addExchangeRate,
  editExchangeRate,
  getCurrentUserAction,
  getMyHouseholdsAction,
  setActiveHouseholdAction,
} from "./actions";

// ── Helpers ───────────────────────────────────────────────────────────────────

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

function fmtDate(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

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

// ── Rate row ──────────────────────────────────────────────────────────────────

function RateRow({
  rate,
  isCurrent,
  onEdit,
}: {
  rate: ExchangeRate;
  isCurrent: boolean;
  onEdit: (r: ExchangeRate) => void;
}) {
  return (
    <div
      className="nb-payment-card"
      style={{
        background: isCurrent
          ? "rgba(44,74,62,0.07)"
          : "var(--paper-card, rgba(255,255,255,0.5))",
      }}
    >
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
        💱
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontFamily: "var(--font-title)",
            fontSize: 16,
            color: "var(--ink)",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          {rate.from_currency} → {rate.to_currency}
          {isCurrent && (
            <span
              style={{
                fontSize: 10,
                background: "rgba(44,74,62,0.15)",
                color: "var(--cover-bg)",
                borderRadius: 4,
                padding: "1px 6px",
                fontFamily: "var(--font-hand)",
              }}
            >
              current
            </span>
          )}
        </div>
        <div
          style={{
            fontFamily: "var(--font-hand)",
            fontSize: 13,
            color: "var(--ink-light)",
          }}
        >
          1 {rate.from_currency} = {Number(rate.rate).toFixed(6)}{" "}
          {rate.to_currency}
          &nbsp;·&nbsp;{fmtDate(rate.rate_date)}
        </div>
      </div>

      <button style={iconBtn} onClick={() => onEdit(rate)}>
        Edit
      </button>
    </div>
  );
}

// ── Add modal ─────────────────────────────────────────────────────────────────

function AddRateModal({
  isOpen,
  onClose,
  onSave,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSave: (rate: string, date: string) => Promise<string | null>;
}) {
  const [rate, setRate] = useState("");
  const [rateDate, setRateDate] = useState(today());
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setRate("");
      setRateDate(today());
      setError(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    const err = await onSave(rate, rateDate);
    setSaving(false);
    if (err) setError(err);
  };

  return (
    <div className="nb-modal-backdrop" onClick={onClose}>
      <div className="nb-modal" onClick={(e) => e.stopPropagation()}>
        <div className="nb-modal-title">Add Exchange Rate</div>

        <form onSubmit={handleSubmit}>
          <div className="nb-form-group">
            <label className="nb-form-label">Currency Pair</label>
            <div
              style={{
                fontFamily: "var(--font-hand)",
                fontSize: 15,
                color: "var(--ink)",
                padding: "6px 0",
              }}
            >
              MXN → USD
            </div>
          </div>

          <div className="nb-form-row">
            <div className="nb-form-group" style={{ flex: 1 }}>
              <label className="nb-form-label">Rate (1 MXN = ? USD)</label>
              <input
                className="nb-form-input"
                type="number"
                step="0.000001"
                min="0.000001"
                placeholder="e.g. 0.052000"
                value={rate}
                onChange={(e) => setRate(e.target.value)}
                required
              />
            </div>

            <div className="nb-form-group" style={{ flex: 1 }}>
              <label className="nb-form-label">Effective Date</label>
              <input
                className="nb-form-input"
                type="date"
                value={rateDate}
                onChange={(e) => setRateDate(e.target.value)}
                required
              />
            </div>
          </div>

          {error && (
            <div
              style={{
                color: "var(--hl-overdue, #d00)",
                fontFamily: "var(--font-hand)",
                fontSize: 13,
                marginBottom: 8,
              }}
            >
              {error}
            </div>
          )}

          <div className="nb-modal-actions">
            <button
              type="button"
              className="nb-btn-cancel"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </button>
            <button type="submit" className="nb-btn-primary" disabled={saving}>
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Edit modal ────────────────────────────────────────────────────────────────

function EditRateModal({
  rate,
  onClose,
  onSave,
}: {
  rate: ExchangeRate | null;
  onClose: () => void;
  onSave: (id: string, newRate: string) => Promise<string | null>;
}) {
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (rate) {
      setValue(Number(rate.rate).toFixed(6));
      setError(null);
    }
  }, [rate]);

  if (!rate) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    const err = await onSave(rate.id, value);
    setSaving(false);
    if (err) setError(err);
  };

  return (
    <div className="nb-modal-backdrop" onClick={onClose}>
      <div className="nb-modal" onClick={(e) => e.stopPropagation()}>
        <div className="nb-modal-title">Edit Exchange Rate</div>

        <form onSubmit={handleSubmit}>
          <div className="nb-form-group">
            <label className="nb-form-label">Currency Pair</label>
            <div
              style={{
                fontFamily: "var(--font-hand)",
                fontSize: 15,
                color: "var(--ink)",
                padding: "6px 0",
              }}
            >
              {rate.from_currency} → {rate.to_currency}
            </div>
          </div>

          <div className="nb-form-group">
            <label className="nb-form-label">Effective Date</label>
            <div
              style={{
                fontFamily: "var(--font-hand)",
                fontSize: 15,
                color: "var(--ink-light)",
                padding: "6px 0",
              }}
            >
              {fmtDate(rate.rate_date)}
            </div>
          </div>

          <div className="nb-form-group">
            <label className="nb-form-label">
              Rate (1 {rate.from_currency} = ? {rate.to_currency})
            </label>
            <input
              className="nb-form-input"
              type="number"
              step="0.000001"
              min="0.000001"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              required
            />
          </div>

          {error && (
            <div
              style={{
                color: "var(--hl-overdue, #d00)",
                fontFamily: "var(--font-hand)",
                fontSize: 13,
                marginBottom: 8,
              }}
            >
              {error}
            </div>
          )}

          <div className="nb-modal-actions">
            <button
              type="button"
              className="nb-btn-cancel"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </button>
            <button type="submit" className="nb-btn-primary" disabled={saving}>
              {saving ? "Saving…" : "Update"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Household selector ────────────────────────────────────────────────────────

function HouseholdSelector() {
  const [households, setHouseholds] = useState<HouseholdResponse[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string>("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      const [userRes, hhRes] = await Promise.all([
        getCurrentUserAction(),
        getMyHouseholdsAction(),
      ]);
      if (userRes.success) setActiveId(userRes.data.active_household_id);
      if (hhRes.success) setHouseholds(hhRes.data);
    };
    load();
  }, []);

  const activeName = households.find((h) => h.id === activeId)?.name ?? "—";
  const canChange = households.length > 1;

  const openModal = () => {
    setSelectedId(activeId ?? "");
    setSaveError(null);
    setModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedId || selectedId === activeId) {
      setModalOpen(false);
      return;
    }
    setSaving(true);
    setSaveError(null);
    const res = await setActiveHouseholdAction(selectedId);
    setSaving(false);
    if (res.success) {
      window.location.reload();
    } else {
      setSaveError(res.error.message);
    }
  };

  return (
    <>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "6px 0 4px",
        }}
      >
        <div
          style={{
            fontFamily: "var(--font-hand)",
            fontSize: 16,
            color: "var(--ink)",
          }}
        >
          🏠 {activeName}
        </div>
        {/* Wrapper span carries the tooltip — disabled buttons suppress hover events */}
        <span
          title={
            canChange
              ? undefined
              : "You only have one household. Ask your admin to create a new household or add you to an existing one."
          }
          style={{ cursor: canChange ? "auto" : "not-allowed" }}
        >
          <button
            className="nb-btn-cancel"
            onClick={canChange ? openModal : undefined}
            disabled={!canChange}
            style={{
              fontSize: "0.85em",
              opacity: canChange ? 1 : 0.4,
              cursor: canChange ? "pointer" : "not-allowed",
              pointerEvents: canChange ? "auto" : "none",
            }}
          >
            Change
          </button>
        </span>
      </div>
      {!canChange && households.length > 0 && (
        <p
          style={{
            fontFamily: "var(--font-hand)",
            fontSize: 13,
            color: "var(--ink-light)",
            marginBottom: 12,
          }}
        >
          You are assigned to one household. Ask your admin to add you to
          another one if needed.
        </p>
      )}

      {modalOpen && (
        <div className="nb-modal-backdrop">
          <div className="nb-modal">
            <h2 className="nb-modal-title">Change Household</h2>
            <form onSubmit={handleSave}>
              <div className="nb-form-group">
                <label className="nb-form-label">Select Household</label>
                <select
                  className="nb-form-select"
                  value={selectedId}
                  onChange={(e) => setSelectedId(e.target.value)}
                >
                  {households.map((h) => (
                    <option key={h.id} value={h.id}>
                      {h.name}
                      {h.id === activeId ? " (current)" : ""}
                    </option>
                  ))}
                </select>
              </div>
              {saveError && (
                <p style={{ color: "red", fontSize: "0.85em" }}>{saveError}</p>
              )}
              <div className="nb-modal-actions">
                <button
                  type="button"
                  className="nb-btn-cancel"
                  onClick={() => setModalOpen(false)}
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="nb-btn-primary"
                  disabled={saving}
                >
                  {saving ? "Saving…" : "Save"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function Settings() {
  const [rates, setRates] = useState<ExchangeRate[]>([]);
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<ExchangeRate | null>(null);

  useEffect(() => {
    getExchangeRates().then((res) => {
      if (res.success) setRates(res.data);
      setLoading(false);
    });
  }, []);

  const handleAdd = async (
    rate: string,
    rateDate: string,
  ): Promise<string | null> => {
    const res = await addExchangeRate({
      from_currency: "MXN",
      to_currency: "USD",
      rate: parseFloat(rate),
      rate_date: rateDate,
    });
    if (res.success) {
      setRates((prev) => [res.data, ...prev]);
      setAddOpen(false);
      return null;
    }
    return res.error.message;
  };

  const handleEdit = async (
    id: string,
    newRate: string,
  ): Promise<string | null> => {
    const res = await editExchangeRate(id, { rate: parseFloat(newRate) });
    if (res.success) {
      setRates((prev) => prev.map((r) => (r.id === id ? res.data : r)));
      setEditTarget(null);
      return null;
    }
    return res.error.message;
  };

  if (loading) {
    return (
      <div className="nb-empty">
        <div className="nb-empty-icon">⚙️</div>
        <div className="nb-empty-text">Loading settings…</div>
      </div>
    );
  }

  const mxnRates = rates.filter(
    (r) => r.from_currency === "MXN" && r.to_currency === "USD",
  );

  return (
    <>
      <div className="nb-page-title">Settings</div>
      <div className="nb-page-subtitle">Application configuration</div>

      <div className="nb-section-title">🏠 Household</div>
      <HouseholdSelector />

      <div className="nb-section-title">💱 Exchange Rates</div>
      <div
        style={{
          fontFamily: "var(--font-hand)",
          fontSize: 13,
          color: "var(--ink-light)",
          marginBottom: 16,
        }}
      >
        MXN → USD rates used to convert expenses. The most recent rate is
        applied automatically when creating expenses.
      </div>

      {mxnRates.length === 0 && (
        <div className="nb-empty">
          <div className="nb-empty-icon">💱</div>
          <div className="nb-empty-text">
            No exchange rates yet — add one to enable MXN expense creation.
          </div>
        </div>
      )}

      {mxnRates.map((r, i) => (
        <RateRow
          key={r.id}
          rate={r}
          isCurrent={i === 0}
          onEdit={setEditTarget}
        />
      ))}

      <button className="nb-add-btn" onClick={() => setAddOpen(true)}>
        + Add Exchange Rate
      </button>

      <AddRateModal
        isOpen={addOpen}
        onClose={() => setAddOpen(false)}
        onSave={handleAdd}
      />

      <EditRateModal
        rate={editTarget}
        onClose={() => setEditTarget(null)}
        onSave={handleEdit}
      />
    </>
  );
}
