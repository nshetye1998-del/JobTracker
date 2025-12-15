"""
Facebook WhatsApp Business API Client for sending notifications
"""
import os
import requests
from typing import Optional
from libs.core.logger import configure_logger

logger = configure_logger("facebook_whatsapp")

class FacebookWhatsAppClient:
    """
    Facebook WhatsApp Business API client for sending messages
    """
    
    def __init__(self):
        self.api_token = os.getenv('WHATSAPP_API_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.recipient_phone = os.getenv('WHATSAPP_RECIPIENT_PHONE')
        
        # WhatsApp Business API endpoint
        self.api_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
        
        # Check if credentials are configured
        if not all([self.api_token, self.phone_number_id, self.recipient_phone]):
            logger.warning("⚠️ Facebook WhatsApp credentials not fully configured")
            logger.info("💡 Required env vars: WHATSAPP_API_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_RECIPIENT_PHONE")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"✅ Facebook WhatsApp client initialized")
            logger.info(f"📱 Phone Number ID: {self.phone_number_id}")
            logger.info(f"📱 Recipient: +{self.recipient_phone}")
    
    def send_notification(self, event: dict) -> Optional[str]:
        """
        Send WhatsApp notification for a job application event
        
        Args:
            event: Event dictionary with company, role, event_type, etc.
        
        Returns:
            Message ID if successful, None otherwise
        """
        if not self.enabled:
            logger.warning("⚠️ WhatsApp notifications disabled (no Facebook credentials)")
            return None
        
        try:
            # Extract event details
            event_type = event.get('event_type', 'UNKNOWN')
            company = event.get('company', 'Unknown Company')
            role = event.get('role', 'Position')
            confidence = event.get('confidence', 0)
            briefing = event.get('research_briefing', 'No research available.')
            
            # Choose emoji based on event type
            emoji_map = {
                'INTERVIEW': '🎉',
                'OFFER': '💰',
                'REJECTION': '😔',
                'APPLIED': '📝',
                'OTHER': '📬'
            }
            emoji = emoji_map.get(event_type, '📬')
            
            # Format message body
            message_body = (
                f"{emoji} *{event_type.upper()}*\n\n"
                f"🏢 Company: *{company}*\n"
                f"💼 Role: {role}\n"
                f"🎯 Confidence: {int(confidence * 100)}%\n\n"
                f"📋 *Research:*\n{briefing[:500]}..."
            )
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": self.recipient_phone,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": message_body
                }
            }
            
            # Send message via Facebook WhatsApp API
            logger.info(f"📤 Sending WhatsApp message to +{self.recipient_phone}")
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                message_id = response_data.get('messages', [{}])[0].get('id', 'unknown')
                
                logger.info(f"✅ WhatsApp notification sent!")
                logger.info(f"   📨 Message ID: {message_id}")
                logger.info(f"   🏢 Company: {company}")
                logger.info(f"   📝 Type: {event_type}")
                
                return message_id
            else:
                logger.error(f"❌ Failed to send WhatsApp message")
                logger.error(f"   Status Code: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return None
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ WhatsApp API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ WhatsApp API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp notification: {e}")
            return None
    
    def send_template_message(self, template_name: str, language_code: str = "en_US", components: list = None) -> Optional[str]:
        """
        Send a WhatsApp template message (for pre-approved templates)
        
        Args:
            template_name: Name of the approved template
            language_code: Language code (default: en_US)
            components: Template components with parameters
        
        Returns:
            Message ID if successful, None otherwise
        """
        if not self.enabled:
            logger.warning("⚠️ WhatsApp notifications disabled")
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": self.recipient_phone,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    }
                }
            }
            
            if components:
                payload["template"]["components"] = components
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                message_id = response_data.get('messages', [{}])[0].get('id', 'unknown')
                logger.info(f"✅ WhatsApp template sent! Message ID: {message_id}")
                return message_id
            else:
                logger.error(f"❌ Template send failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to send template: {e}")
            return None
