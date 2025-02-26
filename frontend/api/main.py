import json
import os
import shutil
import sys
from typing import List, Optional

import gradio as gr
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.requests import Request

# Add the parent directory to the path to import agency.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the manager_agent from agency.py and the stream_to_gradio function from gradio_agent.py
from agency import manager_agent
from gradio_agent import stream_to_gradio

# Initialize FastAPI app
app = FastAPI(title="Smol Agency AI Chat", description="A FastAPI backend for the Smol Agency AI Chat interface")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up template and static directories
templates = Jinja2Templates(directory="frontend/templates")
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "data"  # Use the same upload directory as in agency.py
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Create output directory if it doesn't exist
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Pydantic models for API requests and responses
class ChatRequest(BaseModel):
    message: str
    files: Optional[List[str]] = None

class ChatResponse(BaseModel):
    response: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None

class StatusResponse(BaseModel):
    status: str
    message: Optional[str] = None

# Define API routes
@app.get("/api/status")
async def get_status():
    """Check if the agent is ready."""
    if manager_agent is None:
        return StatusResponse(status="error", message="Agent not initialized")
    return StatusResponse(status="ready", message="Agent is ready")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Send a message to the agent and get a response."""
    if manager_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Process the message with the manager_agent
        response = manager_agent.run(request.message)
        
        # Get token counts if available
        input_tokens = getattr(manager_agent.model, "last_input_token_count", None)
        output_tokens = getattr(manager_agent.model, "last_output_token_count", None)
        
        return ChatResponse(
            response=response,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stream")
async def stream_chat(
    message: str = Form(...),
    files: List[UploadFile] = File(None)
):
    """Stream the agent's response."""
    if manager_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    # Process uploaded files if any
    file_paths = []
    if files:
        for file in files:
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            file_paths.append(file_path)
    
    # Prepare the message with file paths if needed
    if file_paths:
        full_message = f"{message}\n\nYou have been provided with these files, which might be helpful or not: {file_paths}"
    else:
        full_message = message
    
    async def generate_stream():
        try:
            total_input_tokens = 0
            total_output_tokens = 0
            
            # Use the stream_to_gradio function to stream the agent's response
            for message in stream_to_gradio(manager_agent, task=full_message, reset_agent_memory=False):
                # Convert gradio ChatMessage to a JSON format for the frontend
                if hasattr(message, "content") and message.content:
                    # Handle different types of content
                    content = message.content
                    content_type = "text"
                    
                    # Check if content is a dictionary (e.g., for images or audio)
                    if isinstance(content, dict) and "path" in content:
                        content_type = content.get("mime_type", "file")
                        content = content["path"]
                    
                    # Get metadata if available
                    metadata = message.metadata if hasattr(message, "metadata") else {}
                    
                    # Determine message type based on metadata
                    msg_type = "text"
                    if metadata:
                        if "title" in metadata:
                            if "Tool" in metadata["title"]:
                                msg_type = "tool_start"
                            elif "Logs" in metadata["title"]:
                                msg_type = "tool_content"
                            elif "Error" in metadata["title"]:
                                msg_type = "tool_error"
                        if "status" in metadata:
                            if metadata["status"] == "done":
                                msg_type = "tool_result"
                    
                    # Check for special messages like step numbers or token info
                    if isinstance(content, str):
                        if content.startswith("**Step"):
                            msg_type = "step_number"
                        elif content.startswith("<span style=\"color: #bbbbc2; font-size: 12px;\">"):
                            msg_type = "token_info"
                        elif content == "-----":
                            msg_type = "separator"
                    
                    # Create response data
                    data = {
                        "type": msg_type,
                        "content": content,
                        "content_type": content_type,
                    }
                    
                    # Add tool name if available
                    if "title" in metadata and msg_type == "tool_start":
                        tool_name = metadata["title"].replace("🛠️ Used tool ", "")
                        data["tool_name"] = tool_name
                    
                    # Update token counts if available from the model
                    if hasattr(manager_agent.model, "last_input_token_count"):
                        input_tokens = manager_agent.model.last_input_token_count
                        total_input_tokens += input_tokens
                        data["input_tokens"] = total_input_tokens
                    
                    if hasattr(manager_agent.model, "last_output_token_count"):
                        output_tokens = manager_agent.model.last_output_token_count
                        total_output_tokens += output_tokens
                        data["output_tokens"] = total_output_tokens
                    
                    yield f"{json.dumps(data)}\n"
        except Exception as e:
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"
    
    return StreamingResponse(generate_stream(), media_type="text/event-stream")

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload files to be used in the chat."""
    upload_results = []
    
    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        try:
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            
            upload_results.append({
                "filename": file.filename,
                "path": file_path,
                "size": os.path.getsize(file_path),
                "status": "success"
            })
        except Exception as e:
            upload_results.append({
                "filename": file.filename,
                "error": str(e),
                "status": "error"
            })
    
    return upload_results

@app.post("/api/reset")
async def reset_conversation():
    """Reset the agent's conversation history."""
    if manager_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Reset the agent's memory
        manager_agent.run("", reset=True)
        return {"status": "success", "message": "Conversation history reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download")
