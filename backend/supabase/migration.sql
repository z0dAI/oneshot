-- Clay Talent Portal schema
-- Run this in Supabase Dashboard → SQL Editor

-- Enum types
CREATE TYPE user_role AS ENUM ('admin', 'recruiter', 'employee');
CREATE TYPE user_status AS ENUM ('active', 'pending', 'archived');

-- Profiles table (linked to auth.users)
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    role user_role NOT NULL DEFAULT 'employee',
    status user_status NOT NULL DEFAULT 'pending',
    domain TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_profiles_domain ON public.profiles(domain);
CREATE INDEX idx_profiles_status ON public.profiles(status);

-- Auto-update updated_at on row change
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Allowed domains table
CREATE TABLE public.allowed_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain TEXT UNIQUE NOT NULL,
    added_by UUID REFERENCES public.profiles(id),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
