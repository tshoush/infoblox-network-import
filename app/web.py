"""
FastAPI Web Application for InfoBlox Network Import
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import asyncio
import uuid
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd
from io import StringIO
import logging

# Add parent directory to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from app.core.infoblox import InfoBloxWAPI
from app.core.parsers import CloudNetworkParser
from app.core.models import NetworkImportModel, ImportJob, EAMappingConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="InfoBlox Network Import API",
    description="Import networks from various cloud providers into InfoBlox IPAM",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
UPLOAD_DIR = Path("uploads")
REPORT_DIR = Path("reports")
UPLOAD_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

# In-memory job storage (use Redis in production)
jobs: Dict[str, ImportJob] = {}

# Global InfoBlox API instance (in production, use dependency injection)
def get_infoblox_api(request=None):
    """Get InfoBlox API instance with optional overrides from request headers"""
    if request and hasattr(request, 'headers'):
        return InfoBloxWAPI(
            grid_master=request.headers.get('X-Grid-Master'),
            username=request.headers.get('X-Username'),
            password=request.headers.get('X-Password'),
            network_view=request.headers.get('X-Network-View')
        )
    return InfoBloxWAPI()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>InfoBlox Network Import</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    </head>
    <body class="bg-gray-100">
        <div class="container mx-auto px-4 py-8">
            <h1 class="text-3xl font-bold mb-8">InfoBlox Network Import Tool</h1>
            <div id="app" x-data="networkImportApp()">
                <!-- File Upload Section -->
                <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                    <h2 class="text-xl font-semibold mb-4">Upload Network File</h2>
                    
                    <!-- Connection Settings -->
                    <details class="mb-4">
                        <summary class="cursor-pointer text-sm text-blue-600 hover:text-blue-800">
                            ⚙️ InfoBlox Connection Settings
                        </summary>
                        <div class="mt-2 p-4 bg-gray-50 rounded">
                            <div class="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <label class="font-medium">Grid Master:</label>
                                    <input type="text" x-model="settings.gridMaster" 
                                           class="w-full p-1 border rounded text-sm">
                                </div>
                                <div>
                                    <label class="font-medium">Network View:</label>
                                    <input type="text" x-model="settings.networkView" 
                                           class="w-full p-1 border rounded text-sm">
                                </div>
                                <div>
                                    <label class="font-medium">Username:</label>
                                    <input type="text" x-model="settings.username" 
                                           class="w-full p-1 border rounded text-sm">
                                </div>
                                <div>
                                    <label class="font-medium">Password:</label>
                                    <input type="password" x-model="settings.password" 
                                           class="w-full p-1 border rounded text-sm">
                                </div>
                            </div>
                            <button @click="testConnection" class="mt-2 text-sm bg-gray-600 text-white px-3 py-1 rounded">
                                Test Connection
                            </button>
                            <span x-show="connectionStatus" x-text="connectionStatus" 
                                  :class="connectionOk ? 'text-green-600' : 'text-red-600'" 
                                  class="ml-2 text-sm"></span>
                        </div>
                    </details>
                    
                    <form @submit.prevent="uploadFile">
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Source Type</label>
                            <select x-model="sourceType" class="w-full p-2 border rounded">
                                <option value="aws">AWS</option>
                                <option value="properties">Properties Format</option>
                                <option value="custom">Custom CSV</option>
                            </select>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Network File</label>
                            <input type="file" @change="fileSelected" accept=".csv,.xlsx,.xls"
                                   class="w-full p-2 border rounded">
                        </div>
                        <button type="submit" :disabled="!selectedFile"
                                class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50">
                            Upload and Preview
                        </button>
                    </form>
                </div>
                
                <!-- Preview Section -->
                <div class="bg-white rounded-lg shadow-md p-6 mb-6" x-show="previewData">
                    <h2 class="text-xl font-semibold mb-4">Import Preview</h2>
                    <div class="grid grid-cols-4 gap-4 mb-4">
                        <div class="text-center">
                            <div class="text-2xl font-bold text-green-600" x-text="previewData?.new_networks?.length || 0"></div>
                            <div class="text-sm text-gray-600">New Networks</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-blue-600" x-text="previewData?.updated_networks?.length || 0"></div>
                            <div class="text-sm text-gray-600">Updates</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-yellow-600" x-text="previewData?.overlapping_networks?.length || 0"></div>
                            <div class="text-sm text-gray-600">Overlaps</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-red-600" x-text="previewData?.errors?.length || 0"></div>
                            <div class="text-sm text-gray-600">Errors</div>
                        </div>
                    </div>
                    <button @click="executeImport" 
                            class="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
                        Execute Import
                    </button>
                </div>
                
                <!-- Progress Section -->
                <div class="bg-white rounded-lg shadow-md p-6" x-show="jobId">
                    <h2 class="text-xl font-semibold mb-4">Import Progress</h2>
                    <div class="mb-4">
                        <div class="bg-gray-200 rounded-full h-4">
                            <div class="bg-blue-600 h-4 rounded-full transition-all duration-300"
                                 :style="'width: ' + progress + '%'"></div>
                        </div>
                    </div>
                    <div class="text-center" x-text="status"></div>
                </div>
            </div>
        </div>
        
        <script>
        function networkImportApp() {
            return {
                selectedFile: null,
                sourceType: 'aws',
                fileId: null,
                previewData: null,
                jobId: null,
                progress: 0,
                status: '',
                connectionStatus: '',
                connectionOk: false,
                settings: {
                    gridMaster: '""" + os.getenv('INFOBLOX_GRID_MASTER', '192.168.1.222') + """',
                    networkView: '""" + os.getenv('INFOBLOX_NETWORK_VIEW', 'default') + """',
                    username: '""" + os.getenv('INFOBLOX_USERNAME', 'admin') + """',
                    password: '""" + os.getenv('INFOBLOX_PASSWORD', 'infoblox') + """'
                },
                
                fileSelected(event) {
                    this.selectedFile = event.target.files[0];
                },
                
                async uploadFile() {
                    if (!this.selectedFile) return;
                    
                    const formData = new FormData();
                    formData.append('file', this.selectedFile);
                    
                    try {
                        const response = await fetch('/api/v1/import/upload', {
                            method: 'POST',
                            body: formData
                        });
                        const data = await response.json();
                        this.fileId = data.file_id;
                        await this.previewImport();
                    } catch (error) {
                        alert('Upload failed: ' + error);
                    }
                },
                
                async previewImport() {
                    if (!this.fileId) return;
                    
                    try {
                        const params = new URLSearchParams({
                            source_type: this.sourceType,
                            network_view: this.settings.networkView
                        });
                        const response = await fetch(`/api/v1/import/preview/${this.fileId}?${params}`, {
                            headers: {
                                'X-Grid-Master': this.settings.gridMaster,
                                'X-Username': this.settings.username,
                                'X-Password': this.settings.password
                            }
                        });
                        this.previewData = await response.json();
                    } catch (error) {
                        alert('Preview failed: ' + error);
                    }
                },
                
                async executeImport() {
                    if (!this.fileId) return;
                    
                    try {
                        const params = new URLSearchParams({
                            source_type: this.sourceType,
                            network_view: this.settings.networkView
                        });
                        const response = await fetch(`/api/v1/import/execute/${this.fileId}?${params}`, {
                            method: 'POST',
                            headers: {
                                'X-Grid-Master': this.settings.gridMaster,
                                'X-Username': this.settings.username,
                                'X-Password': this.settings.password
                            }
                        });
                        const data = await response.json();
                        this.jobId = data.job_id;
                        this.trackProgress();
                    } catch (error) {
                        alert('Import failed: ' + error);
                    }
                },
                
                async testConnection() {
                    this.connectionStatus = 'Testing...';
                    try {
                        const response = await fetch('/api/v1/test-connection', {
                            headers: {
                                'X-Grid-Master': this.settings.gridMaster,
                                'X-Username': this.settings.username,
                                'X-Password': this.settings.password,
                                'X-Network-View': this.settings.networkView
                            }
                        });
                        const data = await response.json();
                        this.connectionOk = data.connected;
                        this.connectionStatus = data.message;
                    } catch (error) {
                        this.connectionOk = false;
                        this.connectionStatus = 'Connection failed: ' + error;
                    }
                },
                
                async trackProgress() {
                    const eventSource = new EventSource(`/api/v1/import/progress/${this.jobId}`);
                    
                    eventSource.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        this.progress = data.progress;
                        this.status = data.status;
                        
                        if (data.status === 'completed' || data.status === 'failed') {
                            eventSource.close();
                        }
                    };
                }
            }
        }
        </script>
    </body>
    </html>
    """


