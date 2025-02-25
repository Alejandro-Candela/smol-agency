from smolagents import ToolCallingAgent, HfApiModel
from dotenv import load_dotenv
import os
from .tools.MarkdownToExcel import MarkdownToExcel

# Load environment variables
load_dotenv()

model = HfApiModel(model_id=os.getenv('FAST_MODEL'), token=os.getenv('HG_API_TOKEN'), temperature=0.2)

class AccountManager(ToolCallingAgent):
    def __init__(self):
        super().__init__(
            name="AccountManager",
            description="./instructions.md",
            tools=[
                MarkdownToExcel()
            ],
            model=model
        )

    def response_validator(self, message):
        return message
