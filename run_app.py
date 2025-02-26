import os
import sys

# Make sure the upload directory exists
UPLOAD_DIR = "data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Show startup message
print("Starting Smol Agency AI Chat application...")
print("Frontend will be available at http://localhost:8000")

# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("frontend.api.main:app", host="0.0.0.0", port=8000, reload=False) 