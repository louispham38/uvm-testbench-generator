-- =============================================================================
-- UVM Gen - Guest Activity Tracking + Public Stats
-- Run this in Supabase SQL Editor
-- =============================================================================

-- 1. Generation log: tracks ALL generations (guest + logged-in)
CREATE TABLE IF NOT EXISTS public.generation_log (
  id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  session_id    TEXT DEFAULT '',
  user_id       UUID DEFAULT NULL,
  user_email    TEXT DEFAULT '',
  user_name     TEXT DEFAULT '',
  project_name  TEXT NOT NULL,
  protocol      TEXT DEFAULT 'custom',
  file_count    INT DEFAULT 0,
  config_json   JSONB DEFAULT NULL,
  is_guest      BOOLEAN DEFAULT true,
  created_at    TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.generation_log ENABLE ROW LEVEL SECURITY;

-- Anyone (including guests via anon key) can insert
CREATE POLICY "Anyone can log generations"
  ON public.generation_log FOR INSERT
  WITH CHECK (true);

-- Only admins can read all generation logs
CREATE POLICY "Admins can read all generations"
  ON public.generation_log FOR SELECT
  USING (public.is_admin());

-- Index for admin queries
CREATE INDEX IF NOT EXISTS idx_generation_log_created ON public.generation_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_generation_log_guest ON public.generation_log(is_guest);

-- 2. Public stats function (callable by anyone, returns only aggregated numbers)
CREATE OR REPLACE FUNCTION public.get_public_stats()
RETURNS JSON
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT json_build_object(
    'total_generations', (SELECT COUNT(*) FROM public.generation_log),
    'registered_users',  (SELECT COUNT(*) FROM public.profiles),
    'total_downloads',   (SELECT COUNT(*) FROM public.download_log),
    'protocols_used',    (SELECT COUNT(DISTINCT protocol) FROM public.generation_log)
  );
$$;
