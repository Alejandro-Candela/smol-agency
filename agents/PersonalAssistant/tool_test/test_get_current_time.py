import unittest
from datetime import datetime
import pytz
from agents.PersonalAssistant.tools.GetCurrentTime import GetCurrentTime

class TestGetCurrentTime(unittest.TestCase):
    def setUp(self):
        self.tool = GetCurrentTime()

    def test_get_current_time_format(self):
        """Test that the output has the correct format"""
        result = self.tool.forward()
        
        # Check that the result is a string
        self.assertIsInstance(result, str)
        
        # Check that it contains all required parts
        self.assertIn("Current Time (UTC):", result)
        self.assertIn("Date:", result)
        self.assertIn("Day:", result)

    def test_get_current_time_accuracy(self):
        """Test that the time is accurate"""
        result = self.tool.forward()
        current_utc = datetime.now(pytz.UTC)
        
        # Extract the date from the result
        date_line = [line for line in result.split('\n') if "Date:" in line][0]
        result_date = datetime.strptime(date_line.split(': ')[1], '%Y-%m-%d')
        
        # Check that the dates match
        self.assertEqual(result_date.date(), current_utc.date())

if __name__ == '__main__':
    unittest.main() 