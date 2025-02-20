from smolagents import Tool
from datetime import datetime
import pytz

class GetCurrentTime(Tool):
    name = "get_current_time"
    description = """
    Returns the current time in UTC format, including date and day of the week.
    The time is returned in a formatted string with time, date, and day information."""
    inputs = {}  # No inputs needed for this tool
    output_type = "string"

    def forward(self):
        try:
            # Get current UTC time
            utc_now = datetime.now(pytz.UTC)
            
            # Format the time string
            time_str = (
                f"Current Time (UTC): {utc_now.strftime('%I:%M %p')}\n"
                f"Date: {utc_now.strftime('%Y-%m-%d')}\n"
                f"Day: {utc_now.strftime('%A')}"
            )
            
            return time_str
            
        except Exception as e:
            return f"Error getting current time: {str(e)}"

if __name__ == "__main__":
    tool = GetCurrentTime()
    print(tool.forward()) 