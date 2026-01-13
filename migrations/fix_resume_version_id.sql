-- SQL Fix for Jobs Table
-- Run this in your Neon database console to fix the foreign key issue

-- 1. Drop the problematic column if it exists
ALTER TABLE jobs DROP COLUMN IF EXISTS resume_version_id;

-- 2. Verify the fix worked
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'jobs' 
AND column_name = 'resume_version_id';
-- This should return 0 rows

-- 3. Check all columns are present
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'jobs' 
ORDER BY ordinal_position;
