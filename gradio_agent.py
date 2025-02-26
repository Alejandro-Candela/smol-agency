import mimetypes
import os
import re
import shutil
from typing import Optional

from smolagents.agent_types import AgentAudio, AgentImage, AgentText, handle_agent_output_types
from smolagents.agents import ActionStep, MultiStepAgent
from smolagents.memory import MemoryStep
from smolagents.utils import _is_package_available


def pull_messages_from_step(
    step_log: MemoryStep,
):
    """Extract ChatMessage objects from agent steps with proper nesting"""
    import gradio as gr

    if isinstance(step_log, ActionStep):
        # Output the step number
        step_number = f"Step {step_log.step_number}" if step_log.step_number is not None else ""
        yield gr.ChatMessage(role="assistant", content=f"**{step_number}**")

        # First yield the thought/reasoning from the LLM
        if hasattr(step_log, "model_output") and step_log.model_output is not None:
            # Clean up the LLM output
            model_output = step_log.model_output.strip()
            # Remove any trailing <end_code> and extra backticks, handling multiple possible formats
            model_output = re.sub(r"```\s*<end_code>", "```", model_output)  # handles ```<end_code>
            model_output = re.sub(r"<end_code>\s*```", "```", model_output)  # handles <end_code>```
            model_output = re.sub(r"```\s*\n\s*<end_code>", "```", model_output)  # handles ```\n<end_code>
            model_output = model_output.strip()
            yield gr.ChatMessage(role="assistant", content=model_output)

        # For tool calls, create a parent message
        if hasattr(step_log, "tool_calls") and step_log.tool_calls is not None:
            first_tool_call = step_log.tool_calls[0]
            used_code = first_tool_call.name == "python_interpreter"
            parent_id = f"call_{len(step_log.tool_calls)}"

            # Tool call becomes the parent message with timing info
            # First we will handle arguments based on type
            args = first_tool_call.arguments
            if isinstance(args, dict):
                content = str(args.get("answer", str(args)))
            else:
                content = str(args).strip()

            if used_code:
                # Clean up the content by removing any end code tags
                content = re.sub(r"```.*?\n", "", content)  # Remove existing code blocks
                content = re.sub(r"\s*<end_code>\s*", "", content)  # Remove end_code tags
                content = content.strip()
                if not content.startswith("```python"):
                    content = f"```python\n{content}\n```"

            parent_message_tool = gr.ChatMessage(
                role="assistant",
                content=content,
                metadata={
                    "title": f"🛠️ Used tool {first_tool_call.name}",
                    "id": parent_id,
                    "status": "pending",
                },
            )
            yield parent_message_tool

            # Nesting execution logs under the tool call if they exist
            if hasattr(step_log, "observations") and (
                step_log.observations is not None and step_log.observations.strip()
            ):  # Only yield execution logs if there's actual content
                log_content = step_log.observations.strip()
                if log_content:
                    log_content = re.sub(r"^Execution logs:\s*", "", log_content)
                    
                    # Check if this is a MarkdownToExcel result with Excel files
                    if (first_tool_call.name == "markdown_to_excel" and 
                        "Successfully converted" in log_content and 
                        ".xlsx" in log_content):
                        
                        # Process the file paths in the content
                        lines = log_content.split("\n")
                        base_content = lines[0]
                        file_paths = [line.strip() for line in lines[1:] if line.strip().endswith(".xlsx")]
                        
                        # Create HTML for file downloads
                        file_links_html = """
                        <div style="margin-top: 15px;">
                            <div style="font-weight: 500; margin-bottom: 10px; padding-bottom: 5px; border-bottom: 1px solid #eaeaea;">
                                Archivos Excel Generados:
                            </div>
                        """
                        
                        for i, file_path in enumerate(file_paths):
                            file_name = os.path.basename(file_path)
                            file_size = os.path.getsize(file_path)
                            
                            # Format file size
                            if file_size < 1024:
                                size_str = f"{file_size} B"
                            elif file_size < 1024 * 1024:
                                size_str = f"{file_size/1024:.1f} KB"
                            else:
                                size_str = f"{file_size/(1024*1024):.1f} MB"
                                
                            file_links_html += f"""
                            <div style="display: flex; align-items: center; margin: 10px 0; padding: 10px; 
                                      background: linear-gradient(to right, #f0f8ff, #ffffff); 
                                      border-radius: 6px; border: 1px solid #d0e3ff; 
                                      transition: transform 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                                <div style="display: flex; align-items: center; flex: 1;">
                                    <span style="margin-right: 10px; font-size: 24px;">📊</span>
                                    <div style="display: flex; flex-direction: column;">
                                        <span style="font-weight: 500; color: #0066cc;">{file_name}</span>
                                        <span style="font-size: 12px; color: #666; margin-top: 2px;">{size_str}</span>
                                    </div>
                                </div>
                                <a href="/download?path={file_path}" 
                                   style="display: inline-block; padding: 6px 12px; background-color: #0066cc; 
                                         color: white; border-radius: 4px; text-decoration: none; font-size: 14px;
                                         transition: background-color 0.2s;" 
                                   download="{file_name}" 
                                   target="_blank"
                                   onmouseover="this.style.backgroundColor='#0056b3'" 
                                   onmouseout="this.style.backgroundColor='#0066cc'">
                                    Descargar
                                </a>
                            </div>
                            """
                        
                        file_links_html += "</div>"
                        
                        # Combine the base content with file links
                        log_content = f"{base_content}{file_links_html}"
                    
                    yield gr.ChatMessage(
                        role="assistant",
                        content=f"{log_content}",
                        metadata={"title": "📝 Execution Logs", "parent_id": parent_id, "status": "done"},
                    )

            # Nesting any errors under the tool call
            if hasattr(step_log, "error") and step_log.error is not None:
                yield gr.ChatMessage(
                    role="assistant",
                    content=str(step_log.error),
                    metadata={"title": "💥 Error", "parent_id": parent_id, "status": "done"},
                )

            # Update parent message metadata to done status without yielding a new message
            parent_message_tool.metadata["status"] = "done"

        # Handle standalone errors but not from tool calls
        elif hasattr(step_log, "error") and step_log.error is not None:
            yield gr.ChatMessage(role="assistant", content=str(step_log.error), metadata={"title": "💥 Error"})

        # Calculate duration and token information
        step_footnote = f"{step_number}"
        if hasattr(step_log, "input_token_count") and hasattr(step_log, "output_token_count"):
            token_str = (
                f" | Input-tokens:{step_log.input_token_count:,} | Output-tokens:{step_log.output_token_count:,}"
            )
            step_footnote += token_str
        if hasattr(step_log, "duration"):
            step_duration = f" | Duration: {round(float(step_log.duration), 2)}" if step_log.duration else None
            step_footnote += step_duration
        step_footnote = f"""<span style="color: #bbbbc2; font-size: 12px;">{step_footnote}</span> """
        yield gr.ChatMessage(role="assistant", content=f"{step_footnote}")
        yield gr.ChatMessage(role="assistant", content="-----")


