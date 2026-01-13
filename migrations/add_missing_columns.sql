-- Migration: Add missing columns to jobs table for Phase 2 Resume Export Feature
-- Run this in your Neon database console

-- Add selected_template column (for Resume Export feature)
ALTER TABLE jobs 
ADD COLUMN IF NOT EXISTS selected_template VARCHAR(50);

-- Verify the columns were added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'jobs' 
AND column_name IN ('selected_template')
ORDER BY column_name;

-- Expected result: Should show 1 row with selected_template column
