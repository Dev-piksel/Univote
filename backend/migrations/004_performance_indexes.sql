-- Performance indexes for high concurrency
CREATE INDEX IF NOT EXISTS idx_students_department ON public.students(department_id);
CREATE INDEX IF NOT EXISTS idx_votes_election ON public.votes(election_id);

-- Additional indexes for common lookups
CREATE INDEX IF NOT EXISTS idx_candidates_election ON public.candidates(election_id);
CREATE INDEX IF NOT EXISTS idx_advisers_dept ON public.advisers(department_id);
CREATE INDEX IF NOT EXISTS idx_admins_dept ON public.admins(department_id);
