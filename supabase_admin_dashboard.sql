-- =============================================================================
-- UVM Gen - Admin Dashboard Migration
-- Run this AFTER supabase_fix_rls.sql if you haven't already.
-- This ensures admin can read/reply messages and view download stats.
-- =============================================================================

-- Add admin_reply columns to messages (skip if already exists)
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='messages' AND column_name='admin_reply') THEN
    ALTER TABLE public.messages ADD COLUMN admin_reply TEXT DEFAULT NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='messages' AND column_name='replied_at') THEN
    ALTER TABLE public.messages ADD COLUMN replied_at TIMESTAMPTZ DEFAULT NULL;
  END IF;
END $$;

-- Ensure admin can update messages (reply)
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='messages' AND policyname='Admins can update messages') THEN
    CREATE POLICY "Admins can update messages"
      ON public.messages FOR UPDATE
      USING (public.is_admin());
  END IF;
END $$;

-- Ensure admin can read all download_log
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='download_log' AND policyname='Admins can read all download_log') THEN
    CREATE POLICY "Admins can read all download_log"
      ON public.download_log FOR SELECT
      USING (public.is_admin());
  END IF;
END $$;

-- Ensure admin can read all messages  
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='messages' AND policyname='Admins can read all messages (v2)') THEN
    CREATE POLICY "Admins can read all messages (v2)"
      ON public.messages FOR SELECT
      USING (public.is_admin());
  END IF;
END $$;
