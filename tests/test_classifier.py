import unittest
from src.classifier import EmailClassifier

class TestEmailClassifier(unittest.TestCase):

    def setUp(self):
        # Setup test label configs
        self.label_configs = [
            {
                'name': 'Important',
                'criteria': {
                    'from': ['boss@company.com'],
                    'subject_contains': ['urgent'],
                    'notify': True
                }
            },
            {
                'name': 'Work',
                'criteria': {
                    'from_domain': ['company.com'],
                    'notify': False
                }
            }
        ]
        
        self.classifier = EmailClassifier(self.label_configs)
    
    def test_rule_based_classify_important(self):
        # Test email that should be classified as Important
        email_data = {
            'subject': 'Urgent meeting',
            'from': 'boss@company.com',
            'to': 'employee@company.com',
            'body': 'We need to meet ASAP',
            'date': 'Mon, 16 Mar 2025 10:00:00 +0000'
        }
        
        labels = self.classifier._rule_based_classify(email_data)
        self.assertIn('Important', labels)
    
    def test_rule_based_classify_work(self):
        # Test email that should be classified as Work
        email_data = {
            'subject': 'Team update',
            'from': 'colleague@company.com',
            'to': 'employee@company.com',
            'body': 'Here is the latest team update',
            'date': 'Mon, 16 Mar 2025 10:00:00 +0000'
        }
        
        labels = self.classifier._rule_based_classify(email_data)
        self.assertIn('Work', labels)
    
    def test_rule_based_classify_no_match(self):
        # Test email that shouldn't match any labels
        email_data = {
            'subject': 'Hello',
            'from': 'friend@example.com',
            'to': 'employee@company.com',
            'body': 'Just saying hello',
            'date': 'Mon, 16 Mar 2025 10:00:00 +0000'
        }
        
        labels = self.classifier._rule_based_classify(email_data)
        self.assertEqual(len(labels), 0)
    
    def test_extract_domain(self):
        # Test extracting domain from email
        domain = self.classifier._extract_domain('John Doe <john.doe@example.com>')
        self.assertEqual(domain, 'example.com')
        
        domain = self.classifier._extract_domain('simple@example.com')
        self.assertEqual(domain, 'example.com')
    
    def test_extract_name(self):
        # Test extracting name from email
        name = self.classifier._extract_name('John Doe <john.doe@example.com>')
        self.assertEqual(name, 'John Doe')
        
        name = self.classifier._extract_name('simple@example.com')
        self.assertEqual(name, '')

if __name__ == '__main__':
    unittest.main()