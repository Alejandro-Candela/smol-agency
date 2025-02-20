from smolagents import ToolCallingAgent, HfApiModel
from dotenv import load_dotenv
import os
import argparse
import os
import threading

from dotenv import load_dotenv
from huggingface_hub import login
from .tools.text_inspector_tool import TextInspectorTool
from .tools.text_web_browser import (
    ArchiveSearchTool,
    FinderTool,
    FindNextTool,
    PageDownTool,
    PageUpTool,
    SearchInformationTool,
    SimpleTextBrowser,
    VisitTool,
)
from .tools.visual_qa import visualizer
# Load environment variables
load_dotenv()

append_answer_lock = threading.Lock()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "question", type=str, help="for example: 'How many studio albums did Mercedes Sosa release before 2007?'"
    )
    parser.add_argument("--model-id", type=str, default="o1")
    return parser.parse_args()


custom_role_conversions = {"tool-call": "assistant", "tool-response": "user"}

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"

model = HfApiModel(model_id=os.getenv('FAST_MODEL'), token=os.getenv('HG_API_TOKEN'), max_tokens=5000, temperature=0.2)

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
