"""
Twilio WhatsApp Client for sending notifications
Supports both freeform messages and Content Template API
"""
import os
from typing import Optional, Dict, List
from twilio.rest import Client
from libs.core.logger import configure_logger

logger = configure_logger("twilio_whatsapp")

class TwilioWhatsAppClient:
    """
    Twilio client for sending WhatsApp messages
    Supports:
    - Freeform messages (for job application notifications)
    - Content Template API (for approved templates like order updates)
    """
    
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
        self.to_number = os.getenv('TWILIO_WHATSAPP_TO')
        
        # Template configuration for order updates
        self.order_template_sid = os.getenv('TWILIO_ORDER_UPDATE_TEMPLATE_SID')
        self.order_template_name = os.getenv('TWILIO_ORDER_UPDATE_TEMPLATE_NAME', 'order_status_update')
        
        # Check if credentials are configured
        if not all([self.account_sid, self.auth_token, self.to_number]):
            logger.warning("⚠️ Twilio WhatsApp credentials not fully configured")
            logger.info("💡 Required env vars: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_TO")
            self.enabled = False
            self.client = None
        else:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                self.enabled = True
                logger.info(f"✅ Twilio WhatsApp client initialized")
                logger.info(f"📱 From: {self.from_number}")
                logger.info(f"📱 To: {self.to_number}")
                if self.order_template_sid:
                    logger.info(f"📋 Order Template: {self.order_template_name} (SID: {self.order_template_sid})")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Twilio client: {e}")
                self.enabled = False
                self.client = None
    
    def send_notification(self, event: dict) -> Optional[str]:
        """
        Send WhatsApp notification for a job application event
        
        Args:
            event: Event dictionary with company, role, event_type, etc.
        
        Returns:
            Message SID if successful, None otherwise
        """
        if not self.enabled or not self.client:
            logger.warning("⚠️ WhatsApp notifications disabled (no Twilio credentials)")
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
            
            # Send message via Twilio
            message = self.client.messages.create(
                from_=self.from_number,
                body=message_body,
                to=self.to_number
            )
            
            logger.info(f"✅ WhatsApp notification sent!")
            logger.info(f"   📨 Message SID: {message.sid}")
            logger.info(f"   🏢 Company: {company}")
            logger.info(f"   📝 Type: {event_type}")
            
            return message.sid
            
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp notification: {e}")
            
            # Provide helpful error hints
            error_str = str(e).lower()
            if 'authenticate' in error_str or '401' in error_str:
                logger.error("💡 Authentication failed. Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
            elif 'unverified' in error_str or '63003' in error_str:
                logger.error("💡 Phone number not verified. For sandbox:")
                logger.error("   1. Open WhatsApp")
                logger.error(f"   2. Message {self.from_number.replace('whatsapp:', '')}")
                logger.error("   3. Send: 'join <your-sandbox-code>'")
            elif 'invalid' in error_str and 'phone' in error_str:
                logger.error(f"💡 Invalid phone number format. Current: {self.to_number}")
                logger.error("   Use format: whatsapp:+15513627616")
            
            return None
    
    def send_order_update_template(
        self, 
        customer_name: str,
        order_number: str, 
        order_status: str,
        tracking_number: str = "",
        delivery_date: str = "",
        to_number: Optional[str] = None
    ) -> Optional[str]:
        """
        Send order status update using approved Twilio Content Template
        
        Args:
            customer_name: Customer's name (template variable 1)
            order_number: Order number (template variable 2)
            order_status: Order status - shipped, delivered, processing, etc. (template variable 3)
            tracking_number: Tracking number (template variable 4)
            delivery_date: Expected delivery date (template variable 5)
            to_number: Override recipient number (optional)
        
        Returns:
            Message SID if successful, None otherwise
        """
        if not self.enabled or not self.client:
            logger.warning("⚠️ WhatsApp notifications disabled (no Twilio credentials)")
            return None
        
        if not self.order_template_sid:
            logger.error("❌ Order template SID not configured. Set TWILIO_ORDER_UPDATE_TEMPLATE_SID")
            return None
        
        try:
            recipient = to_number or self.to_number
            
            logger.info(f"📤 Sending order update template to {recipient}")
            logger.info(f"   📦 Order: {order_number}")
            logger.info(f"   📊 Status: {order_status}")
            
            # Send using Content Template API
            message = self.client.messages.create(
                from_=self.from_number,
                to=recipient,
                content_sid=self.order_template_sid,
                content_variables=f'{{'
                                  f'"1":"{customer_name}",'
                                  f'"2":"{order_number}",'
                                  f'"3":"{order_status}",'
                                  f'"4":"{tracking_number}",'
                                  f'"5":"{delivery_date}"'
                                  f'}}'
            )
            
            logger.info(f"✅ Order update sent successfully!")
            logger.info(f"   📨 Message SID: {message.sid}")
            logger.info(f"   👤 Customer: {customer_name}")
            logger.info(f"   🚚 Status: {order_status}")
            
            return message.sid
            
        except Exception as e:
            logger.error(f"❌ Failed to send order update template: {e}")
            
            # Provide helpful error hints
            error_str = str(e).lower()
            if 'content template' in error_str or 'content_sid' in error_str:
                logger.error("💡 Template error. Verify:")
                logger.error(f"   - Template SID: {self.order_template_sid}")
                logger.error("   - Template is approved in Twilio Console")
                logger.error("   - Template variables match (1-5)")
            elif 'authenticate' in error_str or '401' in error_str:
                logger.error("💡 Authentication failed. Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
            
            return None
    
    def send_template_message(
        self,
        template_sid: str,
        variables: Dict[str, str],
        to_number: Optional[str] = None
    ) -> Optional[str]:
        """
        Send WhatsApp message using any Twilio Content Template
        
        Args:
            template_sid: Twilio Content Template SID (e.g., HXxxxx)
            variables: Dictionary of template variables {"1": "value1", "2": "value2"}
            to_number: Override recipient number (optional)
        
        Returns:
            Message SID if successful, None otherwise
        """
        if not self.enabled or not self.client:
            logger.warning("⚠️ WhatsApp notifications disabled (no Twilio credentials)")
            return None
        
        try:
            import json
            recipient = to_number or self.to_number
            
            logger.info(f"📤 Sending template message to {recipient}")
            logger.info(f"   📋 Template SID: {template_sid}")
            
            message = self.client.messages.create(
                from_=self.from_number,
                to=recipient,
                content_sid=template_sid,
                content_variables=json.dumps(variables)
            )
            
            logger.info(f"✅ Template message sent!")
            logger.info(f"   📨 Message SID: {message.sid}")
            
            return message.sid
            
        except Exception as e:
            logger.error(f"❌ Failed to send template message: {e}")
            return None
    
    def send_test_message(self) -> bool:
        """
        Send a test message to verify configuration
        
        Returns:
            True if successful, False otherwise
        """
        test_event = {
            'event_type': 'TEST',
            'company': 'Test Company',
            'role': 'Test Role',
            'confidence': 1.0,
            'research_briefing': 'This is a test message from JTC AI Notifier.'
        }
        
        message_sid = self.send_notification(test_event)
        return message_sid is not None
