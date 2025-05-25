#!/usr/bin/env python3
"""
Run the InfoBlox Network Import Web Server
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Import and configure the app
    from app.web import app
    from fastapi.staticfiles import StaticFiles
    
    # Mount static files
    static_path = Path(__file__).parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    # Serve index.html at root
    from fastapi.responses import FileResponse
    
    @app.get("/", response_class=FileResponse)
    async def serve_index():
        """Serve the main HTML file"""
        return FileResponse(str(static_path / "index.html"))
    
    # Run the server
    import uvicorn
    
    print("InfoBlox Network Import Web Server")
    print("==================================")
    print("Server running at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
