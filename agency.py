from smolagents import (
    CodeAgent,
    DuckDuckGoSearchTool,
    HfApiModel,
    LiteLLMModel
)

from gradio_agent import GradioUI

from demo_gradio import demo_gradio

from agents.WebBrowserAgent.WebBrowserAgent import WebBrowserAgent
from agents.PersonalAssistant.PersonalAssistant import PersonalAssistant
from agents.WebBrowserAgent.tools.visual_qa import visualizer
from agents.WebBrowserAgent.tools.text_inspector_tool import TextInspectorTool
from basic_tools import MarkdownToExcel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

model = LiteLLMModel(model_id=os.getenv('SMART_MODEL'), token=os.getenv('GEMINI_API_KEY'))

text_limit = 100000
document_inspection_tool = TextInspectorTool(model, text_limit)

AUTHORIZED_IMPORTS = [
    "requests",
    "zipfile",
    "os",
    "pandas",
    "numpy",
    "sympy",
    "json",
    "bs4",
    "pubchempy",
    "xml",
    "yahoo_finance",
    "Bio",
    "sklearn",
    "scipy",
    "pydub",
    "io",
    "PIL",
    "chess",
    "PyPDF2",
    "pptx",
    "torch",
    "datetime",
    "fractions",
    "csv",
]

# Initialize the agents
personal_assistant = PersonalAssistant()
webbrowser_agent = WebBrowserAgent()

webbrowser_agent.prompt_templates["managed_agent"]["task"] += """You can navigate to .txt online files.
    If a non-html page is in another format, especially .pdf or a Youtube video, use tool 'inspect_file_as_text' to inspect it.
    Additionally, if after some searching you find out that you need more information to answer the question, you can use `final_answer` with your request for clarification as argument to request for more information."""

def read_markdown_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# Load the agency description from the markdown file
agency_description = read_markdown_file('agency_manifesto.md')

# Create the agency with the personal assistant
manager_agent = CodeAgent(
    name="Agency Manager",
    model=model,
    max_steps=10,
    add_base_tools = True,
    managed_agents=[personal_assistant, webbrowser_agent],
    additional_authorized_imports=AUTHORIZED_IMPORTS,
    tools=[visualizer, document_inspection_tool, MarkdownToExcel()]
)

manager_agent.prompt_templates["system_prompt"] += agency_description

if __name__ == "__main__":
    # manager_agent.run("Que dia es hoy? Utiliza el agente PersonalAssistant para obtener la fecha actual.")  # starts the agency in terminal 
    # demo_gradio(manager_agent)  # starts the agency in gradio
    GradioUI(manager_agent, file_upload_folder="./data").launch(share=True)
    