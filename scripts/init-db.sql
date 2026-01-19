-- =============================================================================
-- FastAPI REST API Starter - Database Initialization
-- =============================================================================
-- This script runs when the PostgreSQL container is first created.
-- It sets up the database with required extensions.
-- =============================================================================

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Grant permissions (if using a non-default user)
-- GRANT ALL PRIVILEGES ON DATABASE fastapi_starter TO your_user;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully';
END $$;
