# SQL Migration Script for Job Table
# Run these SQL statements in your Neon/PostgreSQL database console

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

-- Verify migration
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'jobs' 
ORDER BY ordinal_position;
