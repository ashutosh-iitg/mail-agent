"""
Email Classifier module - Classifies emails based on configured rules and LLM analysis.
"""

import re
import logging
from email.utils import parseaddr

logger = logging.getLogger(__name__)

class EmailClassifier:
    """Classifies emails based on configured rules and LLM analysis."""
    
    def __init__(self, label_configs):
        """
        Initialize the classifier with label configurations.
        
        Args:
            label_configs (list): List of label configuration dictionaries.
        """
        self.label_configs = label_configs
    
    def classify(self, email_data):
        """
        Classify an email based on configured rules and LLM analysis.
        
        Args:
            email_data (dict): Email data dictionary.
            
        Returns:
            list: List of labels that apply to the email.
        """
        # First try rule-based classification
        rule_based_labels = self._rule_based_classify(email_data)
        
        # If no labels found or LLM analysis is always enabled, use LLM
        if not rule_based_labels or True:  # TODO: Add config for always using LLM
            llm_labels = self._llm_classify(email_data)
            # Combine labels, removing duplicates
            all_labels = list(set(rule_based_labels + llm_labels))
            return all_labels
        
        return rule_based_labels
    
    def _llm_classify(self, email_data):
        """
        Use LLM to classify an email.
        
        Args:
            email_data (dict): Email data dictionary.
            
        Returns:
            list: List of labels suggested by the LLM.
        """
        # TODO: Implement actual LLM integration
        return self._dummy_llm_call(email_data)
    
    def _dummy_llm_call(self, email_data):
        """
        Placeholder for LLM classification.
        
        Args:
            email_data (dict): Email data dictionary.
            
        Returns:
            list: Empty list for now.
        """
        logger.info("TODO: Implement LLM classification")
        # In a real implementation, we would:
        # 1. Prepare a prompt with the email subject, sender, and content
        # 2. Send it to the LLM API (OpenAI, Anthropic, etc.)
        # 3. Parse the response to extract suggested labels
        
        # For now, return empty list
        return []
    
    def _rule_based_classify(self, email_data):
        """
        Classify an email based on configured rules.
        
        Args:
            email_data (dict): Email data dictionary.
            
        Returns:
            list: List of labels that apply to the email.
        """
        applicable_labels = []
        
        for label_config in self.label_configs:
            if self._matches_criteria(email_data, label_config['criteria']):
                applicable_labels.append(label_config['name'])
        
        return applicable_labels
    
    def _matches_criteria(self, email_data, criteria):
        """
        Check if an email matches the given criteria.
        
        Args:
            email_data (dict): Email data dictionary.
            criteria (dict): Criteria dictionary.
            
        Returns:
            bool: True if the email matches the criteria, False otherwise.
        """
        # Check 'from' criteria
        if 'from' in criteria and criteria['from']:
            sender_email = self._extract_email(email_data['from'])
            if not any(sender_email.lower() == from_addr.lower() for from_addr in criteria['from']):
                if not self._check_alternate_from_criteria(email_data, criteria):
                    return False
        
        # Check 'from_domain' criteria
        if 'from_domain' in criteria and criteria['from_domain']:
            sender_domain = self._extract_domain(email_data['from'])
            if not any(sender_domain.lower().endswith(domain.lower()) for domain in criteria['from_domain']):
                return False
        
        # Check 'subject_contains' criteria
        if 'subject_contains' in criteria and criteria['subject_contains']:
            subject = email_data['subject'].lower()
            if not any(keyword.lower() in subject for keyword in criteria['subject_contains']):
                return False
        
        # Check 'body_contains' criteria
        if 'body_contains' in criteria and criteria['body_contains']:
            body = email_data['body'].lower()
            if not any(keyword.lower() in body for keyword in criteria['body_contains']):
                return False
        
        return True
    
    def _check_alternate_from_criteria(self, email_data, criteria):
        """
        Check alternate 'from' criteria like name or partial match.
        
        Args:
            email_data (dict): Email data dictionary.
            criteria (dict): Criteria dictionary.
            
        Returns:
            bool: True if the email matches alternate criteria, False otherwise.
        """
        if 'from_name' in criteria and criteria['from_name']:
            sender_name = self._extract_name(email_data['from'])
            if any(name.lower() in sender_name.lower() for name in criteria['from_name']):
                return True
        
        return False
    
    def _extract_email(self, from_field):
        """Extract email address from the 'from' field."""
        _, email = parseaddr(from_field)
        return email
    
    def _extract_name(self, from_field):
        """Extract name from the 'from' field."""
        name, _ = parseaddr(from_field)
        return name
    
    def _extract_domain(self, from_field):
        """Extract domain from the 'from' field."""
        _, email = parseaddr(from_field)
        try:
            return email.split('@')[1]
        except (IndexError, AttributeError):
            return ""