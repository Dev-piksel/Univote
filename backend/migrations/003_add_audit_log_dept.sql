-- Add department_id to audit_log table for role-based scoping
ALTER TABLE public.audit_log ADD COLUMN IF NOT EXISTS department_id UUID REFERENCES public.departments(id) ON DELETE SET NULL;

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_audit_log_dept ON public.audit_log(department_id);
