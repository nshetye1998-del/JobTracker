"""
Outlook/Office 365 Email Client using Microsoft Graph API with Device Code Flow
No Azure Portal registration needed!
"""
import os
import msal
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from libs.core.logger import configure_logger

logger = configure_logger("outlook_client")

class OutlookClient:
    """
    Outlook client using Microsoft Graph API with Device Code Flow
    Uses Microsoft's public client ID - no registration needed!
    """
    
    def __init__(self):
        # Microsoft Graph CLI public client ID (no registration needed!)
        self.client_id = "14d82eec-204b-4c2f-b7e8-296a70dab67e"
        
        self.authority = "https://login.microsoftonline.com/common"
        self.scopes = ["Mail.Read", "User.Read"]
        
        # Token cache file
        self.cache_file = "outlook_token_cache.json"
        self.cache = msal.SerializableTokenCache()
        
        # Load cached tokens if available
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                self.cache.deserialize(f.read())
            logger.info("✅ Loaded cached Outlook tokens")
        
        # Create MSAL public client application
        self.app = msal.PublicClientApplication(
            self.client_id,
            authority=self.authority,
            token_cache=self.cache
        )
        
        # Check if we have cached credentials
        accounts = self.app.get_accounts()
        if accounts:
            self.enabled = True
            logger.info(f"✅ Outlook client initialized for {accounts[0]['username']}")
        else:
            self.enabled = False
            logger.warning("⚠️ Outlook not authenticated. Run authenticate_outlook.py first")
    
    def _save_cache(self):
        """Save token cache to file"""
        if self.cache.has_state_changed:
            with open(self.cache_file, "w") as f:
                f.write(self.cache.serialize())
            logger.info("💾 Token cache saved")
    
    def authenticate(self) -> Optional[str]:
        """
        Device code authentication - user does this once
        Returns access token if successful
        """
        try:
            # Initiate device flow
            flow = self.app.initiate_device_flow(scopes=self.scopes)
            
            if "user_code" not in flow:
                raise ValueError("Failed to create device flow")
            
            # Display instructions to user
            logger.info("\n" + "="*60)
            logger.info("OUTLOOK AUTHENTICATION REQUIRED")
            logger.info("="*60)
            logger.info(flow["message"])
            logger.info("="*60)
            
            print("\n" + "="*60)
            print("OUTLOOK AUTHENTICATION REQUIRED")
            print("="*60)
            print(flow["message"])
            print("="*60)
            
            # Wait for user to authenticate
            result = self.app.acquire_token_by_device_flow(flow)
            
            if "access_token" in result:
                self._save_cache()
                self.enabled = True
                logger.info("✅ Authentication successful!")
                print("✅ Authentication successful!")
                return result["access_token"]
            else:
                error = result.get('error_description', result.get('error'))
                logger.error(f"❌ Authentication failed: {error}")
                raise Exception(f"Authentication failed: {error}")
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            raise
    
    def get_token(self) -> Optional[str]:
        """
        Get access token (uses cache if available, otherwise prompts for auth)
        Returns access token or None
        """
        try:
            accounts = self.app.get_accounts()
            
            if accounts:
                # Try silent token acquisition from cache
                result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
                if result and "access_token" in result:
                    self._save_cache()
                    return result["access_token"]
            
            # Need to authenticate
            logger.warning("⚠️ No valid token found. Need to authenticate.")
            return self.authenticate()
            
        except Exception as e:
            logger.error(f"❌ Failed to get token: {e}")
            return None
    
    def fetch_emails(self, since_hours: int = 24) -> List[Dict]:
        """
        Fetch emails from Outlook using Microsoft Graph API
        
        Args:
            since_hours: Fetch emails from the last N hours (default: 24)
        
        Returns:
            List of email dictionaries in standard format
        """
        if not self.enabled:
            logger.warning("⚠️ Outlook client not authenticated. Run authenticate_outlook.py")
            return []
        
        try:
            # Get access token
            token = self.get_token()
            if not token:
                logger.error("❌ Could not obtain access token")
                return []
            
            # Calculate time filter
            since_time = datetime.utcnow() - timedelta(hours=since_hours)
            since_time_str = since_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Microsoft Graph API endpoint
            url = "https://graph.microsoft.com/v1.0/me/messages"
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Query parameters
            params = {
                '$filter': f"receivedDateTime ge {since_time_str}",
                '$select': 'id,subject,from,receivedDateTime,bodyPreview,body',
                '$orderby': 'receivedDateTime desc',
                '$top': 100  # Fetch up to 100 emails
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            messages = response.json().get('value', [])
            
            logger.info(f"✅ Fetched {len(messages)} emails from Outlook")
            
            # Convert to standard format
            formatted_emails = []
            for msg in messages:
                try:
                    email = {
                        'id': f"outlook_{msg['id']}",
                        'subject': msg.get('subject', ''),
                        'from': msg['from']['emailAddress']['address'] if msg.get('from') else 'unknown',
                        'body': msg.get('body', {}).get('content', msg.get('bodyPreview', '')),
                        'received_at': msg['receivedDateTime'],
                        'provider': 'outlook'
                    }
                    formatted_emails.append(email)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse email {msg.get('id')}: {e}")
                    continue
            
            return formatted_emails
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch Outlook emails: {e}")
            
            # Provide helpful error hints
            error_str = str(e).lower()
            if 'unauthorized' in error_str or '401' in error_str:
                logger.error("💡 Token expired. Re-authenticate with authenticate_outlook.py")
            elif '403' in error_str or 'forbidden' in error_str:
                logger.error("💡 Permission denied. Ensure you granted Mail.Read permission")
            
            return []
