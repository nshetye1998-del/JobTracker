"""
Outlook Email Client using Microsoft Graph API
Fetches unread emails from Outlook/Office 365 accounts
"""
import requests
from typing import List, Dict, Optional
from libs.core.logger import configure_logger
from libs.core.config import BaseConfig, get_config

logger = configure_logger("outlook_client")

class OutlookConfig(BaseConfig):
    OUTLOOK_CLIENT_ID: Optional[str] = None
    OUTLOOK_CLIENT_SECRET: Optional[str] = None
    OUTLOOK_TENANT_ID: Optional[str] = None

config = get_config(OutlookConfig)

class OutlookClient:
    """
    Microsoft Graph API client for fetching emails from Outlook
    Uses Application permissions (daemon app) instead of delegated
    """
    
    def __init__(self):
        self.client_id = config.OUTLOOK_CLIENT_ID
        self.client_secret = config.OUTLOOK_CLIENT_SECRET
        self.tenant_id = config.OUTLOOK_TENANT_ID
        self.access_token = None
        
        # Check if credentials are configured
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            logger.warning("Outlook credentials not configured. Outlook integration disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Outlook client initialized")
    
    def _get_access_token(self) -> Optional[str]:
        """
        Get access token using client credentials flow
        https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow
        """
        if not self.enabled:
            return None
            
        try:
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'https://graph.microsoft.com/.default',
                'grant_type': 'client_credentials'
            }
            
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            logger.info("✅ Outlook access token obtained")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Failed to get Outlook access token: {e}")
            return None
    
    def list_messages(self, user_email: str, query: str = "isRead eq false") -> List[Dict]:
        """
        List messages for a specific user
        
        Args:
            user_email: The user's email address (e.g., 'user@company.com')
            query: OData filter query (default: unread emails)
        
        Returns:
            List of message metadata dictionaries
        """
        if not self.enabled:
            return []
        
        # Get fresh token if needed
        if not self.access_token:
            if not self._get_access_token():
                return []
        
        try:
            url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            params = {
                '$filter': query,
                '$select': 'id,subject,from,receivedDateTime,bodyPreview,isRead',
                '$top': 50,  # Max 50 emails per request
                '$orderby': 'receivedDateTime DESC'
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            messages = data.get('value', [])
            logger.info(f"📧 Found {len(messages)} unread Outlook emails")
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to list Outlook messages: {e}")
            if 'response' in locals():
                logger.error(f"Response: {response.text}")
            return []
    
    def get_message(self, user_email: str, message_id: str) -> Optional[Dict]:
        """
        Get full message content including body
        
        Args:
            user_email: The user's email address
            message_id: The message ID to fetch
        
        Returns:
            Full message dictionary or None
        """
        if not self.enabled:
            return None
            
        if not self.access_token:
            if not self._get_access_token():
                return None
        
        try:
            url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages/{message_id}"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            params = {
                '$select': 'id,subject,from,to,receivedDateTime,body,bodyPreview,isRead,conversationId'
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            message = response.json()
            return message
            
        except Exception as e:
            logger.error(f"Failed to get Outlook message {message_id}: {e}")
            return None
    
    def mark_as_read(self, user_email: str, message_id: str) -> bool:
        """
        Mark a message as read
        
        Args:
            user_email: The user's email address
            message_id: The message ID to mark as read
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
            
        if not self.access_token:
            if not self._get_access_token():
                return False
        
        try:
            url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages/{message_id}"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {'isRead': True}
            
            response = requests.patch(url, headers=headers, json=data)
            response.raise_for_status()
            
            logger.info(f"Marked Outlook message {message_id} as read")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark Outlook message as read: {e}")
            return False
    
    def convert_to_standard_format(self, outlook_message: Dict, user_email: str) -> Dict:
        """
        Convert Outlook message format to standard format (same as Gmail)
        
        Args:
            outlook_message: Raw Outlook message from Graph API
            user_email: The user's email address (for context)
        
        Returns:
            Standardized message dictionary
        """
        try:
            # Extract sender email
            from_field = outlook_message.get('from', {})
            sender_email = from_field.get('emailAddress', {}).get('address', 'unknown')
            sender_name = from_field.get('emailAddress', {}).get('name', sender_email)
            
            # Extract body
            body = outlook_message.get('body', {})
            body_content = body.get('content', '')
            body_type = body.get('contentType', 'text')  # 'text' or 'html'
            
            # Standardized format (matching Gmail structure)
            standard_message = {
                'message_id': f"outlook_{outlook_message['id']}",
                'thread_id': outlook_message.get('conversationId', ''),
                'from_email': sender_email,
                'from_name': sender_name,
                'to_email': user_email,
                'subject': outlook_message.get('subject', '(No subject)'),
                'received_at': outlook_message.get('receivedDateTime', ''),
                'snippet': outlook_message.get('bodyPreview', '')[:200],
                'body_text': body_content if body_type == 'text' else '',
                'body_html': body_content if body_type == 'html' else '',
                'labels': ['outlook', 'unread'] if not outlook_message.get('isRead') else ['outlook'],
                'source': 'outlook',
                'raw_data': outlook_message
            }
            
            return standard_message
            
        except Exception as e:
            logger.error(f"Failed to convert Outlook message format: {e}")
            return {}
