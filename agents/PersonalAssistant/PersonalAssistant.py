from smolagents import ToolCallingAgent, LiteLLMModel, HfApiModel
from dotenv import load_dotenv
import os
from .tools.GetCurrentTime import GetCurrentTime
from .tools.GetUnreadEmails import GetUnreadEmails
from .tools.FetchDailyMeetingSchedule import FetchDailyMeetingSchedule
from .tools.SendEmail import SendEmail

# Load environment variables
load_dotenv()

model = HfApiModel(
    model_id=os.getenv("FAST_MODEL"), token=os.getenv("HG_API_TOKEN"), temperature=0.2
)


def read_markdown_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

# Load the agent description from the markdown file
personal_assistant_description = read_markdown_file('personal_assistant_instructions.md')


class PersonalAssistant(ToolCallingAgent):
    def __init__(self):
        super().__init__(
            name="personal_assistant",
            description=personal_assistant_description,
            max_steps=5,
            tools=[
                GetUnreadEmails(),
                GetCurrentTime(),
                FetchDailyMeetingSchedule(),
                SendEmail(),
            ],
            model=model,
        )
        

    def response_validator(self, message):
        return message
