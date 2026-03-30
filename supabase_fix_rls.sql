-- =============================================================================
-- FIX: Infinite recursion in RLS policies
-- Run this in Supabase SQL Editor AFTER the migration
-- =============================================================================

-- Helper function to check admin role (bypasses RLS)
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.profiles
    WHERE id = auth.uid() AND role = 'admin'
  );
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- ═══════════════════════════════════════════════════════════════
-- Fix PROFILES policies
-- ═══════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS "Users can read own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
DROP POLICY IF EXISTS "Admins can read all profiles" ON public.profiles;

CREATE POLICY "Users can read own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);

-- Admin policy now uses the SECURITY DEFINER function (no recursion)
CREATE POLICY "Admins can read all profiles"
  ON public.profiles FOR SELECT
  USING (public.is_admin());

-- ═══════════════════════════════════════════════════════════════
-- Fix MESSAGES policies
-- ═══════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS "Users can insert own messages" ON public.messages;
DROP POLICY IF EXISTS "Users can read own messages" ON public.messages;
DROP POLICY IF EXISTS "Admins can read all messages" ON public.messages;
DROP POLICY IF EXISTS "Admins can update messages (reply)" ON public.messages;

CREATE POLICY "Users can insert own messages"
  ON public.messages FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can read own messages"
  ON public.messages FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Admins can read all messages"
  ON public.messages FOR SELECT
  USING (public.is_admin());

CREATE POLICY "Admins can update messages (reply)"
  ON public.messages FOR UPDATE
  USING (public.is_admin());

-- ═══════════════════════════════════════════════════════════════
-- Fix DOWNLOAD_LOG policies
-- ═══════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS "Users can insert own downloads" ON public.download_log;
DROP POLICY IF EXISTS "Users can read own downloads" ON public.download_log;
DROP POLICY IF EXISTS "Admins can read all downloads" ON public.download_log;

CREATE POLICY "Users can insert own downloads"
  ON public.download_log FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can read own downloads"
  ON public.download_log FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Admins can read all downloads"
  ON public.download_log FOR SELECT
  USING (public.is_admin());
