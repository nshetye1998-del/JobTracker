import React, { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const AuthCallback = () => {
  const { provider } = useParams();
  const navigate = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Parse the token from URL hash
        const hash = window.location.hash.substring(1);
        const params = new URLSearchParams(hash);
        const accessToken = params.get('access_token');

        if (!accessToken) {
          throw new Error('No access token received');
        }

        let userInfo;
        
        if (provider === 'google') {
          // Fetch user info from Google
          const response = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
            headers: {
              Authorization: `Bearer ${accessToken}`
            }
          });
          userInfo = await response.json();
          
          login({
            id: userInfo.id,
            email: userInfo.email,
            name: userInfo.name || userInfo.email.split('@')[0],
            provider: 'google'
          }, accessToken);  // Pass token to login
        } else if (provider === 'microsoft') {
          // Fetch user info from Microsoft Graph
          const response = await fetch('https://graph.microsoft.com/v1.0/me', {
            headers: {
              Authorization: `Bearer ${accessToken}`
            }
          });
          userInfo = await response.json();
          
          login({
            id: userInfo.id,
            email: userInfo.mail || userInfo.userPrincipalName,
            name: userInfo.displayName || (userInfo.mail || userInfo.userPrincipalName).split('@')[0],
            provider: 'microsoft'
          }, accessToken);  // Pass token to login
        }

        navigate('/');
      } catch (error) {
        console.error('Auth callback error:', error);
        navigate('/?auth=error');
      }
    };

    handleCallback();
  }, [provider, login, navigate]);

  return (
    <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-white text-lg">Completing sign in...</p>
      </div>
    </div>
  );
};

export default AuthCallback;
