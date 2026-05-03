-- Add department_id to audit_log for scoped viewing
ALTER TABLE audit_log ADD COLUMN department_id UUID REFERENCES departments(id);

-- Migration: Attempt to backfill department_id from actors if possible (optional)
-- UPDATE audit_log a SET department_id = (SELECT department_id FROM admins WHERE id = a.actor_id) WHERE actor_role IN ('admin', 'super_admin');
