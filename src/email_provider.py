"""
Email Provider module - Handles different email service providers.
"""

import os
import logging
import imaplib
import email
from email.header import decode_header
from abc import ABC, abstractmethod
import re

# For Gmail API
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

def get_email_provider(config):
    """Factory function to get the appropriate email provider."""
    provider_type = config.get('provider', 'auto').lower()
    
    if provider_type == 'auto':
        # Auto-detect based on email domain
        email_address = config.get('other', {}).get('username', '')
        if '@gmail.com' in email_address:
            provider_type = 'gmail'
        else:
            provider_type = 'other'
    
    if provider_type == 'gmail':
        return GmailProvider(config['gmail'])
    else:
        return ImapProvider(config['other'])

class EmailProvider(ABC):
    """Abstract base class for email providers."""
    
    @abstractmethod
    def get_unprocessed_emails(self):
        """Get unprocessed emails."""
        pass
    
    @abstractmethod
    def apply_labels(self, email_data, labels):
        """Apply labels to an email."""
        pass
    
    @abstractmethod
    def mark_as_processed(self, email_data):
        """Mark an email as processed."""
        pass
    
    @abstractmethod
    def delete_email(self, email_data):
        """Delete an email."""
        pass
    
    @abstractmethod
    def move_to_folder(self, email_data, folder):
        """Move an email to a folder."""
        pass

