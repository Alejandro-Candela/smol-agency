from smolagents import ToolCallingAgent, HfApiModel, LiteLLMModel
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
from .tools.visual_qa import VisualQATool

# Load environment variables
load_dotenv()

append_answer_lock = threading.Lock()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "question",
        type=str,
        help="for example: 'How many studio albums did Mercedes Sosa release before 2007?'",
    )
    parser.add_argument("--model-id", type=str, default="o1")
    return parser.parse_args()


custom_role_conversions = {"tool-call": "assistant", "tool-response": "user"}

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"

BROWSER_CONFIG = {
    "viewport_size": 1024 * 5,
    "downloads_folder": "downloads_folder",
    "request_kwargs": {
        "headers": {"User-Agent": user_agent},
        "timeout": 300,
    },
    "zenrows_key": os.getenv("ZENROWS_API_KEY"),
}

os.makedirs(f"./{BROWSER_CONFIG['downloads_folder']}", exist_ok=True)

model = HfApiModel(
    model_id="Qwen/Qwen2.5-Coder-32B-Instruct",
    custom_role_conversions={"tool-call": "assistant", "tool-response": "user"},
    token=os.getenv("HG_API_TOKEN"),
    max_tokens=8192,
)

args = parse_args()
text_limit = 100000

document_inspection_tool = TextInspectorTool(model, text_limit)

browser = SimpleTextBrowser(**BROWSER_CONFIG)

WEB_TOOLS = [
    SearchInformationTool(browser),
    VisitTool(browser),
    PageUpTool(browser),
    PageDownTool(browser),
    FinderTool(browser),
    FindNextTool(browser),
    ArchiveSearchTool(browser),
    TextInspectorTool(model, text_limit),
    VisualQATool(),
]


class WebBrowserAgent(ToolCallingAgent):
    def __init__(self):
        super().__init__(
            model=model,
            tools=WEB_TOOLS,
            max_steps=10,
            verbosity_level=2,
            planning_interval=4,
            name="web_browser_agent",
            description="""A team member that will search the internet to answer your question.
    Ask him for all your questions that require browsing the web.
    Provide him as much context as possible, in particular if you need to search on a specific timeframe!
    And don't hesitate to provide him with a complex search task, like finding a difference between two webpages.
    Your request must be a real sentence, not a google search! Like "Find me this information (...)" rather than a few keywords.
    """,
            provide_run_summary=True,
        )

    def response_validator(self, message):
        return message
