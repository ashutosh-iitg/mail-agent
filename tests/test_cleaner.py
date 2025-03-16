import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from src.cleaner import EmailCleaner

class TestEmailCleaner(unittest.TestCase):

    def setUp(self):
        # Setup test cleaning config
        self.cleaning_config = {
            'delete_newsletters': True,
            'newsletter_domains': ['newsletter.com', 'marketing.com'],
            'delete_older_than': 30,
            'delete_read': True
        }
        
        self.cleaner = EmailCleaner(self.cleaning_config)
    
    def test_is_newsletter_domain(self):
        # Test newsletter detection by domain
        email = {
            'subject': 'Latest news',
            'from': 'info@newsletter.com',
            'body': 'Here are the latest news'
        }
        
        self.assertTrue(self.cleaner._is_newsletter(email))
    
    def test_is_newsletter_subject(self):
        # Test newsletter detection by subject
        email = {
            'subject': 'Your weekly newsletter',
            'from': 'info@example.com',
            'body': 'Here are the latest news'
        }
        
        self.assertTrue(self.cleaner._is_newsletter(email))
    
    def test_is_newsletter_body(self):
        # Test newsletter detection by body
        email = {
            'subject': 'Updates',
            'from': 'info@example.com',
            'body': 'Here are some updates. Click here to unsubscribe.'
        }
        
        self.assertTrue(self.cleaner._is_newsletter(email))
    
    def test_is_not_newsletter(self):
        # Test not newsletter
        email = {
            'subject': 'Hello',
            'from': 'friend@example.com',
            'body': 'Just saying hello'
        }
        
        self.assertFalse(self.cleaner._is_newsletter(email))
    
    def test_is_too_old(self):
        # Test email age detection
        old_date = (datetime.now() - timedelta(days=40)).strftime('%a, %d %b %Y %H:%M:%S %z')
        recent_date = (datetime.now() - timedelta(days=10)).strftime('%a, %d %b %Y %H:%M:%S %z')
        
        old_email = {
            'subject': 'Old email',
            'from': 'sender@example.com',
            'body': 'This is an old email',
            'date': old_date
        }
        
        recent_email = {
            'subject': 'Recent email',
            'from': 'sender@example.com',
            'body': 'This is a recent email',
            'date': recent_date
        }
        
        with patch('src.cleaner.parsedate_to_datetime') as mock_parse:
            # Mock date parsing for old email
            mock_parse.return_value = datetime.now() - timedelta(days=40)
            self.assertTrue(self.cleaner._is_too_old(old_email, 30))
            
            # Mock date parsing for recent email
            mock_parse.return_value = datetime.now() - timedelta(days=10)
            self.assertFalse(self.cleaner._is_too_old(recent_email, 30))
    
    def test_is_read_gmail(self):
        # Test read detection for Gmail
        read_email = {
            'subject': 'Read email',
            'from': 'sender@example.com',
            'body': 'This is a read email',
            'labels': ['INBOX', 'CATEGORY_PERSONAL']
        }
        
        unread_email = {
            'subject': 'Unread email',
            'from': 'sender@example.com',
            'body': 'This is an unread email',
            'labels': ['INBOX', 'UNREAD', 'CATEGORY_PERSONAL']
        }
        
        self.assertTrue(self.cleaner._is_read(read_email))
        self.assertFalse(self.cleaner._is_read(unread_email))
    
    def test_is_read_imap(self):
        # Test read detection for IMAP
        read_email = {
            'subject': 'Read email',
            'from': 'sender@example.com',
            'body': 'This is a read email',
            'flags': ['\\Seen', '\\Recent']
        }
        
        unread_email = {
            'subject': 'Unread email',
            'from': 'sender@example.com',
            'body': 'This is an unread email',
            'flags': ['\\Recent']
        }
        
        self.assertTrue(self.cleaner._is_read(read_email))
        self.assertFalse(self.cleaner._is_read(unread_email))
    
    def test_clean(self):
        # Test cleaning process
        email_provider = MagicMock()
        
        # Setup test emails
        emails = [
            {
                'id': '1',
                'subject': 'Newsletter',
                'from': 'info@newsletter.com',
                'body': 'Here are the latest news',
                'date': (datetime.now() - timedelta(days=10)).strftime('%a, %d %b %Y %H:%M:%S %z'),
                'labels': ['INBOX']
            },
            {
                'id': '2',
                'subject': 'Old email',
                'from': 'sender@example.com',
                'body': 'This is an old email',
                'date': (datetime.now() - timedelta(days=40)).strftime('%a, %d %b %Y %H:%M:%S %z'),
                'labels': ['INBOX', 'UNREAD']
            },
            {
                'id': '3',
                'subject': 'Read email',
                'from': 'sender@example.com',
                'body': 'This is a read email',
                'date': (datetime.now() - timedelta(days=10)).strftime('%a, %d %b %Y %H:%M:%S %z'),
                'labels': ['INBOX']
            },
            {
                'id': '4',
                'subject': 'Keep me',
                'from': 'important@example.com',
                'body': 'This email should be kept',
                'date': (datetime.now() - timedelta(days=10)).strftime('%a, %d %b %Y %H:%M:%S %z'),
                'labels': ['INBOX', 'UNREAD']
            }
        ]
        
        # Mock email provider methods
        email_provider.get_all_emails.return_value = emails
        email_provider.delete_email.return_value = True
        
        # Mock date parsing for the is_too_old method
        with patch('src.cleaner.parsedate_to_datetime') as mock_parse:
            def side_effect(date_str):
                if 'Old email' in next((e['subject'] for e in emails if e['date'] == date_str), ''):
                    return datetime.now() - timedelta(days=40)
                return datetime.now() - timedelta(days=10)
            
            mock_parse.side_effect = side_effect
            
            # Call the clean method
            cleaned_count = self.cleaner.clean(email_provider)
            
            # Check that the correct emails were deleted
            self.assertEqual(cleaned_count, 3)
            self.assertEqual(email_provider.delete_email.call_count, 3)
            
            # Check that the emails with IDs 1, 2, and 3 were deleted
            email_provider.delete_email.assert_any_call(emails[0])  # Newsletter
            email_provider.delete_email.assert_any_call(emails[1])  # Old email
            email_provider.delete_email.assert_any_call(emails[2])  # Read email

if __name__ == '__main__':
    unittest.main()