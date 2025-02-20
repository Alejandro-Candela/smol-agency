import unittest
import os
from unittest.mock import patch, MagicMock
from agents.PersonalAssistant.tools.SendEmail import SendEmail

class TestSendEmail(unittest.TestCase):
    def setUp(self):
        self.tool = SendEmail()
        self.test_email = {
            'to': 'test@example.com',
            'subject': 'Test Subject',
            'body': 'Test Body',
            'attachments': None
        }

    @patch('PersonalAssistant.tools.SendEmail.Credentials')
    @patch('PersonalAssistant.tools.SendEmail.build')
    def test_send_email_success(self, mock_build, mock_credentials):
        """Test successful email sending"""
        # Mock credentials
        mock_credentials.from_authorized_user_file.return_value = MagicMock(valid=True)
        
        # Mock Gmail API response
        mock_sent_message = {'id': '12345'}
        
        # Setup mock service
        mock_service = MagicMock()
        mock_service.users().messages().send().execute.return_value = mock_sent_message
        mock_build.return_value = mock_service
        
        # Create mock token.json
        with open('token.json', 'w') as f:
            f.write('{"test": "test"}')
        
        result = self.tool.forward(**self.test_email)
        
        # Cleanup
        if os.path.exists('token.json'):
            os.remove('token.json')
        
        # Assertions
        self.assertIsInstance(result, str)
        self.assertIn('successfully', result)
        self.assertIn('12345', result)

    def test_send_email_no_credentials(self):
        """Test behavior when no credentials are available"""
        # Ensure no token.json exists
        if os.path.exists('token.json'):
            os.remove('token.json')
            
        result = self.tool.forward(**self.test_email)
        self.assertIn('Error', result)

    @patch('PersonalAssistant.tools.SendEmail.Credentials')
    @patch('PersonalAssistant.tools.SendEmail.build')
    def test_send_email_with_attachment(self, mock_build, mock_credentials):
        """Test sending email with attachment"""
        # Create test attachment file
        test_file = 'test_attachment.txt'
        with open(test_file, 'w') as f:
            f.write('Test content')
        
        # Mock credentials and service
        mock_credentials.from_authorized_user_file.return_value = MagicMock(valid=True)
        mock_service = MagicMock()
        mock_service.users().messages().send().execute.return_value = {'id': '12345'}
        mock_build.return_value = mock_service
        
        # Create mock token.json
        with open('token.json', 'w') as f:
            f.write('{"test": "test"}')
        
        # Test with attachment
        test_email_with_attachment = self.test_email.copy()
        test_email_with_attachment['attachments'] = [test_file]
        
        result = self.tool.forward(**test_email_with_attachment)
        
        # Cleanup
        if os.path.exists('token.json'):
            os.remove('token.json')
        if os.path.exists(test_file):
            os.remove(test_file)
        
        # Assertions
        self.assertIsInstance(result, str)
        self.assertIn('successfully', result)

    @patch('PersonalAssistant.tools.SendEmail.Credentials')
    @patch('PersonalAssistant.tools.SendEmail.build')
    def test_send_email_invalid_attachment(self, mock_build, mock_credentials):
        """Test behavior with non-existent attachment"""
        # Mock credentials
        mock_credentials.from_authorized_user_file.return_value = MagicMock(valid=True)
        
        # Create mock token.json
        with open('token.json', 'w') as f:
            f.write('{"test": "test"}')
        
        # Test with non-existent attachment
        test_email_invalid = self.test_email.copy()
        test_email_invalid['attachments'] = ['nonexistent.txt']
        
        result = self.tool.forward(**test_email_invalid)
        
        # Cleanup
        if os.path.exists('token.json'):
            os.remove('token.json')
        
        # Assertions
        self.assertIn('Error', result)
        self.assertIn('File not found', result)

if __name__ == '__main__':
    unittest.main() 