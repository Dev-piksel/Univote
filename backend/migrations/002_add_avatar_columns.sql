-- Add photo_url columns for avatars
ALTER TABLE public.students ADD COLUMN IF NOT EXISTS photo_url TEXT;
ALTER TABLE public.advisers ADD COLUMN IF NOT EXISTS photo_url TEXT;
ALTER TABLE public.admins ADD COLUMN IF NOT EXISTS photo_url TEXT;

-- Standardize indexes for these new columns (optional but good for future lookups)
CREATE INDEX IF NOT EXISTS idx_students_photo ON public.students(photo_url) WHERE photo_url IS NOT NULL;
