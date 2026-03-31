-- =============================================================================
-- UVM Gen - Admin Dashboard v2: Store full generation configs
-- Run this in Supabase SQL Editor
-- =============================================================================

-- Add config_json column to store the full UVM generation config
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='download_log' AND column_name='config_json') THEN
    ALTER TABLE public.download_log ADD COLUMN config_json JSONB DEFAULT NULL;
  END IF;
END $$;

-- Add user_email for quick lookup without joining profiles
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='download_log' AND column_name='user_email') THEN
    ALTER TABLE public.download_log ADD COLUMN user_email TEXT DEFAULT '';
  END IF;
END $$;

-- Add user_name for quick lookup
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='download_log' AND column_name='user_name') THEN
    ALTER TABLE public.download_log ADD COLUMN user_name TEXT DEFAULT '';
  END IF;
END $$;

-- Index for admin queries
CREATE INDEX IF NOT EXISTS idx_download_log_created ON public.download_log(created_at DESC);
