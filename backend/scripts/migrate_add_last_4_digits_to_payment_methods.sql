-- Migration: add last_4_digits column to payment_methods
--
-- Run this script against an existing database to add the new column.
-- Fresh databases created via create_tables.py do not need this script.
--
-- Usage (inside Docker or with psql):
--   psql "$DATABASE_URL" -f scripts/migrate_add_last_4_digits_to_payment_methods.sql

ALTER TABLE payment_methods
    ADD COLUMN IF NOT EXISTS last_4_digits VARCHAR(4);
