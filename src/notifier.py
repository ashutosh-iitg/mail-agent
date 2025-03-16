"""
Notifier module - Sends notifications for important emails.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import notifiers
from twilio.rest import Client

logger = logging.getLogger(__name__)

class Notifier:
    """Sends notifications for important emails."""
    
    def __init__(self, config):
        """
        Initialize the notifier with configuration.
        
        Args:
            config (dict): Notification configuration dictionary.
        """
        self.config = config
        self.notification_method = config.get('method', 'sms')
    
    def send_notification(self, email_data):
        """
        Send a notification for an important email.
        
        Args:
            email_data (dict): Email data dictionary.
            
        Returns:
            bool: True if notification was sent successfully, False otherwise.
        """
        notification_methods = {
            'pushover': self._send_pushover_notification,
            'email': self._send_email_notification,
            'sms': self._send_sms_notification,
            'whatsapp': self._send_whatsapp_notification
        }
        
        if self.notification_method in notification_methods:
            return notification_methods[self.notification_method](email_data)
        else:
            logger.error(f"Unsupported notification method: {self.notification_method}")
            return False
    
    def _send_pushover_notification(self, email_data):
        """
        Send a notification via Pushover.
        
        Args:
            email_data (dict): Email data dictionary.
            
        Returns:
            bool: True if notification was sent successfully, False otherwise.
        """
        try:
            pushover_config = self.config.get('pushover', {})
            
            # Create notification content
            title = f"Important Email: {email_data['subject']}"
            message = f"From: {email_data['from']}\n\n{email_data['body'][:200]}..."
            
            # Send notification
            pushover = notifiers.get_notifier("pushover")
            result = pushover.notify(
                message=message,
                title=title,
                user=pushover_config.get('user_key'),
                token=pushover_config.get('api_token')
            )
            
            if result.status == "Success":
                logger.info(f"Pushover notification sent for email: {email_data['subject']}")
                return True
            else:
                logger.error(f"Error sending Pushover notification: {result.errors}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Pushover notification: {e}")
            return False
    
    def _send_email_notification(self, email_data):
        """
        Send a notification via email.
        
        Args:
            email_data (dict): Email data dictionary.
            
        Returns:
            bool: True if notification was sent successfully, False otherwise.
        """
        try:
            email_config = self.config.get('email', {})
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_config.get('from_address')
            msg['To'] = email_config.get('to_address')
            msg['Subject'] = f"Important Email: {email_data['subject']}"
            
            # Email body
            body = f"""
            Important email received:
            
            From: {email_data['from']}
            Subject: {email_data['subject']}
            Date: {email_data['date']}
            
            Preview:
            {email_data['body'][:500]}...
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server and send
            with smtplib.SMTP_SSL(email_config.get('smtp_server'), email_config.get('smtp_port')) as server:
                server.login(email_config.get('username'), email_config.get('password'))
                server.send_message(msg)
            
            logger.info(f"Email notification sent for: {email_data['subject']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    def _send_sms_notification(self, email_data):
        """
        Send a notification via SMS using Twilio.
        
        Args:
            email_data (dict): Email data dictionary.
            
        Returns:
            bool: True if notification was sent successfully, False otherwise.
        """
        try:
            sms_config = self.config.get('sms', {})
            provider = sms_config.get('provider', 'twilio').lower()
            
            if provider == 'twilio':
                twilio_config = sms_config.get('twilio', {})
                
                # Create notification content
                message = f"Important Email: {email_data['subject']} - From: {email_data['from']}"
                
                # Initialize Twilio client
                client = Client(twilio_config.get('account_sid'), twilio_config.get('auth_token'))
                
                # Send SMS
                message = client.messages.create(
                    body=message,
                    from_=twilio_config.get('from_number'),
                    to=twilio_config.get('to_number')
                )
                
                logger.info(f"SMS sent with ID: {message.sid} for email: {email_data['subject']}")
                return True
            else:
                logger.error(f"Unsupported SMS provider: {provider}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")
            return False
    
    def _send_whatsapp_notification(self, email_data):
        """
        Send a notification via WhatsApp using Twilio.
        
        Args:
            email_data (dict): Email data dictionary.
            
        Returns:
            bool: True if notification was sent successfully, False otherwise.
        """
        try:
            whatsapp_config = self.config.get('whatsapp', {})
            provider = whatsapp_config.get('provider', 'twilio').lower()
            
            if provider == 'twilio':
                twilio_config = whatsapp_config.get('twilio', {})
                
                # Create notification content with more details for WhatsApp
                message = f"""
                📧 *Important Email*
                
                *Subject:* {email_data['subject']}
                *From:* {email_data['from']}
                *Date:* {email_data['date']}
                
                *Preview:*
                {email_data['body'][:250]}...
                """
                
                # Initialize Twilio client
                client = Client(twilio_config.get('account_sid'), twilio_config.get('auth_token'))
                
                # Send WhatsApp message
                # Note: Twilio WhatsApp numbers should be prefixed with "whatsapp:"
                message = client.messages.create(
                    body=message,
                    from_=twilio_config.get('from_number'),
                    to=twilio_config.get('to_number')
                )
                
                logger.info(f"WhatsApp message sent with ID: {message.sid} for email: {email_data['subject']}")
                return True
            else:
                logger.error(f"Unsupported WhatsApp provider: {provider}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp notification: {e}")
            return False