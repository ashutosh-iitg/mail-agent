# Mail Agent

An automated email management system that:
- Labels incoming emails based on content and sender using both rule-based and LLM-powered classification
- Sends notifications for important emails via SMS, WhatsApp, email, or Pushover
- Cleans your inbox by removing spam and unwanted newsletters
- Organizes emails into appropriate folders

## Features

- **Smart Email Classification**: Uses both rule-based and LLM classification to categorize emails
- **Multiple Email Provider Support**: Works with Gmail (via Gmail API) and other email providers (via IMAP)
- **Multiple Notification Methods**: Get notified about important emails via SMS, WhatsApp, email or Pushover
- **Inbox Cleaning**: Automatically delete newsletters, old emails, and read emails based on your preferences
- **Customizable Rules**: Configure your own labeling and notification rules

## Setup and Installation

1. Clone the repository
2. Install dependencies:
```
pip install -r requirements.txt
```

3. Configure your email and notification settings in `config/config.yaml`
4. Create a `.env` file with your API keys and passwords:
```
EMAIL_PASSWORD=your_email_password
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
PUSHOVER_TOKEN=your_pushover_token
PUSHOVER_USER=your_pushover_user
```

5. For Gmail API, you'll need to set up OAuth2 credentials:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Gmail API
   - Create OAuth2 credentials
   - Download the credentials.json file and place it in the project root

## Usage

Run the mail agent:
```
python src/main.py
```

The agent will run continuously, checking for new emails based on the configured frequency.

## Configuration

Edit `config/config.yaml` to customize:

- Email provider settings
- Label rules and criteria
- Cleaning preferences
- Notification methods and settings