@app.post("/api/v1/import/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload network file for import"""
    # Validate file extension
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(400, "Invalid file format. Only CSV and Excel files are supported.")
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(500, f"Failed to save file: {str(e)}")
    finally:
        file.file.close()
    
    return {"file_id": file_id, "filename": file.filename, "size": file_path.stat().st_size}


@app.get("/api/v1/import/preview/{file_id}")
async def preview_import(file_id: str, source_type: str = "aws", network_view: str = "default", request: Request):
    """Preview import changes"""
    # Find the uploaded file
    files = list(UPLOAD_DIR.glob(f"{file_id}_*"))
    if not files:
        raise HTTPException(404, "File not found")
    
    file_path = files[0]
    
    try:
        # Parse file
        parser = CloudNetworkParser()
        networks = parser.parse_file(str(file_path), source_type)
        
        # Analyze changes with custom API settings
        api = get_infoblox_api(request)
        analysis = await analyze_network_changes(api, networks, network_view)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Preview failed: {e}")
        raise HTTPException(500, f"Preview failed: {str(e)}")


async def analyze_network_changes(api: InfoBloxWAPI, networks: List[NetworkImportModel], network_view: str = "default") -> Dict:
    """Analyze what changes would be made"""
    analysis = {
        'new_networks': [],
        'updated_networks': [],
        'overlapping_networks': [],
        'errors': []
    }
    
    for network in networks:
        try:
            # Check if network exists
            existing = api.get_network(network.address, network_view=network_view, 
                                     return_fields=['network', 'comment', 'extattrs'])
            
            if existing:
                # Check for differences
                if has_changes(existing, network):
                    analysis['updated_networks'].append({
                        'network': network.dict(),
                        'existing': existing
                    })
            else:
                # Check for overlaps
                overlaps = api.check_network_overlaps(network.address, network_view=network_view)
                if overlaps:
                    analysis['overlapping_networks'].append({
                        'network': network.dict(),
                        'overlaps': overlaps
                    })
                else:
                    analysis['new_networks'].append(network.dict())
                    
        except Exception as e:
            analysis['errors'].append({
                'network': network.address,
                'error': str(e)
            })
    
    return analysis


def has_changes(existing: dict, new: NetworkImportModel) -> bool:
    """Check if network has changes"""
    if existing.get('comment', '') != new.description:
        return True
    
    existing_eas = existing.get('extattrs', {})
    for tag_key, tag_value in new.tags.items():
        if tag_key not in existing_eas or existing_eas[tag_key].get('value') != tag_value:
            return True
    
    return False


@app.post("/api/v1/import/execute/{file_id}")
async def execute_import(file_id: str, source_type: str, network_view: str = "default", 
                        background_tasks: BackgroundTasks, request: Request):
    """Execute import in background"""
    # Create job
    job_id = str(uuid.uuid4())
    job = ImportJob(
        job_id=job_id,
        status="queued",
        started_at=datetime.now()
    )
    jobs[job_id] = job
    
    # Get connection settings from headers
    settings = {
        'grid_master': request.headers.get('X-Grid-Master'),
        'username': request.headers.get('X-Username'),
        'password': request.headers.get('X-Password'),
        'network_view': network_view
    }
    
    # Start background task
    background_tasks.add_task(
        process_import_task, job_id, file_id, source_type, settings
    )
    
    return {"job_id": job_id, "status": "queued"}


async def process_import_task(job_id: str, file_id: str, source_type: str, settings: dict):
    """Background task to process import"""
    job = jobs[job_id]
    job.status = "processing"
    
    try:
        # Find file
        files = list(UPLOAD_DIR.glob(f"{file_id}_*"))
        if not files:
            raise Exception("File not found")
        
        file_path = files[0]
        
        # Parse file
        parser = CloudNetworkParser()
        networks = parser.parse_file(str(file_path), source_type)
        job.total_networks = len(networks)
        
        # Get API instance with custom settings
        api = InfoBloxWAPI(
            grid_master=settings.get('grid_master'),
            username=settings.get('username'),
            password=settings.get('password')
        )
        network_view = settings.get('network_view', 'default')
        
        # Process networks
        for i, network in enumerate(networks):
            try:
                # Map tags to EAs
                extattrs = {}
                for key, value in network.tags.items():
                    ea_name = key.replace(' ', '_').replace('-', '_')
                    extattrs[ea_name] = {"value": str(value)}
                
                # Create network
                api.create_network(
                    network.address,
                    network_view=network_view,
                    comment=network.description,
                    extattrs=extattrs
                )
                
                job.processed_networks += 1
                job.progress = int((job.processed_networks / job.total_networks) * 100)
                
            except Exception as e:
                job.errors.append({
                    'network': network.address,
                    'error': str(e)
                })
            
            # Small delay to prevent overwhelming the API
            await asyncio.sleep(0.1)
        
        job.status = "completed"
        job.completed_at = datetime.now()
        
    except Exception as e:
        job.status = "failed"
        job.errors.append({'error': str(e)})
        job.completed_at = datetime.now()


@app.get("/api/v1/import/progress/{job_id}")
async def stream_progress(job_id: str):
    """Stream import progress using Server-Sent Events"""
    async def event_stream():
        while True:
            if job_id in jobs:
                job = jobs[job_id]
                
                event_data = {
                    "job_id": job_id,
                    "status": job.status,
                    "progress": job.progress,
                    "total": job.total_networks,
                    "processed": job.processed_networks,
                    "errors": len(job.errors)
                }
                
                yield f"data: {json.dumps(event_data)}\n\n"
                
                if job.status in ["completed", "failed"]:
                    break
            else:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break
            
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@app.get("/api/v1/jobs/{job_id}")
async def get_job_details(job_id: str):
    """Get job details and results"""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    
    job = jobs[job_id]
    return job.dict()


@app.get("/api/v1/test-connection")
async def test_connection(request: Request):
    """Test InfoBlox connection"""
    try:
        api = get_infoblox_api(request)
        if api.test_connection():
            return {"connected": True, "message": f"Successfully connected to InfoBlox at {api.grid_master}"}
        else:
            return {"connected": False, "message": "Connection failed"}
    except Exception as e:
        return {"connected": False, "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
