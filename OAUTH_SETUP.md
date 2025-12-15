# OAuth Authentication Setup Guide

## ✅ Implementation Complete

Your dashboard now has OAuth authentication with:
- **Google Sign-In** (Gmail)
- **Microsoft Sign-In** (Outlook)
- **Sign Up / Log In** buttons
- User profile with picture and email
- Automatic button hiding when logged in

## 🔧 Setup Required

To enable OAuth, you need to configure your OAuth credentials:

### 1. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **Google+ API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure consent screen
6. Add authorized redirect URIs:
   - `http://localhost:3300/auth/callback/google`
   - `http://localhost:5173/auth/callback/google` (for dev)
7. Copy your **Client ID**

### 2. Microsoft OAuth Setup

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Set redirect URIs:
   - `http://localhost:3300/auth/callback/microsoft`
   - `http://localhost:5173/auth/callback/microsoft` (for dev)
5. Copy your **Application (client) ID**

### 3. Configure Environment Variables

Create a `.env` file in `services/dashboard-ui/`:

```bash
# Google OAuth
VITE_GOOGLE_CLIENT_ID=your_google_client_id_here

# Microsoft OAuth
VITE_MICROSOFT_CLIENT_ID=your_microsoft_client_id_here

# API URLs
VITE_API_URL=http://localhost:8000
VITE_ORCHESTRATOR_URL=http://localhost:8005
```

### 4. Rebuild Dashboard

```bash
cd services/dashboard-ui
npm run build
cd ../..
docker-compose -f deploy/docker-compose.yml up -d --build dashboard-ui
```

## 🎯 Features Implemented

### Before Login
- ✅ "Log In" button in header
- ✅ "Sign Up" button in header (gradient style)
- ✅ OAuth modal with Google and Outlook options
- ✅ Responsive design

### After Login
- ✅ Login/Signup buttons disappear
- ✅ User profile appears with:
  - Profile picture (if available)
  - User name
  - Email address
  - OAuth provider indicator
- ✅ Profile dropdown with:
  - My Profile
  - Settings
  - Sign Out
- ✅ User data persists in localStorage

## 🔐 Security Features

- OAuth 2.0 implicit flow
- Token-based authentication
- Secure callback handling
- User data persistence
- Automatic session management

## 📱 User Flow

1. User clicks "Sign Up" or "Log In"
2. Modal opens with OAuth options
3. User selects Google or Outlook
4. Redirected to OAuth provider
5. User grants permissions
6. Redirected back with token
7. User profile fetched and stored
8. Dashboard shows authenticated state

## 🎨 UI Changes

- Header now conditionally renders:
  - **Not logged in**: Log In + Sign Up buttons
  - **Logged in**: User profile with picture/name/email
- OAuth modal with branded buttons
- Loading state during authentication
- Error handling for failed auth

## 🔄 Current Status

Dashboard is running on **http://localhost:3300** with authentication ready!

**Note**: OAuth will work once you add your Client IDs to the `.env` file.
