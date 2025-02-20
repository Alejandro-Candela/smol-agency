from smolagents import (
    CodeAgent,
    HfApiModel,
    GradioUI
)

from agents.WebBrowserAgent.WebBrowserAgent import WebBrowserAgent
from agents.AccountManager.AccountManager import AccountManager
from agents.PersonalAssistant.PersonalAssistant import PersonalAssistant
from agents.WebBrowserAgent.tools.visual_qa import visualizer
from agents.WebBrowserAgent.tools.text_inspector_tool import TextInspectorTool

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

model = HfApiModel(model_id=os.getenv('FAST_MODEL'), token=os.getenv('HG_API_TOKEN'), max_tokens=5000)

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
assistant = PersonalAssistant()
account_manager = AccountManager()
text_webbrowser_agent = WebBrowserAgent()

text_webbrowser_agent.prompt_templates["managed_agent"]["task"] += """You can navigate to .txt online files.
    If a non-html page is in another format, especially .pdf or a Youtube video, use tool 'inspect_file_as_text' to inspect it.
    Additionally, if after some searching you find out that you need more information to answer the question, you can use `final_answer` with your request for clarification as argument to request for more information."""

# Create the agency with the personal assistant
manager_agent = CodeAgent(
    model=model,
    max_steps=10,
    add_base_tools = False,
    managed_agents=[assistant, account_manager],
    description='agency_manifesto.md',
    additional_authorized_imports=AUTHORIZED_IMPORTS,
    tools=[visualizer, document_inspection_tool]
)

if __name__ == "__main__":
    # manager_agent.run("Que dia es hoy? Utiliza el agente PersonalAssistant para obtener la fecha actual.")  # starts the agency in terminal 
    # demo_gradio(manager_agent)  # starts the agency in gradio 
    GradioUI(manager_agent, file_upload_folder="./data").launch(share=True)   