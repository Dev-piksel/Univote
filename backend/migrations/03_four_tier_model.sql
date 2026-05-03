-- Migration: 03_four_tier_model.sql
-- Description: Adds department scoping and support for 4-tier model.

-- 1. Create Departments table
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    code TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Add department_id to relevant tables
ALTER TABLE admins ADD COLUMN IF NOT EXISTS department_id UUID REFERENCES departments(id);
ALTER TABLE admins ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'admin'; -- 'super_admin' or 'admin'

ALTER TABLE advisers ADD COLUMN IF NOT EXISTS department_id UUID REFERENCES departments(id);

ALTER TABLE students ADD COLUMN IF NOT EXISTS department_id UUID REFERENCES departments(id);
ALTER TABLE students ADD COLUMN IF NOT EXISTS email TEXT;

ALTER TABLE elections ADD COLUMN IF NOT EXISTS department_id UUID REFERENCES departments(id);

ALTER TABLE partylists ADD COLUMN IF NOT EXISTS logo_url TEXT;
ALTER TABLE partylists ADD COLUMN IF NOT EXISTS department_id UUID REFERENCES departments(id);

ALTER TABLE candidates ADD COLUMN IF NOT EXISTS photo_url TEXT;

-- 3. Update RLS (Policies would be added here in a real environment)
-- For now, we assume the application logic handles the scoping.

-- 4. Seed a default department if needed
-- INSERT INTO departments (name, code) VALUES ('Default Department', 'DEF') ON CONFLICT DO NOTHING;
