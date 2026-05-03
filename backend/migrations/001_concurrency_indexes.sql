-- Strategic Indexes for High Concurrency
-- These indexes optimize the most frequent lookups during peak voting periods.

-- Optimize student lookup by department (used in voter list and scoping)
CREATE INDEX IF NOT EXISTS idx_students_department ON public.students(department_id);

-- Optimize vote counting and results streaming
CREATE INDEX IF NOT EXISTS idx_votes_election ON public.votes(election_id);

-- Optimize candidate lookup by election
CREATE INDEX IF NOT EXISTS idx_candidates_election ON public.candidates(election_id);

-- Optimize audit log lookups by actor (for dashboard/logs)
CREATE INDEX IF NOT EXISTS idx_audit_log_actor ON public.audit_log(actor_id);

-- Optimize passcode verification
CREATE INDEX IF NOT EXISTS idx_passcodes_election ON public.election_passcodes(election_id, entry_pin);
