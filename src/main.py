#!/usr/bin/env python3
"""
Mail Agent - Automated email management system.
Main entry point for the application.
"""

import os
import time
import logging
from dotenv import load_dotenv
import schedule
import yaml

from email_provider import get_email_provider
from classifier import EmailClassifier
from notifier import Notifier
from cleaner import EmailCleaner

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("mail_agent.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from YAML file."""
    try:
        with open("config/config.yaml", "r") as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise


def process_emails(config):
    """Main function to process emails."""
    # try:
    # Get the email provider
    email_provider = get_email_provider(config["email"])

    import pdb

    pdb.set_trace()

    # Initialize components
    classifier = EmailClassifier(config["labels"])
    notifier = Notifier(config["notifications"])
    cleaner = EmailCleaner(config["cleaning"])

    # Get unprocessed emails
    emails = email_provider.get_unprocessed_emails()
    logger.info(f"Found {len(emails)} unprocessed emails")

    for email in emails:
        # Classify email
        labels = classifier.classify(email)

        # Apply labels
        if labels:
            email_provider.apply_labels(email, labels)
            logger.info(f"Applied labels {labels} to email: {email['subject']}")

        # Send notifications if needed
        for label in labels:
            label_config = next(
                (l for l in config["labels"] if l["name"] == label), None
            )
            if label_config and label_config.get("notify", False):
                notifier.send_notification(email)
                logger.info(f"Sent notification for email: {email['subject']}")

        # Mark as processed
        email_provider.mark_as_processed(email)

    # Clean up emails
    cleaned_count = cleaner.clean(email_provider)
    logger.info(f"Cleaned {cleaned_count} emails")

    # except Exception as e:
    #     logger.error(f"Error processing emails: {e}")


def main():
    """Main entry point for the application."""
    try:
        # Load environment variables from .env file
        load_dotenv()

        # Load configuration
        config = load_config()

        # Process emails immediately on startup
        process_emails(config)

        # Schedule regular processing
        schedule.every(config["email"]["check_frequency"]).seconds.do(
            process_emails, config
        )

        # Keep the script running
        logger.info("Mail Agent started. Press Ctrl+C to exit.")
        while True:
            schedule.run_pending()
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Mail Agent stopped.")
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main()