def stream_to_gradio(
    agent,
    task: str,
    reset_agent_memory: bool = False,
    additional_args: Optional[dict] = None,
):
    """Runs an agent with the given task and streams the messages from the agent as gradio ChatMessages."""
    if not _is_package_available("gradio"):
        raise ModuleNotFoundError(
            "Please install 'gradio' extra to use the GradioUI: `pip install 'smolagents[gradio]'`"
        )
    import gradio as gr

    total_input_tokens = 0
    total_output_tokens = 0

    for step_log in agent.run(task, stream=True, reset=reset_agent_memory, additional_args=additional_args):
        # Track tokens if model provides them
        if getattr(agent.model, "last_input_token_count", None) is not None:
            total_input_tokens += agent.model.last_input_token_count / 3
            total_output_tokens += agent.model.last_output_token_count / 3
            if isinstance(step_log, ActionStep):
                step_log.input_token_count = agent.model.last_input_token_count
                step_log.output_token_count = agent.model.last_output_token_count

        for message in pull_messages_from_step(
            step_log,
        ):
            yield message

    final_answer = step_log  # Last log is the run's final_answer
    final_answer = handle_agent_output_types(final_answer)

    if isinstance(final_answer, AgentText):
        yield gr.ChatMessage(
            role="assistant",
            content=f"**Final answer:**\n{final_answer.to_string()}\n",
        )
    elif isinstance(final_answer, AgentImage):
        yield gr.ChatMessage(
            role="assistant",
            content={"path": final_answer.to_string(), "mime_type": "image/png"},
        )
    elif isinstance(final_answer, AgentAudio):
        yield gr.ChatMessage(
            role="assistant",
            content={"path": final_answer.to_string(), "mime_type": "audio/wav"},
        )
    else:
        yield gr.ChatMessage(role="assistant", content=f"**Final answer:** {str(final_answer)}")


