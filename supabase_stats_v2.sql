-- =============================================================================
-- UVM Gen - Enhanced Public Stats with per-protocol breakdown
-- Run this in Supabase SQL Editor
-- =============================================================================

-- Replace the get_public_stats function with one that includes protocol breakdown
CREATE OR REPLACE FUNCTION public.get_public_stats()
RETURNS JSON
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT json_build_object(
    'total_generations', (SELECT COUNT(*) FROM public.generation_log),
    'registered_users',  (SELECT COUNT(*) FROM public.profiles),
    'total_downloads',   (SELECT COUNT(*) FROM public.download_log),
    'protocols_used',    (SELECT COUNT(DISTINCT protocol) FROM public.generation_log),
    'protocol_breakdown', (
      SELECT COALESCE(json_object_agg(protocol, cnt), '{}'::json)
      FROM (
        SELECT protocol, COUNT(*) AS cnt
        FROM public.generation_log
        GROUP BY protocol
        ORDER BY cnt DESC
      ) sub
    ),
    'download_protocol_breakdown', (
      SELECT COALESCE(json_object_agg(protocol, cnt), '{}'::json)
      FROM (
        SELECT protocol, COUNT(*) AS cnt
        FROM public.download_log
        GROUP BY protocol
        ORDER BY cnt DESC
      ) sub
    )
  );
$$;

GRANT EXECUTE ON FUNCTION public.get_public_stats() TO anon;
GRANT EXECUTE ON FUNCTION public.get_public_stats() TO authenticated;
