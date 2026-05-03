-- Add actor_username (ID Number/Student ID) to audit_log table
ALTER TABLE public.audit_log ADD COLUMN IF NOT EXISTS actor_username TEXT;

-- Recommended: also add actor_name if you haven't already
ALTER TABLE public.audit_log ADD COLUMN IF NOT EXISTS actor_name TEXT;
