from smolagents import ToolCallingAgent, HfApiModel
from dotenv import load_dotenv
import os
from .tools.GetCurrentTime import GetCurrentTime
from .tools.GetUnreadEmails import GetUnreadEmails
from .tools.FetchDailyMeetingSchedule import FetchDailyMeetingSchedule

# Load environment variables
load_dotenv()

model = HfApiModel(model_id=os.getenv('FAST_MODEL'), token=os.getenv('HG_API_TOKEN'), max_tokens=5000, temperature=0.7)

class PersonalAssistant(ToolCallingAgent):
    def __init__(self):
        super().__init__(
            name="PersonalAssistant",
            description="./instructions.md",
            tools=[GetUnreadEmails(), GetCurrentTime(), FetchDailyMeetingSchedule()],
            model=model
        )

    def response_validator(self, message):
        return message
