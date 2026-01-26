-- PowersBioStrikes Beta/Waitlist Mode
-- Run this in Supabase SQL Editor to enable waitlist functionality

-- Add access_status column to profiles table
-- Values: 'admin', 'approved', 'waitlist'
ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS access_status VARCHAR(20) DEFAULT 'waitlist';

-- Update existing users to 'approved' (they signed up before waitlist mode)
UPDATE profiles
SET access_status = 'approved'
WHERE access_status IS NULL OR access_status = 'waitlist';

-- Set yourself as admin (replace with your actual user ID from auth.users)
-- To find your user ID: Go to Authentication > Users in Supabase Dashboard
-- UPDATE profiles SET access_status = 'admin' WHERE id = 'your-user-id-here';

-- Create an index for faster queries
CREATE INDEX IF NOT EXISTS idx_profiles_access_status ON profiles(access_status);

-- Create a function to automatically create a profile with 'waitlist' status on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, access_status, created_at)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
        'waitlist',
        NOW()
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for new user signups
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- View for approved members only (use this for member-only content)
CREATE OR REPLACE VIEW approved_members AS
SELECT * FROM profiles WHERE access_status IN ('admin', 'approved');

-- Grant access
GRANT SELECT ON approved_members TO authenticated;

COMMENT ON COLUMN profiles.access_status IS 'User access level: admin, approved, or waitlist';
