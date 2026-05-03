-- Create session_logs table for auth and session events
CREATE TABLE IF NOT EXISTS public.session_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT, -- Can be student_id or admin/adviser UUID
    user_role TEXT,
    event_type TEXT NOT NULL, -- LOGIN, REGISTER, LOGOUT, VALIDATE
    ip_address TEXT,
    user_agent TEXT,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.session_logs ENABLE ROW LEVEL SECURITY;

-- Allow public insert (backend acts as proxy)
CREATE POLICY "Allow public insert to session_logs" ON public.session_logs
    FOR INSERT WITH CHECK (TRUE);

-- Allow admins to read
CREATE POLICY "Allow public read-only access to session_logs" ON public.session_logs
    FOR SELECT USING (TRUE);
