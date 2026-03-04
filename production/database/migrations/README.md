# Database Migrations

This directory contains database migrations for schema evolution.

## Usage

### Create a new migration

```bash
# Manual: Create new migration file
cp production/database/migrations/001_initial_schema.sql \
   production/database/migrations/002_<description>.sql
```

### Run migrations

```bash
# Using psql
docker-compose exec postgres psql -U user -d crm_fte_db -f /docker-entrypoint-initdb.d/migrations/001_initial_schema.sql

# Or from Python
python production/database/migrations/run_migrations.py
```

### Rollback migrations

```bash
# Each migration should include a -- DOWN section
# Rollback using the DOWN section
```

## Migration Template

```sql
-- Migration: 002_<description>
-- Date: YYYY-MM-DD
-- Description: <what this migration does>

-- UP
BEGIN;

-- Your migration SQL here

COMMIT;

-- DOWN
BEGIN;

-- Rollback SQL here

COMMIT;
```

## Current Migrations

1. **001_initial_schema.sql** - Initial database schema with all tables
   - customers
   - conversations
   - tickets
   - messages
   - escalations
   - knowledge_base
   - ticket_counters (for auto-generating ticket numbers)
