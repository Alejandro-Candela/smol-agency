import unittest
import os
from unittest.mock import patch, MagicMock
from datetime import datetime
import pytz
from ..agents.PersonalAssistant.tools.FetchDailyMeetingSchedule import FetchDailyMeetingSchedule

class TestFetchDailyMeetingSchedule(unittest.TestCase):
    def setUp(self):
        self.tool = FetchDailyMeetingSchedule()
        self.test_date = "2024-02-20"

    @patch('PersonalAssistant.tools.FetchDailyMeetingSchedule.Credentials')
    @patch('PersonalAssistant.tools.FetchDailyMeetingSchedule.build')
    def test_fetch_meetings_success(self, mock_build, mock_credentials):
        """Test successful meeting retrieval"""
        # Mock credentials
        mock_credentials.from_authorized_user_file.return_value = MagicMock(valid=True)
        
        # Mock Calendar API response
        mock_events = {
            'items': [
                {
                    'summary': 'Test Meeting',
                    'start': {'dateTime': '2024-02-20T10:00:00Z'},
                    'end': {'dateTime': '2024-02-20T11:00:00Z'},
                    'location': 'Room 1',
                    'description': 'Test Description'
                }
            ]
        }
        
        # Setup mock service
        mock_service = MagicMock()
        mock_service.events().list().execute.return_value = mock_events
        mock_build.return_value = mock_service
        
        # Create mock token.json
        with open('token.json', 'w') as f:
            f.write('{"test": "test"}')
        
        result = self.tool.forward(date=self.test_date)
        
        # Cleanup
        if os.path.exists('token.json'):
            os.remove('token.json')
        
        # Assertions
        self.assertIsInstance(result, str)
        self.assertIn('Test Meeting', result)
        self.assertIn('Room 1', result)
        self.assertIn('Test Description', result)

    def test_fetch_meetings_no_credentials(self):
        """Test behavior when no credentials are available"""
        # Ensure no token.json exists
        if os.path.exists('token.json'):
            os.remove('token.json')
            
        result = self.tool.forward(date=self.test_date)
        self.assertIn('Error', result)

    @patch('PersonalAssistant.tools.FetchDailyMeetingSchedule.Credentials')
    @patch('PersonalAssistant.tools.FetchDailyMeetingSchedule.build')
    def test_fetch_meetings_no_events(self, mock_build, mock_credentials):
        """Test behavior when no meetings are scheduled"""
        # Mock credentials
        mock_credentials.from_authorized_user_file.return_value = MagicMock(valid=True)
        
        # Mock empty Calendar API response
        mock_events = {'items': []}
        
        # Setup mock service
        mock_service = MagicMock()
        mock_service.events().list().execute.return_value = mock_events
        mock_build.return_value = mock_service
        
        # Create mock token.json
        with open('token.json', 'w') as f:
            f.write('{"test": "test"}')
        
        result = self.tool.forward(date=self.test_date)
        
        # Cleanup
        if os.path.exists('token.json'):
            os.remove('token.json')
        
        # Assertions
        self.assertIn('No meetings scheduled', result)

if __name__ == '__main__':
    unittest.main() 