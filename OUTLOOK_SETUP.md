# Outlook Integration - Device Code Flow

## 🚀 Simple Setup (No Azure Portal!)

This Outlook integration uses Microsoft's **Device Code Flow** with a public client ID - **no Azure Portal access required**!

### How It Works

1. **One-Time Authentication**: Run a simple script once
2. **Device Code Flow**: Visit a URL, enter a code, authenticate
3. **Token Cached**: Token saved locally for future use
4. **Automatic Fetching**: Ingestion service automatically fetches Outlook emails

---

## 📋 Setup Steps

### Step 1: Authenticate (ONE TIME)

```bash
cd /Users/nikunjshetye/.claude-worktrees/JTC_ai/focused-lovelace
python3 services/ingestion/authenticate_outlook.py
```

**What happens:**
1. Script displays a URL: `https://microsoft.com/devicelogin`
2. Script shows a code: e.g., `ABC-DEF-GHI`
3. You visit the URL in your browser
4. Enter the code
5. Sign in with your Outlook account
6. Grant Mail.Read permission
7. Token saved to `outlook_token_cache.json`

**Example output:**
```
============================================================
OUTLOOK AUTHENTICATION REQUIRED
============================================================
To sign in, use a web browser to open the page https://microsoft.com/devicelogin
and enter the code ABC-DEF-GHI to authenticate.
============================================================

✅ Authentication successful!
Token cached in: outlook_token_cache.json
```

### Step 2: Rebuild Ingestion Service

```bash
cd deploy
docker-compose build ingestion
docker-compose restart ingestion
```

### Step 3: Verify

```bash
docker-compose logs -f ingestion
```

**Expected logs:**
```
✅ Loaded cached Outlook tokens
✅ Outlook client initialized for your.email@outlook.com
✅ Email sources enabled: Gmail, Outlook
✅ Fetched 15 emails from Outlook
```

---

## 🧪 Testing

### Quick Test (Without Docker)

```bash
cd /Users/nikunjshetye/.claude-worktrees/JTC_ai/focused-lovelace
python3 test_outlook_auth.py
```

This will:
- Check if already authenticated
- If not, run device authentication
- Test fetching recent emails
- Display sample email

### Full Integration Test

```bash
# Check if ingestion service sees Outlook emails
docker-compose logs ingestion | grep -i outlook

# Should see:
# ✅ Outlook client initialized
# ✅ Fetched X emails from Outlook
```

---

## 📁 Files Changed

### 1. **services/ingestion/src/outlook_client.py** (NEW)
- Uses MSAL (Microsoft Authentication Library)
- Device code flow authentication
- Public client ID: `14d82eec-204b-4c2f-b7e8-296a70dab67e`
- Token caching in `outlook_token_cache.json`

### 2. **services/ingestion/authenticate_outlook.py** (NEW)
- One-time setup script
- Guides user through device authentication
- Tests email fetch after auth

### 3. **services/ingestion/requirements.txt**
- Added: `msal==1.26.0`

### 4. **services/ingestion/src/main.py**
- Updated to check for token cache before initializing Outlook
- Fetches emails from both Gmail and Outlook
- Logs which sources are active

---

## 🔧 Troubleshooting

### "Outlook not authenticated"
**Solution**: Run `python3 services/ingestion/authenticate_outlook.py`

### "Token expired"
**Solution**: Delete `outlook_token_cache.json` and re-authenticate

### "Permission denied"
**Solution**: During authentication, ensure you grant **Mail.Read** permission

### "Module 'msal' not found" (in Docker)
**Solution**: Rebuild the ingestion service:
```bash
docker-compose build ingestion
docker-compose restart ingestion
```

---

## 🎯 What Gets Fetched

- **Source**: Outlook/Office 365 emails
- **Time Range**: Last 24 hours (configurable)
- **Limit**: 100 emails per fetch
- **Permissions**: Read-only (Mail.Read)

---

## 🔐 Security

- **Public Client ID**: Uses Microsoft's official Graph CLI client
- **No Secrets**: No client secrets or app registration needed
- **Token Storage**: Cached locally in `outlook_token_cache.json`
- **Permissions**: Read-only access to your mailbox
- **Scope**: `Mail.Read` and `User.Read`

---

## ✅ Benefits

✅ **No Azure Portal** - No registration needed  
✅ **Simple Setup** - One-time device authentication  
✅ **Automatic Refresh** - Token auto-refreshes  
✅ **Secure** - Uses Microsoft's official client  
✅ **Multi-Source** - Works alongside Gmail  

---

## 📝 Next Steps

After authentication:

1. ✅ Outlook emails automatically fetched every 60 seconds
2. ✅ Combined with Gmail in same batch
3. ✅ Classified, researched, and notifications sent
4. ✅ WhatsApp notifications for INTERVIEW events

**You're all set! 🎉**
