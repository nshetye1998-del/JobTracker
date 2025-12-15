import React from 'react';
import { X, Mail } from 'lucide-react';

const AuthModal = ({ isOpen, onClose, mode }) => {
  if (!isOpen) return null;

  const handleGoogleLogin = () => {
    // OAuth 2.0 configuration for Google
    const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || 'YOUR_GOOGLE_CLIENT_ID';
    const redirectUri = `${window.location.origin}/auth/callback/google`;
    const scope = 'email profile';
    
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${googleClientId}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=token&scope=${encodeURIComponent(scope)}`;
    
    window.location.href = authUrl;
  };

  const handleOutlookLogin = () => {
    // OAuth 2.0 configuration for Microsoft/Outlook
    const microsoftClientId = import.meta.env.VITE_MICROSOFT_CLIENT_ID || 'YOUR_MICROSOFT_CLIENT_ID';
    const redirectUri = `${window.location.origin}/auth/callback/microsoft`;
    const scope = 'openid profile email';
    
    const authUrl = `https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=${microsoftClientId}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=token&scope=${encodeURIComponent(scope)}`;
    
    window.location.href = authUrl;
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-slate-900 rounded-xl border border-slate-700 max-w-sm w-full p-5 relative my-auto">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 p-1.5 text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="text-center mb-5">
          <h2 className="text-xl font-bold text-white mb-1.5">
            {mode === 'login' ? 'Welcome Back' : 'Create Account'}
          </h2>
          <p className="text-sm text-slate-400">
            {mode === 'login' 
              ? 'Sign in to access your career dashboard' 
              : 'Join us to track your career journey'}
          </p>
        </div>

        <div className="space-y-2.5">
          {/* Google OAuth */}
          <button
            onClick={handleGoogleLogin}
            className="w-full flex items-center justify-center gap-3 px-5 py-2.5 bg-white hover:bg-gray-100 text-gray-900 rounded-lg font-medium transition-all text-sm"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </button>

          {/* Microsoft/Outlook OAuth */}
          <button
            onClick={handleOutlookLogin}
            className="w-full flex items-center justify-center gap-3 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-all text-sm"
          >
            <Mail className="w-4 h-4" />
            Continue with Outlook
          </button>
        </div>

        <div className="mt-3 pt-3 border-t border-slate-700 text-center">
          <p className="text-xs text-slate-400">
            {mode === 'login' ? (
              <>
                Don't have an account?{' '}
                <button className="text-blue-400 hover:text-blue-300 font-medium">
                  Sign up
                </button>
              </>
            ) : (
              <>
                Already have an account?{' '}
                <button className="text-blue-400 hover:text-blue-300 font-medium">
                  Sign in
                </button>
              </>
            )}
          </p>
        </div>

        <p className="text-xs text-slate-500 text-center mt-3">
          By continuing, you agree to our Terms of Service and Privacy Policy
        </p>
      </div>
    </div>
  );
};

export default AuthModal;