class GmailProvider(EmailProvider):
    """Gmail API provider."""
    
    def __init__(self, config):
        self.config = config
        self.service = self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API."""
        creds = None
        token_file = self.config['token_file']
        
        # Check if token.json exists
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If credentials don't exist or are invalid, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config['credentials_file'], self.config['scopes'])
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        # Build the Gmail service
        return build('gmail', 'v1', credentials=creds)
    
    def get_unprocessed_emails(self):
        """Get unprocessed emails from Gmail."""
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            print(labels)
            # Get messages without the "Processed" label
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread'
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for num,message in enumerate(messages):
                msg = self.service.users().messages().get(
                    userId='me', 
                    id=message['id'],
                    format='full'
                ).execute()

                
                # Extract email details
                headers = {header['name']: header['value'] for header in msg['payload']['headers']}
                
                email_data = {
                    'id': message['id'],
                    'subject': headers.get('Subject', ''),
                    'from': headers.get('From', ''),
                    'to': headers.get('To', ''),
                    'date': headers.get('Date', ''),
                    'body': self._get_email_body(msg),
                    'labels': msg['labelIds']
                }


                emails.append(email_data)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error getting emails from Gmail: {e}")
            return []
    
    def _get_email_body(self, message):
        """Extract email body from Gmail message."""
        payload = message['payload']
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    return self._decode_part(part)
        elif 'body' in payload and 'data' in payload['body']:
            return self._decode_part(payload)
        
        return ""
    
    def _decode_part(self, part):
        """Decode a message part."""
        if 'body' in part and 'data' in part['body']:
            from base64 import urlsafe_b64decode
            data = part['body']['data']
            data = data.replace('-', '+').replace('_', '/')
            return urlsafe_b64decode(data).decode('utf-8')
        return ""
    
    def apply_labels(self, email_data, labels):
        """Apply labels to a Gmail message."""
        try:
            # Make sure the labels exist
            for label in labels:
                self._ensure_label_exists(label)
            
            # Apply the labels
            self.service.users().messages().modify(
                userId='me',
                id=email_data['id'],
                body={'addLabelIds': labels}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error applying labels: {e}")
            return False
    
    def _ensure_label_exists(self, label_name):
        """Ensure a label exists in Gmail."""
        try:
            # Get all labels
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            # Check if label exists
            if not any(label['name'] == label_name for label in labels):
                # Create the label
                self.service.users().labels().create(
                    userId='me',
                    body={'name': label_name}
                ).execute()
                logger.info(f"Created new label: {label_name}")
        except Exception as e:
            logger.error(f"Error ensuring label exists: {e}")
    
    def mark_as_processed(self, email_data):
        """Mark a Gmail message as processed."""
        try:
            # Make sure the "Processed" label exists
            self._ensure_label_exists("Processed")
            
            # Add the "Processed" label
            self.service.users().messages().modify(
                userId='me',
                id=email_data['id'],
                body={'addLabelIds': ['Processed']}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error marking email as processed: {e}")
            return False
    
    def delete_email(self, email_data):
        """Delete a Gmail message (move to trash)."""
        try:
            self.service.users().messages().trash(
                userId='me',
                id=email_data['id']
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting email: {e}")
            return False
    
    def move_to_folder(self, email_data, folder):
        """Move a Gmail message to a folder (label in Gmail)."""
        try:
            # In Gmail, moving to a folder is applying a label and removing INBOX
            self._ensure_label_exists(folder)
            
            self.service.users().messages().modify(
                userId='me',
                id=email_data['id'],
                body={
                    'addLabelIds': [folder],
                    'removeLabelIds': ['INBOX']
                }
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error moving email to folder: {e}")
            return False

class ImapProvider(EmailProvider):
    """IMAP email provider for non-Gmail services."""
    
    def __init__(self, config):
        self.config = config
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Connect to the IMAP server."""
        try:
            self.conn = imaplib.IMAP4_SSL(self.config['imap_server'], self.config['port'])
            self.conn.login(self.config['username'], self.config['password'])
            logger.info(f"Connected to IMAP server: {self.config['imap_server']}")
        except Exception as e:
            logger.error(f"Error connecting to IMAP server: {e}")
            self.conn = None
    
    def get_unprocessed_emails(self):
        """Get unprocessed emails via IMAP."""
        if not self.conn:
            self._connect()
            if not self.conn:
                return []
        
        try:
            # Select the inbox
            self.conn.select('INBOX')
            
            # Search for unprocessed emails (not flagged as seen)
            status, data = self.conn.search(None, 'UNSEEN')
            
            if status != 'OK':
                logger.error("Error searching for emails")
                return []
            
            email_ids = data[0].split()
            emails = []
            
            for email_id in email_ids:
                status, data = self.conn.fetch(email_id, '(RFC822)')
                
                if status != 'OK':
                    logger.error(f"Error fetching email {email_id}")
                    continue
                
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Get email details
                subject = self._decode_header(msg['Subject'])
                from_ = self._decode_header(msg['From'])
                to = self._decode_header(msg['To'])
                date = msg['Date']
                
                # Get email body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get('Content-Disposition'))
                        
                        if content_type == 'text/plain' and 'attachment' not in content_disposition:
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()
                
                email_data = {
                    'id': email_id.decode(),
                    'subject': subject,
                    'from': from_,
                    'to': to,
                    'date': date,
                    'body': body,
                    'raw_message': msg
                }
                
                emails.append(email_data)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error getting emails via IMAP: {e}")
            return []
    
    def _decode_header(self, header):
        """Decode email header."""
        if header is None:
            return ""
            
        decoded_header, encoding = decode_header(header)[0]
        if isinstance(decoded_header, bytes):
            if encoding:
                return decoded_header.decode(encoding)
            else:
                return decoded_header.decode('utf-8', errors='ignore')
        return decoded_header
    
    def apply_labels(self, email_data, labels):
        """Apply labels (flags in IMAP) to an email."""
        if not self.conn:
            self._connect()
            if not self.conn:
                return False
        
        try:
            for label in labels:
                # In IMAP, we can only apply certain flags
                if label.upper() in ['SEEN', 'FLAGGED', 'ANSWERED', 'DELETED', 'DRAFT']:
                    self.conn.store(email_data['id'].encode(), '+FLAGS', f'\\{label}')
            return True
        except Exception as e:
            logger.error(f"Error applying labels via IMAP: {e}")
            return False
    
    def mark_as_processed(self, email_data):
        """Mark an email as processed (seen in IMAP)."""
        if not self.conn:
            self._connect()
            if not self.conn:
                return False
        
        try:
            self.conn.store(email_data['id'].encode(), '+FLAGS', '\\Seen')
            return True
        except Exception as e:
            logger.error(f"Error marking email as processed via IMAP: {e}")
            return False
    
    def delete_email(self, email_data):
        """Delete an email via IMAP."""
        if not self.conn:
            self._connect()
            if not self.conn:
                return False
        
        try:
            self.conn.store(email_data['id'].encode(), '+FLAGS', '\\Deleted')
            self.conn.expunge()
            return True
        except Exception as e:
            logger.error(f"Error deleting email via IMAP: {e}")
            return False
    
    def move_to_folder(self, email_data, folder):
        """Move an email to a folder via IMAP."""
        if not self.conn:
            self._connect()
            if not self.conn:
                return False
        
        try:
            # Copy the message to the destination folder
            result = self.conn.copy(email_data['id'].encode(), folder)
            
            if result[0] == 'OK':
                # Delete the original message
                self.conn.store(email_data['id'].encode(), '+FLAGS', '\\Deleted')
                self.conn.expunge()
                return True
            else:
                logger.error(f"Error copying email to folder: {result}")
                return False
        except Exception as e:
            logger.error(f"Error moving email to folder via IMAP: {e}")
            return False

    def __del__(self):
        """Close the IMAP connection when the object is destroyed."""
        if self.conn:
            try:
                self.conn.close()
                self.conn.logout()
            except:
                pass