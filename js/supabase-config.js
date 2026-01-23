/**
 * PowersBioStrikes - Supabase Configuration
 *
 * SETUP INSTRUCTIONS:
 * 1. Go to your Supabase project dashboard: https://supabase.com/dashboard
 * 2. Click on Settings > API
 * 3. Copy your Project URL and paste it below
 * 4. Copy your anon/public key and paste it below
 * 5. In Authentication > URL Configuration, add your site URL to "Site URL"
 * 6. Add redirect URLs for:
 *    - https://powersbiostrikes.com/auth-callback.html
 *    - http://localhost:5500/auth-callback.html (for local dev)
 */

// Supabase credentials
const SUPABASE_URL = 'https://fnjnqtikxcspebobqdbe.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZuam5xdGlreGNzcGVib2JxZGJlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkwOTU1ODYsImV4cCI6MjA4NDY3MTU4Nn0.VR6perR3Oibvc0iE9ieS0Pb3BYJT0ApRYPZhg7zPyPc';

// Initialize Supabase client (use different name to avoid conflict with SDK)
const supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Auth helper functions
const pbsAuth = {
    // Get current user
    async getUser() {
        const { data: { user } } = await supabaseClient.auth.getUser();
        return user;
    },

    // Get current session
    async getSession() {
        const { data: { session } } = await supabaseClient.auth.getSession();
        return session;
    },

    // Sign up with email and password
    async signUp(email, password, fullName) {
        const { data, error } = await supabaseClient.auth.signUp({
            email,
            password,
            options: {
                data: {
                    full_name: fullName,
                },
                emailRedirectTo: `${window.location.origin}/auth-callback.html`
            }
        });
        return { data, error };
    },

    // Sign in with email and password
    async signIn(email, password) {
        const { data, error } = await supabaseClient.auth.signInWithPassword({
            email,
            password
        });
        return { data, error };
    },

    // Sign out
    async signOut() {
        const { error } = await supabaseClient.auth.signOut();
        return { error };
    },

    // Send password reset email
    async resetPassword(email) {
        const { data, error } = await supabaseClient.auth.resetPasswordForEmail(email, {
            redirectTo: `${window.location.origin}/reset-password.html`
        });
        return { data, error };
    },

    // Update password
    async updatePassword(newPassword) {
        const { data, error } = await supabaseClient.auth.updateUser({
            password: newPassword
        });
        return { data, error };
    },

    // Check if user is authenticated
    async isAuthenticated() {
        const session = await this.getSession();
        return !!session;
    },

    // Listen to auth state changes
    onAuthStateChange(callback) {
        return supabaseClient.auth.onAuthStateChange((event, session) => {
            callback(event, session);
        });
    },

    // Get user profile from database
    async getProfile(userId) {
        const { data, error } = await supabaseClient
            .from('profiles')
            .select('*')
            .eq('id', userId)
            .single();
        return { data, error };
    },

    // Update user profile
    async updateProfile(userId, updates) {
        const { data, error } = await supabaseClient
            .from('profiles')
            .upsert({ id: userId, ...updates, updated_at: new Date().toISOString() });
        return { data, error };
    }
};

// Export for use in other scripts
window.pbsAuth = pbsAuth;
window.supabaseClient = supabaseClient;
