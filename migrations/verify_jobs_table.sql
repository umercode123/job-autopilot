-- Complete Jobs Table Structure Verification and Fix
-- Run this in Neon SQL Editor to ensure all columns exist

-- 1. First, check what columns currently exist
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'jobs' 
ORDER BY ordinal_position;

-- 2. If any columns are missing, add them (safe to run multiple times)

-- Date fields
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS expiration_date TIMESTAMP;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS job_age VARCHAR;

-- URLs
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS apply_url VARCHAR;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_url VARCHAR;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_logo_url VARCHAR;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS header_image_url VARCHAR;

-- Job details
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS job_type VARCHAR;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS occupation VARCHAR;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS benefits TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS rating VARCHAR;

-- 3. Verify all columns now exist
SELECT 
    column_name,
    data_type,
    CASE WHEN is_nullable = 'YES' THEN 'NULL' ELSE 'NOT NULL' END as nullable
FROM information_schema.columns 
WHERE table_name = 'jobs' 
ORDER BY ordinal_position;

-- 4. Count existing jobs
SELECT COUNT(*) as total_jobs FROM jobs;
