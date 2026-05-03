-- Add actor_name to audit_log table for better accountability
ALTER TABLE public.audit_log ADD COLUMN IF NOT EXISTS actor_name TEXT;

-- Update existing logs if possible (optional)
-- UPDATE public.audit_log SET actor_name = 'System' WHERE actor_name IS NULL;
