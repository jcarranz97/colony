-- Add 'extra' value to expense_category enum for existing databases.
-- Fresh databases (create_tables.py / tests) get it automatically.
--
-- Usage (inside Docker or with psql):
--   psql "$DATABASE_URL" -f scripts/migrate_add_expense_category_extra.sql

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'extra'
          AND enumtypid = 'expense_category'::regtype
    ) THEN
        ALTER TYPE expense_category ADD VALUE 'extra';
    END IF;
END;
$$;
