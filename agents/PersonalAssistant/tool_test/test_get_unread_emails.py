import unittest
import os
from unittest.mock import patch, MagicMock
from .tools.GetUnreadEmails import GetUnreadEmails

class TestGetUnreadEmails(unittest.TestCase):
    def setUp(self):
        self.tool = GetUnreadEmails()

    @patch('PersonalAssistant.tools.GetUnreadEmails.Credentials')
    @patch('PersonalAssistant.tools.GetUnreadEmails.build')
    def test_get_unread_emails_success(self, mock_build, mock_credentials):
        """Test successful email retrieval"""
        # Mock credentials
        mock_credentials.from_authorized_user_file.return_value = MagicMock(valid=True)
        
        # Mock Gmail API response
        mock_messages = {
            'messages': [
                {'id': '1'},
                {'id': '2'}
            ]
        }
        mock_message_content = {
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'test@example.com'},
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'Date', 'value': '2024-02-20'}
                ]
            }
        }
        
        # Setup mock service
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = mock_messages
        mock_service.users().messages().get().execute.return_value = mock_message_content
        mock_build.return_value = mock_service
        
        # Create mock token.json
        with open('token.json', 'w') as f:
            f.write('{"test": "test"}')
        
        result = self.tool.forward(max_results=2)
        
        # Cleanup
        if os.path.exists('token.json'):
            os.remove('token.json')
        
        # Assertions
        self.assertIsInstance(result, str)
        self.assertIn('test@example.com', result)
        self.assertIn('Test Subject', result)
        self.assertIn('2024-02-20', result)

    def test_get_unread_emails_no_credentials(self):
        """Test behavior when no credentials are available"""
        # Ensure no token.json exists
        if os.path.exists('token.json'):
            os.remove('token.json')
            
        result = self.tool.forward(max_results=2)
        self.assertIn('Error', result)

if __name__ == '__main__':
    unittest.main() 