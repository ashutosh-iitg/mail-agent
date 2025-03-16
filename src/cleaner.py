"""
Email Cleaner module - Cleans inbox by removing unwanted emails.
"""

import logging
import re
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

logger = logging.getLogger(__name__)

class EmailCleaner:
    """Cleans inbox by removing unwanted emails."""
    
    def __init__(self, config):
        """
        Initialize the cleaner with configuration.
        
        Args:
            config (dict): Cleaning configuration dictionary.
        """
        self.config = config
    
    def clean(self, email_provider):
        """
        Clean the inbox by removing unwanted emails.
        
        Args:
            email_provider (EmailProvider): The email provider instance.
            
        Returns:
            int: Number of emails cleaned.
        """
        cleaned_count = 0
        
        try:
            # Get all emails (we need to search in all emails, not just unprocessed)
            emails = email_provider.get_all_emails()
            logger.info(f"Found {len(emails)} emails to check for cleaning")
            
            for email in emails:
                if self._should_delete(email):
                    if email_provider.delete_email(email):
                        cleaned_count += 1
                        logger.info(f"Deleted email: {email['subject']}")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning emails: {e}")
            return cleaned_count
    
    def _should_delete(self, email):
        """
        Determine if an email should be deleted.
        
        Args:
            email (dict): Email data dictionary.
            
        Returns:
            bool: True if the email should be deleted, False otherwise.
        """
        # Check if it's a newsletter and newsletters should be deleted
        if self.config.get('delete_newsletters', False) and self._is_newsletter(email):
            return True
        
        # Check if it's older than the configured age
        if self.config.get('delete_older_than') and self._is_too_old(email, self.config.get('delete_older_than')):
            return True
        
        # Check if it's read and read emails should be deleted
        if self.config.get('delete_read', False) and self._is_read(email):
            return True
        
        return False
    
    def _is_newsletter(self, email):
        """
        Check if an email is a newsletter.
        
        Args:
            email (dict): Email data dictionary.
            
        Returns:
            bool: True if the email is a newsletter, False otherwise.
        """
        # Check if the sender domain is in the newsletter domains list
        sender_domain = self._extract_domain(email['from'])
        newsletter_domains = self.config.get('newsletter_domains', [])
        
        if any(domain.lower() in sender_domain.lower() for domain in newsletter_domains):
            return True
        
        # Check for common newsletter indicators in the subject
        newsletter_keywords = ['newsletter', 'subscribe', 'update', 'digest', 'weekly', 'monthly']
        subject = email['subject'].lower()
        
        if any(keyword in subject for keyword in newsletter_keywords):
            return True
        
        # Check for unsubscribe link in email body
        if 'unsubscribe' in email['body'].lower():
            return True
        
        return False
    
    def _is_too_old(self, email, max_age_days):
        """
        Check if an email is older than the maximum age.
        
        Args:
            email (dict): Email data dictionary.
            max_age_days (int): Maximum age in days.
            
        Returns:
            bool: True if the email is too old, False otherwise.
        """
        try:
            # Parse the email date
            email_date = parsedate_to_datetime(email['date'])
            
            # Calculate the cutoff date
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            # Compare dates
            return email_date < cutoff_date
            
        except Exception as e:
            logger.error(f"Error checking email age: {e}")
            return False
    
    def _is_read(self, email):
        """
        Check if an email has been read.
        
        Args:
            email (dict): Email data dictionary.
            
        Returns:
            bool: True if the email has been read, False otherwise.
        """
        # Gmail uses the 'UNREAD' label
        if 'labels' in email and 'UNREAD' not in email['labels']:
            return True
        
        # For IMAP, check the '\Seen' flag
        if 'flags' in email and '\\Seen' in email['flags']:
            return True
        
        return False
    
    def _extract_domain(self, from_field):
        """
        Extract domain from the 'from' field.
        
        Args:
            from_field (str): The 'from' field of the email.
            
        Returns:
            str: The domain of the sender's email address.
        """
        try:
            # Extract email address from the 'from' field
            match = re.search(r'<([^>]+)>', from_field)
            if match:
                email = match.group(1)
            else:
                email = from_field.strip()
            
            # Extract domain from email address
            domain = email.split('@')[-1]
            return domain
            
        except Exception as e:
            logger.error(f"Error extracting domain: {e}")
            return ""