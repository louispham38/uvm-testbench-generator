-- =============================================================================
-- Fix: Use SECURITY DEFINER function to bypass RLS for generation logging
-- This is the same approach used for is_admin() — reliable and clean
-- Run this in Supabase SQL Editor
-- =============================================================================

-- 1. Create a SECURITY DEFINER function for logging (bypasses RLS)
CREATE OR REPLACE FUNCTION public.log_generation(
  p_session_id TEXT DEFAULT '',
  p_user_id UUID DEFAULT NULL,
  p_user_email TEXT DEFAULT '',
  p_user_name TEXT DEFAULT '',
  p_project_name TEXT DEFAULT '',
  p_protocol TEXT DEFAULT 'custom',
  p_file_count INT DEFAULT 0,
  p_config_json JSONB DEFAULT NULL,
  p_is_guest BOOLEAN DEFAULT TRUE
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  INSERT INTO public.generation_log
    (session_id, user_id, user_email, user_name, project_name, protocol, file_count, config_json, is_guest)
  VALUES
    (p_session_id, p_user_id, p_user_email, p_user_name, p_project_name, p_protocol, p_file_count, p_config_json, p_is_guest);
END;
$$;

-- 2. Grant execute to both anon and authenticated
GRANT EXECUTE ON FUNCTION public.log_generation TO anon;
GRANT EXECUTE ON FUNCTION public.log_generation TO authenticated;

-- 3. Ensure stats function is accessible
GRANT EXECUTE ON FUNCTION public.get_public_stats() TO anon;
GRANT EXECUTE ON FUNCTION public.get_public_stats() TO authenticated;

-- 4. Fix admin SELECT policy on generation_log
DROP POLICY IF EXISTS "Admins can read all generations" ON public.generation_log;
CREATE POLICY "Admins can read all generations"
  ON public.generation_log FOR SELECT
  TO authenticated
  USING (public.is_admin());

-- Also allow admin DELETE for cleanup
DROP POLICY IF EXISTS "Admins can delete generations" ON public.generation_log;
CREATE POLICY "Admins can delete generations"
  ON public.generation_log FOR DELETE
  TO authenticated
  USING (public.is_admin());

-- 5. Table-level grants
GRANT SELECT, DELETE ON public.generation_log TO authenticated;