class GradioUI:
    """A one-line interface to launch your agent in Gradio"""

    def __init__(self, agent: MultiStepAgent, file_upload_folder: str | None = None):
        if not _is_package_available("gradio"):
            raise ModuleNotFoundError(
                "Please install 'gradio' extra to use the GradioUI: `pip install 'smolagents[gradio]'`"
            )
        self.agent = agent
        self.file_upload_folder = file_upload_folder
        if self.file_upload_folder is not None:
            if not os.path.exists(file_upload_folder):
                os.mkdir(file_upload_folder)
        
        # Create output directory for generated files if it doesn't exist
        self.output_dir = "data/output"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Define output directories that should be cleared on page refresh
        self.output_directories = [
            "output",
            "data/output",
            "uploads",
            "downloads",
            "downloads_folder"
        ]
    
    def clear_output_directories(self):
        """
        Clears all files in the specified output directories.
        This function is called when the page is refreshed.
        """
        cleared_files = []
        
        for directory in self.output_directories:
            if os.path.exists(directory):
                for file_name in os.listdir(directory):
                    file_path = os.path.join(directory, file_name)
                    if os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                            cleared_files.append(file_path)
                        except Exception as e:
                            print(f"Error removing file {file_path}: {str(e)}")
        
        print(f"Cleared {len(cleared_files)} files from output directories")
        
        # Create HTML feedback for user
        if cleared_files:
            html_feedback = f"""
            <div style="padding: 10px; background-color: #e6f7ff; border-radius: 4px; margin-top: 10px; text-align: center;">
                <p style="margin: 0; font-size: 14px; color: #0066cc;">
                    <strong>✅ Se eliminaron {len(cleared_files)} archivos al refrescar la página.</strong>
                </p>
            </div>
            """
            
            # If there are files to show, list them in a collapsible section
            if len(cleared_files) > 0:
                file_list_html = """
                <details style="margin-top: 10px; padding: 8px; border: 1px solid #d0e3ff; border-radius: 4px;">
                    <summary style="cursor: pointer; font-weight: 500; color: #0066cc;">Ver archivos eliminados</summary>
                    <div style="margin-top: 8px; max-height: 150px; overflow-y: auto; font-size: 12px;">
                        <ul style="margin: 0; padding-left: 20px;">
                """
                
                for file_path in cleared_files:
                    file_list_html += f"<li>{file_path}</li>"
                
                file_list_html += """
                        </ul>
                    </div>
                </details>
                """
                html_feedback += file_list_html
        else:
            html_feedback = """
            <div style="padding: 10px; background-color: #f8f9fa; border-radius: 4px; margin-top: 10px; text-align: center;">
                <p style="margin: 0; font-size: 14px; color: #6c757d;">No se encontraron archivos para eliminar.</p>
            </div>
            """
        
        return html_feedback

    def interact_with_agent(self, prompt, messages):
        import gradio as gr

        messages.append(gr.ChatMessage(role="user", content=prompt))
        yield messages
        
        # Flag to detect if a file was generated during this interaction
        files_generated = False
        
        for msg in stream_to_gradio(self.agent, task=prompt, reset_agent_memory=False):
            messages.append(msg)
            
            # Check if this message contains a file generation tool result
            if hasattr(msg, "content") and isinstance(msg.content, str):
                if "Successfully converted" in msg.content or "file generated" in msg.content or "created file" in msg.content:
                    files_generated = True
            
            yield messages
        
        # Return one more time to signal the interaction is complete
        # This will be used to trigger the file list refresh if needed
        yield messages, files_generated
    
    def get_available_files(self):
        """
        List all available files in the output directories.
        Returns an HTML string with links to download the files.
        """
        import gradio as gr
        import datetime
        import glob
        
        # Buscar archivos en múltiples ubicaciones posibles
        search_dirs = [
            self.output_dir,          # data/output
            "output",                  # output en el directorio raíz
            "data",                    # data
            "downloads",               # downloads
            "downloads_folder",        # downloads_folder
            ".",                       # directorio actual
        ]
        
        all_files = []
        
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
                
            # Busca todos los archivos en el directorio y subdirectorios
            for file_path in glob.glob(os.path.join(search_dir, "**", "*"), recursive=True):
                if os.path.isfile(file_path) and not os.path.basename(file_path).startswith('.'):
                    # Get file metadata
                    file_size = os.path.getsize(file_path)
                    mod_time = os.path.getmtime(file_path)
                    mod_time_str = datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Get file extension
                    file_ext = os.path.splitext(file_path)[1].lower()
                    
                    # Format file size
                    if file_size < 1024:
                        size_str = f"{file_size} B"
                    elif file_size < 1024 * 1024:
                        size_str = f"{file_size/1024:.1f} KB"
                    else:
                        size_str = f"{file_size/(1024*1024):.1f} MB"
                    
                    # Choose icon based on file extension
                    if file_ext == '.xlsx':
                        icon = "📊"  # Excel 
                    elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                        icon = "🖼️"  # Image
                    elif file_ext in ['.pdf']:
                        icon = "📄"  # PDF
                    elif file_ext in ['.doc', '.docx']:
                        icon = "📝"  # Word
                    elif file_ext in ['.txt', '.md']:
                        icon = "📃"  # Text
                    elif file_ext in ['.csv']:
                        icon = "📋"  # CSV
                    elif file_ext in ['.py']:
                        icon = "🐍"  # Python
                    else:
                        icon = "📁"  # General file
                    
                    # Para evitar duplicados si un archivo aparece en múltiples rutas de búsqueda
                    if not any(e["path"] == file_path for e in all_files):
                        all_files.append({
                            "path": file_path,
                            "name": os.path.basename(file_path),
                            "size": size_str,
                            "modified": mod_time_str,
                            "modified_timestamp": mod_time,  # For sorting
                            "icon": icon,
                            "extension": file_ext
                        })
        
        if not all_files:
            return """
            <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 8px; margin-top: 10px;">
                <p style="font-size: 16px; color: #6c757d;">No se han encontrado archivos.</p>
                <p style="font-size: 14px; color: #6c757d; margin-top: 8px;">Los archivos aparecerán aquí cuando se generen.</p>
                <p style="font-size: 12px; color: #6c757d; margin-top: 15px; font-style: italic;">Carpetas buscadas: data/output, output, data, downloads, downloads_folder</p>
            </div>
            """
        
        # Sort files by modification time (newest first)
        all_files.sort(key=lambda x: x["modified_timestamp"], reverse=True)
        
        # Create HTML for the files list
        html_content = """
        <div style="padding: 10px;">
            <h3 style="margin-bottom: 15px; color: #0066cc; border-bottom: 1px solid #e0e0e0; padding-bottom: 8px;">
                Archivos Encontrados ({0})
            </h3>
            <div style="display: flex; flex-direction: column; gap: 10px;">
        """.format(len(all_files))
        
        for file in all_files:
            html_content += f"""
            <div style="display: flex; flex-direction: column; padding: 12px; background: #f0f8ff; border-radius: 8px; border: 1px solid #d0e3ff; transition: all 0.2s ease;">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <span style="margin-right: 12px; font-size: 24px;">{file['icon']}</span>
                    <a href="/download?path={file['path']}" 
                       style="color: #0066cc; text-decoration: none; font-size: 16px; font-weight: 500;" 
                       download="{file['name']}" 
                       target="_blank">
                        {file['name']}
                    </a>
                </div>
                <div style="display: flex; flex-direction: column; font-size: 12px; color: #666; padding-left: 36px; gap: 2px;">
                    <span>Tamaño: {file['size']}</span>
                    <span>Modificado: {file['modified']}</span>
                    <span style="word-break: break-all;">Ruta: {file['path']}</span>
                </div>
                <div style="margin-top: 8px; display: flex; justify-content: flex-end;">
                    <a href="/download?path={file['path']}" 
                       style="display: inline-block; padding: 5px 12px; background-color: #0066cc; color: white; border-radius: 4px; text-decoration: none; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" 
                       download="{file['name']}" 
                       target="_blank">
                        Descargar Archivo
                    </a>
                </div>
            </div>
            """
        
        html_content += """
            </div>
        </div>
        """
        
        return html_content

    def upload_file(
        self,
        file,
        file_uploads_log,
        allowed_file_types=[
            "application/pdf",
            "application/vnd.ms-excel",
            "application/msexcel",
            "application/x-msexcel",
            "application/x-ms-excel",
            "application/x-excel",
            "application/x-dos_ms_excel",
            "application/xls",
            "application/x-xls",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.openxmlformats-officedocument.presentationml.slideshow",
            "application/vnd.openxmlformats-officedocument.presentationml.template",
            "application/vnd.openxmlformats-officedocument.presentationml.slide",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "image/jpeg",
            "image/png",
            "image/jpg",
            "image/gif",
            "image/bmp",
            "image/tiff",
            "image/ico",
            "image/webp",
            "image/svg+xml",
            "image/heic",
            "image/heif",
            "image/heic-sequence",
            "image/heif-sequence",
        ],
    ):
        """
        Handle file uploads, default allowed types are .pdf, .docx, and .txt
        """
        import gradio as gr

        if file is None:
            return gr.Textbox("No file uploaded", visible=True), file_uploads_log

        try:
            mime_type, _ = mimetypes.guess_type(file.name)
        except Exception as e:
            return gr.Textbox(f"Error: {e}", visible=True), file_uploads_log

        if mime_type not in allowed_file_types:
            return gr.Textbox("File type not allowed", visible=True), file_uploads_log

        # Sanitize file name
        original_name = os.path.basename(file.name)
        sanitized_name = re.sub(
            r"[^\w\-.]", "_", original_name
        )  # Replace any non-alphanumeric, non-dash, or non-dot characters with underscores

        type_to_ext = {}
        for ext, t in mimetypes.types_map.items():
            if t not in type_to_ext:
                type_to_ext[t] = ext

        # Ensure the extension correlates to the mime type
        sanitized_name = sanitized_name.split(".")[:-1]
        sanitized_name.append("" + type_to_ext[mime_type])
        sanitized_name = "".join(sanitized_name)

        # Save the uploaded file to the specified folder
        file_path = os.path.join(self.file_upload_folder, os.path.basename(sanitized_name))
        shutil.copy(file.name, file_path)

        return gr.Textbox(f"File uploaded: {file_path}", visible=True), file_uploads_log + [file_path]

    def log_user_message(self, text_input, file_uploads_log):
        return (
            text_input
            + (
                f"\nYou have been provided with these files, which might be helpful or not: {file_uploads_log}"
                if len(file_uploads_log) > 0
                else ""
            ),
            "",
        )

    def launch(self, share: bool = False, **kwargs):
        import gradio as gr
        import time

        def handle_file_upload(file, current_log):
            return self.upload_file(file, current_log)
        
        def handle_text_submit(text, uploads_log):
            return self.log_user_message(text, uploads_log)
        
        def handle_chat_interaction(stored_msg, chat):
            return self.interact_with_agent(stored_msg, chat)
        
        def refresh_files():
            return self.get_available_files()
        
        # Function to clear output directories and refresh file list
        def clear_and_refresh():
            clear_result = self.clear_output_directories()
            files_html = self.get_available_files()
            return files_html + clear_result
        
        # New function to handle the post-chat update with auto-refresh
        def handle_chat_complete(messages, files_generated, files_html):
            # Force refresh of files list
            files_html_updated = self.get_available_files()
            
            # Inicia un mensaje con información sobre la actualización automática
            info_message = """<div style="padding: 10px; background-color: #e6f7ff; border-radius: 4px; margin-top: 10px; text-align: center;">
                <p style="margin: 0; font-size: 14px;">Buscando archivos generados... <span id="countdown">5</span></p>
            </div>"""
            
            # Reemplazar el html de archivos con la información y el temporizador
            if files_generated:
                return messages, files_html_updated + info_message
            return messages, files_html_updated

        # Function to check for new files periodically
        def check_for_new_files():
            time.sleep(2)  # Esperar 2 segundos
            return self.get_available_files()

        with gr.Blocks(fill_height=True) as demo:
            stored_messages = gr.State([])
            file_uploads_log = gr.State([])
            
            with gr.Row(equal_height=True) as main_row:
                # Main chat interface
                with gr.Column(scale=3):
                    chatbot = gr.Chatbot(
                        label="Agent",
                        type="messages",
                        avatar_images=(
                            None,
                            "https://i.pinimg.com/736x/b4/9b/1f/b49b1f1896a4c3138dc50bb74f9ab712.jpg",
                        ),
                        resizeable=True,
                        scale=1,
                        height=600
                    )
                    
                    # If an upload folder is provided, enable the upload feature
                    if self.file_upload_folder is not None:
                        with gr.Row():
                            upload_file = gr.File(label="Upload file")
                            upload_status = gr.Textbox(label="Upload Status", interactive=False, visible=False)
                        
                    # Create the text input field
                    text_input = gr.Textbox(lines=1, label="Chat Message")
                
                # Side panel for files
                with gr.Column(scale=1, min_width=350):
                    with gr.Group(visible=True):
                        gr.HTML("<h2 style='text-align: center; margin: 10px 0; color: #0066cc;'>Archivos Generados</h2>")
                        
                        # Add a description for the files panel
                        gr.HTML("""
                            <div style="margin-bottom: 15px; padding: 10px; background-color: #f0f8ff; border-radius: 6px; border-left: 3px solid #0066cc;">
                                <p style="margin: 0; font-size: 14px;">Los archivos generados por el sistema se mostrarán aquí automáticamente. <strong>Se eliminarán al refrescar la página.</strong></p>
                            </div>
                        """)
                        
                        refresh_files_btn = gr.Button("🔄 Actualizar Archivos", size="sm", variant="primary")
                        files_html = gr.HTML(self.get_available_files(), elem_id="files-container")
            
            # Add a Javascript function to clear output directories on page refresh
            demo.load(
                fn=clear_and_refresh,
                inputs=[],
                outputs=[files_html],
                js="""() => {
                    // Log that the page was refreshed
                    console.log("Page refreshed - clearing output directories");
                    // Return null to trigger the Python function
                    return null;
                }"""
            )
            
            # Set up event handlers
            if self.file_upload_folder is not None:
                gr.on(
                    "change",
                    fn=handle_file_upload,
                    inputs=[upload_file, file_uploads_log],
                    outputs=[upload_status, file_uploads_log],
                    api_name="upload_file_change"
                )
            
            # Create the chain of events for chat interaction and file list update
            chat_submit_event = gr.on(
                "submit",
                fn=handle_text_submit,
                inputs=[text_input, file_uploads_log],
                outputs=[stored_messages, text_input],
                api_name="chat_submit"
            )
            
            chat_interaction_event = gr.on(
                "data",
                fn=handle_chat_interaction,
                inputs=[stored_messages, chatbot],
                outputs=[chatbot, gr.State()],  # Pass the files_generated flag through a State
                api_name="chat_interaction",
                triggers=[chat_submit_event]
            )
            
            chat_complete_event = gr.on(
                "data",
                fn=handle_chat_complete,
                inputs=[chatbot, gr.State(), files_html],  # Add the files_html as input
                outputs=[chatbot, files_html],  # Update both chatbot and files_html
                api_name="chat_complete",
                triggers=[chat_interaction_event]
            )
            
            # Add back the event handler for checking new files after chat completion
            gr.on(
                "data",
                fn=check_for_new_files,  # Actualización adicional después de unos segundos
                inputs=[],
                outputs=[files_html],
                api_name="check_for_new_files",
                triggers=[chat_complete_event],
                js="() => {let count = 5; const interval = setInterval(() => {const el = document.getElementById('countdown'); if(el) {count--; el.innerText = count; if(count <= 0) clearInterval(interval)}}, 1000)}"
            )
            
            # Refresh button for files
            gr.on(
                "click",
                fn=refresh_files,
                inputs=[],
                outputs=[files_html],
                api_name="refresh_files",
                triggers=[refresh_files_btn]
            )

        demo.launch(debug=True, share=share, **kwargs)


__all__ = ["stream_to_gradio", "GradioUI"]
