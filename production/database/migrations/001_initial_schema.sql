-- Migration: 001_initial_schema
-- Date: 2026-02-27
-- Description: Initial database schema with all tables for Customer Success Digital FTE

-- UP
BEGIN;

-- Run the main schema
\i /docker-entrypoint-initdb.d/schema.sql

COMMIT;

-- DOWN
BEGIN;

-- Drop all tables in reverse dependency order
DROP TABLE IF EXISTS ticket_counters CASCADE;
DROP TABLE IF EXISTS knowledge_base CASCADE;
DROP TABLE IF EXISTS escalations CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP FUNCTION IF EXISTS generate_ticket_number() CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
DROP EXTENSION IF EXISTS vector;
DROP EXTENSION IF EXISTS "uuid-ossp";

COMMIT;