async def download_file(path: str):
    """
    Download a file by path.
    
    This route allows downloading files generated by the agent, such as Excel files
    created by the MarkdownToExcel tool.
    """
    # Normalizar la ruta (resolver rutas relativas)
    normalized_path = os.path.normpath(os.path.abspath(path))
    
    # Comprobar si el archivo existe
    if not os.path.exists(normalized_path) or not os.path.isfile(normalized_path):
        # Si no existe, intentar buscar en otras ubicaciones
        search_dirs = ["data/output", "output", "data", "downloads", "downloads_folder", "."]
        found = False
        
        for search_dir in search_dirs:
            filename = os.path.basename(path)
            alt_path = os.path.join(search_dir, filename)
            if os.path.exists(alt_path) and os.path.isfile(alt_path):
                normalized_path = alt_path
                found = True
                break
        
        if not found:
            raise HTTPException(
                status_code=404, 
                detail=f"Archivo no encontrado: {path}. Se buscó en: {', '.join(search_dirs)}"
            )
    
    # Get the filename from the path
    filename = os.path.basename(normalized_path)
    
    # Determine the media type (MIME type) basado en la extensión del archivo
    extension = os.path.splitext(filename)[1].lower()
    media_type_map = {
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".csv": "text/csv",
        ".txt": "text/plain",
        ".pdf": "application/pdf",
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".html": "text/html",
        ".htm": "text/html",
        ".xml": "application/xml",
        ".zip": "application/zip",
        ".md": "text/markdown",
    }
    
    media_type = media_type_map.get(extension, "application/octet-stream")
    
    # Log descarga para depuración
    print(f"Descargando archivo: {normalized_path}, tipo: {media_type}, tamaño: {os.path.getsize(normalized_path)}")
    
    # Return the file as a downloadable response
    return FileResponse(
        path=normalized_path,
        filename=filename,
        media_type=media_type
    )

@app.get("/api/files")
async def get_files():
    """
    Get a list of available files from the output directory.
    
    Returns a list of all files found in the output directory, with metadata
    such as file size and modification time.
    """
    import glob
    import os
    import datetime
    
    # Solo buscar en la carpeta output del directorio raíz
    search_dir = "output"
    
    all_files = []
    
    if os.path.exists(search_dir):
        # Busca todos los archivos en el directorio y subdirectorios
        for file_path in glob.glob(os.path.join(search_dir, "**", "*"), recursive=True):
            if os.path.isfile(file_path):
                # Obtener metadatos del archivo
                file_size = os.path.getsize(file_path)
                mod_time = os.path.getmtime(file_path)
                mod_time_str = datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
                
                # Obtener extensión del archivo
                file_ext = os.path.splitext(file_path)[1].lower()
                
                # Determinar icono basado en la extensión
                icon = "📄"  # Icono por defecto
                if file_ext in ['.xlsx', '.xls']:
                    icon = "📊"
                elif file_ext in ['.pdf']:
                    icon = "📝"
                elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    icon = "🖼️"
                elif file_ext in ['.txt', '.md', '.csv']:
                    icon = "📃"
                elif file_ext in ['.zip', '.rar', '.7z']:
                    icon = "🗜️"
                elif file_ext in ['.mp3', '.wav', '.ogg']:
                    icon = "🎵"
                elif file_ext in ['.mp4', '.avi', '.mov']:
                    icon = "🎬"
                
                # Formatear tamaño del archivo
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size/1024:.1f} KB"
                else:
                    size_str = f"{file_size/(1024*1024):.1f} MB"
                
                all_files.append({
                    "path": file_path,
                    "name": os.path.basename(file_path),
                    "size": size_str,
                    "modified": mod_time_str,
                    "modified_timestamp": mod_time,  # Para ordenar
                    "extension": file_ext,
                    "icon": icon
                })
    
    # Ordenar archivos por hora de modificación (más recientes primero)
    all_files.sort(key=lambda x: x["modified_timestamp"], reverse=True)
    
    return {"files": all_files}

