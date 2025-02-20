from smolagents import (
    CodeAgent,
    HfApiModel,
    GradioUI
)
from PersonalAssistant import PersonalAssistant
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

model = HfApiModel(model_id=os.getenv('FAST_MODEL'), token=os.getenv('HG_API_TOKEN'), max_tokens=5000, temperature=0.7)

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

# Initialize the personal assistant
assistant = PersonalAssistant()

# Create the agency with the personal assistant
manager_agent = CodeAgent(
    model=model,
    max_steps=10,
    add_base_tools = False,
    managed_agents=[assistant],
    description='agency_manifesto.md',
    additional_authorized_imports=AUTHORIZED_IMPORTS,
    tools=[]
)

if __name__ == "__main__":
    # manager_agent.run("Que dia es hoy? Utiliza el agente PersonalAssistant para obtener la fecha actual.")  # starts the agency in terminal 
    # demo_gradio(manager_agent)  # starts the agency in gradio 
    GradioUI(manager_agent, file_upload_folder="./data").launch(share=True)   