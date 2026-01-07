-- ForgeWorks Database Initialization Script
-- This script runs on first PostgreSQL container startup

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'ForgeWorks database initialized successfully';
END $$;
