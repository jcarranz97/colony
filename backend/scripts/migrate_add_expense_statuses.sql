-- Migration: add paid_other and skipped values to expense_status enum
--
-- Run this script against an existing database to add the two new statuses.
-- Fresh databases created via create_tables.py do not need this script.
--
-- Usage (inside Docker or with psql):
--   psql "$DATABASE_URL" -f scripts/migrate_add_expense_statuses.sql

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'paid_other'
          AND enumtypid = 'expense_status'::regtype
    ) THEN
        ALTER TYPE expense_status ADD VALUE 'paid_other';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'skipped'
          AND enumtypid = 'expense_status'::regtype
    ) THEN
        ALTER TYPE expense_status ADD VALUE 'skipped';
    END IF;
END;
$$;
