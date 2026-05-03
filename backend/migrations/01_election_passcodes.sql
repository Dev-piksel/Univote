-- Migration: Enhanced Election Passcodes
-- Date: 2026-03-29

-- Create table for election passcodes
CREATE TABLE IF NOT EXISTS public.election_passcodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    election_id UUID NOT NULL REFERENCES public.elections(id) ON DELETE CASCADE,
    adviser_id UUID NOT NULL, -- Reference to admin or adviser ID (unified users table not found)
    passcode TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_election_passcodes_election_id ON public.election_passcodes(election_id);
CREATE INDEX IF NOT EXISTS idx_election_passcodes_is_active ON public.election_passcodes(is_active);

-- Enable RLS (Optional, but good practice)
ALTER TABLE public.election_passcodes ENABLE ROW LEVEL SECURITY;

-- Allow public read-only access (backend acts as proxy)
CREATE POLICY "Allow public read-only access to passcodes" ON public.election_passcodes
    FOR SELECT USING (TRUE);

-- Atomic function to generate and deactivate
CREATE OR REPLACE FUNCTION public.generate_election_passcode(
    p_election_id UUID,
    p_adviser_id UUID,
    p_passcode TEXT,
    p_expires_at TIMESTAMPTZ
) RETURNS JSONB AS $$
DECLARE
    v_id UUID;
BEGIN
    -- Deactivate existing passcodes for this election and adviser
    -- but FIRST, capture the existing entry_pin if it exists
    DECLARE
        v_preserved_pin TEXT;
    BEGIN
        SELECT entry_pin INTO v_preserved_pin
        FROM public.election_passcodes
        WHERE election_id = p_election_id AND adviser_id = p_adviser_id AND is_active = TRUE
        LIMIT 1;

        UPDATE public.election_passcodes
        SET is_active = FALSE
        WHERE election_id = p_election_id AND adviser_id = p_adviser_id;

        -- Insert new passcode with preserved entry_pin
        INSERT INTO public.election_passcodes (election_id, adviser_id, passcode, expires_at, entry_pin)
        VALUES (p_election_id, p_adviser_id, p_passcode, p_expires_at, v_preserved_pin)
        RETURNING id INTO v_id;
    END;

    RETURN jsonb_build_object('id', v_id, 'passcode', p_passcode, 'expires_at', p_expires_at);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