@app.get("/api/search_files")
async def search_files(directory: str = None):
    """
    Search for all files in the output directory.
    
    Parameters:
        directory (str, optional): Not used, only the output directory is searched.
    
    Returns:
        A list of files found in the output directory.
    """
    import glob
    import os
    
    # Solo buscar en la carpeta output del directorio raíz
    search_dir = "output"
    all_files = []
    
    if os.path.exists(search_dir):
        # Buscar todos los archivos en el directorio
        for file_path in glob.glob(os.path.join(search_dir, "*")):
            if os.path.isfile(file_path):
                # Obtener información básica del archivo
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                
                # Obtener extensión del archivo
                file_ext = os.path.splitext(file_path)[1].lower()
                
                # Determinar icono basado en la extensión
                icon = "📄"  # Icono por defecto
                if file_ext in ['.xlsx', '.xls']:
                    icon = "📊"
                elif file_ext in ['.pdf']:
                    icon = "📝"
                elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    icon = "🖼️"
                elif file_ext in ['.txt', '.md', '.csv']:
                    icon = "📃"
                elif file_ext in ['.zip', '.rar', '.7z']:
                    icon = "🗜️"
                elif file_ext in ['.mp3', '.wav', '.ogg']:
                    icon = "🎵"
                elif file_ext in ['.mp4', '.avi', '.mov']:
                    icon = "🎬"
                
                # Formatear tamaño del archivo
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size/1024:.1f} KB"
                else:
                    size_str = f"{file_size/(1024*1024):.1f} MB"
                
                all_files.append({
                    "name": file_name,
                    "path": file_path,
                    "size": size_str,
                    "extension": file_ext,
                    "icon": icon
                })
    
    return {"files": all_files}

# Main HTML route
@app.get("/")
async def read_root(request: Request):
    """Serve the main HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})

# Keep the old route for backward compatibility
@app.get("/api/excel_files")
async def get_excel_files():
    """Legacy endpoint that redirects to the new /api/files endpoint"""
    return await get_files()

# Keep the old route for backward compatibility
@app.get("/api/search_excel_files")
async def search_excel_files(directory: str = None):
    """Legacy endpoint that redirects to the new /api/search_files endpoint"""
    return await search_files(directory)

@app.get("/api/clear_output_files")
async def clear_output_files():
    """
    Delete all files in the output directory.
    This endpoint is called when the page is refreshed.
    """
    import os
    import glob
    
    output_dir = "output"
    cleared_files = []
    
    # Asegurarse de que el directorio existe
    if os.path.exists(output_dir):
        # Obtener todos los archivos en el directorio
        for file_path in glob.glob(os.path.join(output_dir, "*")):
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    cleared_files.append(file_path)
                except Exception as e:
                    print(f"Error al eliminar el archivo {file_path}: {str(e)}")
    
    return {
        "status": "success", 
        "message": f"Se eliminaron {len(cleared_files)} archivos de la carpeta output",
        "files_cleared": cleared_files
    }

# Run the application with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("frontend.api.main:app", host="0.0.0.0", port=8000, reload=True) 