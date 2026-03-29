-- =============================================================================
-- UVM Testbench Generator - Supabase Migration
-- Run this in your Supabase SQL Editor (Dashboard > SQL Editor)
-- =============================================================================

-- 1. Profiles table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
  id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email       TEXT NOT NULL,
  full_name   TEXT DEFAULT '',
  company     TEXT DEFAULT '',
  role        TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin')),
  created_at  TIMESTAMPTZ DEFAULT now(),
  updated_at  TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);

CREATE POLICY "Admins can read all profiles"
  ON public.profiles FOR SELECT
  USING (
    EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', '')
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 2. Messages / Feedback table
CREATE TABLE IF NOT EXISTS public.messages (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  user_email  TEXT NOT NULL,
  user_name   TEXT DEFAULT '',
  content     TEXT NOT NULL CHECK (length(content) > 0 AND length(content) <= 2000),
  category    TEXT DEFAULT 'feedback' CHECK (category IN ('feedback', 'bug', 'feature', 'question')),
  is_read     BOOLEAN DEFAULT false,
  admin_reply TEXT DEFAULT NULL,
  replied_at  TIMESTAMPTZ DEFAULT NULL,
  created_at  TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can insert own messages"
  ON public.messages FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can read own messages"
  ON public.messages FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Admins can read all messages"
  ON public.messages FOR SELECT
  USING (
    EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
  );

CREATE POLICY "Admins can update messages (reply)"
  ON public.messages FOR UPDATE
  USING (
    EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- 3. Download log (tracks who downloaded what)
CREATE TABLE IF NOT EXISTS public.download_log (
  id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  project_name  TEXT NOT NULL,
  protocol      TEXT DEFAULT 'custom',
  file_count    INT DEFAULT 0,
  created_at    TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.download_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can insert own downloads"
  ON public.download_log FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can read own downloads"
  ON public.download_log FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Admins can read all downloads"
  ON public.download_log FOR SELECT
  USING (
    EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- 4. Indexes
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON public.messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON public.messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_download_log_user_id ON public.download_log(user_id);
