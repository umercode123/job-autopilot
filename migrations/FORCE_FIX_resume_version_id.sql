-- FORCE FIX: Remove resume_version_id column if it exists
-- This is THE PROBLEM causing "0 saved to database"

-- Step 1: Drop the problematic column
ALTER TABLE jobs DROP COLUMN IF EXISTS resume_version_id CASCADE;

-- Step 2: Verify it's gone
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'jobs' AND column_name = 'resume_version_id';
-- Should return 0 rows

-- Step 3: Check all current columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'jobs' 
ORDER BY ordinal_position;
