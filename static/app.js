// InfoBlox Network Import Web Application
const API_BASE = '/api/v1';

// Global state
let uploadedFileId = null;
let mappingFileId = null;
let previewData = null;
let currentJobId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    checkConnection();
    loadJobs();
});

// Initialize event listeners
function initializeEventListeners() {
    // File uploads
    document.getElementById('network-file').addEventListener('change', handleNetworkFileUpload);
    document.getElementById('mapping-file').addEventListener('change', handleMappingFileUpload);
    
    // Buttons
    document.getElementById('preview-btn').addEventListener('click', handlePreview);
    document.getElementById('import-btn').addEventListener('click', handleImport);
    
    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => handleTabClick(e.target));
    });
    
    // Initially disable buttons
    document.getElementById('preview-btn').disabled = true;
    document.getElementById('import-btn').disabled = true;
}

// Check InfoBlox connection
async function checkConnection() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        
        const indicator = document.getElementById('status-indicator');
        if (data.infoblox_connected) {
            indicator.textContent = 'Connected';
            indicator.className = 'px-2 py-1 rounded text-sm bg-green-500 text-white';
        } else {
            indicator.textContent = 'Disconnected';
            indicator.className = 'px-2 py-1 rounded text-sm bg-red-500 text-white';
        }
    } catch (error) {
        console.error('Connection check failed:', error);
        const indicator = document.getElementById('status-indicator');
        indicator.textContent = 'Error';
        indicator.className = 'px-2 py-1 rounded text-sm bg-red-500 text-white';
    }
}

// Handle network file upload
async function handleNetworkFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(await response.text());
        }
        
        const data = await response.json();
        uploadedFileId = data.file_id;
        
        // Update UI
        document.getElementById('network-file-info').innerHTML = `
            <i class="fas fa-check-circle text-green-500"></i>
            Uploaded: ${data.filename} (${formatBytes(data.size)})
        `;
        
        // Enable preview button
        document.getElementById('preview-btn').disabled = false;
        
    } catch (error) {
        alert('Upload failed: ' + error.message);
    }
}

// Handle mapping file upload
async function handleMappingFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE}/upload/mapping`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(await response.text());
        }
        
        const data = await response.json();
        mappingFileId = data.file_id;
        
        // Update UI
        document.getElementById('mapping-file-info').innerHTML = `
            <i class="fas fa-check-circle text-green-500"></i>
            Uploaded: ${data.filename} (${formatBytes(data.size)})
        `;
        
    } catch (error) {
        alert('Mapping upload failed: ' + error.message);
    }
}

// Handle preview
async function handlePreview() {
    if (!uploadedFileId) return;
    
    const sourceType = document.getElementById('source-type').value;
    
    // Show loading
    document.getElementById('preview-loading').classList.remove('hidden');
    document.getElementById('preview-results').classList.add('hidden');
    
    try {
        const response = await fetch(`${API_BASE}/preview/${uploadedFileId}?source_type=${sourceType}`);
        
        if (!response.ok) {
            throw new Error(await response.text());
        }
        
        previewData = await response.json();
        
        // Update summary counts
        document.getElementById('new-count').textContent = previewData.new_networks.length;
        document.getElementById('update-count').textContent = previewData.updated_networks.length;
        document.getElementById('overlap-count').textContent = previewData.overlapping_networks.length;
        document.getElementById('error-count').textContent = previewData.errors.length;
        
        // Show results
        document.getElementById('preview-loading').classList.add('hidden');
        document.getElementById('preview-results').classList.remove('hidden');
        
        // Show first tab
        showTab('new');
        
        // Enable import button if there are changes
        if (previewData.new_networks.length > 0 || previewData.updated_networks.length > 0) {
            document.getElementById('import-btn').disabled = false;
        }
        
    } catch (error) {
        alert('Preview failed: ' + error.message);
        document.getElementById('preview-loading').classList.add('hidden');
    }
}

// Handle tab clicks
function handleTabClick(tabBtn) {
    // Update active states
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('border-blue-600', 'text-blue-600');
        btn.classList.add('border-transparent', 'text-gray-700');
    });
    
    tabBtn.classList.remove('border-transparent', 'text-gray-700');
    tabBtn.classList.add('border-blue-600', 'text-blue-600');
    
    // Show content
    showTab(tabBtn.dataset.tab);
}

// Show tab content
function showTab(tabName) {
    const content = document.getElementById('tab-content');
    let html = '';
    
    switch (tabName) {
        case 'new':
            if (previewData.new_networks.length === 0) {
                html = '<p class="text-gray-500">No new networks to create</p>';
            } else {
                html = '<div class="space-y-2">';
                previewData.new_networks.forEach(item => {
                    html += renderNetworkItem(item);
                });
                html += '</div>';
            }
            break;
            
        case 'updates':
            if (previewData.updated_networks.length === 0) {
                html = '<p class="text-gray-500">No networks to update</p>';
            } else {
                html = '<div class="space-y-2">';
                previewData.updated_networks.forEach(item => {
                    html += renderNetworkItem(item);
                });
                html += '</div>';
            }
            break;
            
        case 'overlaps':
            if (previewData.overlapping_networks.length === 0) {
                html = '<p class="text-gray-500">No overlapping networks</p>';
            } else {
                html = '<div class="space-y-2">';
                previewData.overlapping_networks.forEach(item => {
                    html += renderNetworkItem(item);
                });
                html += '</div>';
            }
            break;
            
        case 'errors':
            if (previewData.errors.length === 0) {
                html = '<p class="text-gray-500">No errors</p>';
            } else {
                html = '<div class="space-y-2">';
                previewData.errors.forEach(error => {
                    html += `
                        <div class="bg-red-50 border border-red-200 rounded p-3">
                            <p class="font-medium text-red-800">${error.network}</p>
                            <p class="text-sm text-red-600">${error.error}</p>
                        </div>
                    `;
                });
                html += '</div>';
            }
            break;
    }
    
    content.innerHTML = html;
}

// Render network item
function renderNetworkItem(item) {
    const actionColors = {
        'create': 'green',
        'update': 'blue',
        'skip': 'yellow'
    };
    const color = actionColors[item.action] || 'gray';
    
    let tagsHtml = '';
    if (item.network.tags && Object.keys(item.network.tags).length > 0) {
        tagsHtml = '<div class="mt-1">';
        for (const [key, value] of Object.entries(item.network.tags)) {
            tagsHtml += `<span class="inline-block bg-gray-200 rounded-full px-2 py-1 text-xs text-gray-700 mr-1">${key}: ${value}</span>`;
        }
        tagsHtml += '</div>';
    }
    
    return `
        <div class="bg-${color}-50 border border-${color}-200 rounded p-3">
            <div class="flex justify-between items-start">
                <div>
                    <p class="font-medium text-${color}-800">${item.network.address} - ${item.network.name}</p>
                    <p class="text-sm text-${color}-600">${item.reason || ''}</p>
                    ${tagsHtml}
                </div>
                <span class="px-2 py-1 text-xs rounded bg-${color}-100 text-${color}-800">${item.action}</span>
            </div>
        </div>
    `;
}

// Handle import
async function handleImport() {
    if (!uploadedFileId || !previewData) return;
    
    if (!confirm('Are you sure you want to execute this import?')) {
        return;
    }
    
    const sourceType = document.getElementById('source-type').value;
    
    // Disable button and show progress
    document.getElementById('import-btn').disabled = true;
    document.getElementById('import-progress').classList.remove('hidden');
    document.getElementById('import-results').classList.add('hidden');
    
    try {
        const requestData = {
            file_id: uploadedFileId,
            source_type: sourceType,
            network_view: 'default',
            confirm: true
        };
        
        if (mappingFileId) {
            requestData.ea_mapping_file_id = mappingFileId;
        }
        
        const response = await fetch(`${API_BASE}/import/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(await response.text());
        }
        
        const data = await response.json();
        currentJobId = data.job_id;
        
        // Start monitoring progress
        monitorJob(currentJobId);
        
    } catch (error) {
        alert('Import failed: ' + error.message);
        document.getElementById('import-btn').disabled = false;
        document.getElementById('import-progress').classList.add('hidden');
    }
}

// Monitor job progress
async function monitorJob(jobId) {
    const eventSource = new EventSource(`${API_BASE}/jobs/${jobId}/stream`);
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        // Update progress bar
        document.getElementById('progress-bar').style.width = `${data.progress}%`;
        document.getElementById('progress-text').textContent = `${data.progress}%`;
        document.getElementById('progress-status').textContent = 
            `Processing: ${data.processed}/${data.total} networks`;
        
        if (data.status === 'completed' || data.status === 'failed') {
            eventSource.close();
            handleJobComplete(jobId);
        }
    };
    
    eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        eventSource.close();
        handleJobComplete(jobId);
    };
}

// Handle job completion
async function handleJobComplete(jobId) {
    try {
        const response = await fetch(`${API_BASE}/jobs/${jobId}`);
        const job = await response.json();
        
        document.getElementById('import-progress').classList.add('hidden');
        
        if (job.status === 'completed') {
            // Show results
            const results = job.results;
            document.getElementById('results-summary').innerHTML = `
                <p>✓ Created: ${results.created} networks</p>
                <p>✓ Updated: ${results.updated} networks</p>
                <p>⚠ Skipped: ${results.skipped} networks</p>
                ${results.failed > 0 ? `<p>✗ Failed: ${results.failed} networks</p>` : ''}
            `;
            document.getElementById('import-results').classList.remove('hidden');
        } else {
            alert('Import failed: ' + (job.results?.error || 'Unknown error'));
        }
        
        // Reload jobs list
        loadJobs();
        
        // Reset state
        currentJobId = null;
        document.getElementById('import-btn').disabled = true;
        
    } catch (error) {
        console.error('Error fetching job status:', error);
    }
}

// Load jobs history
async function loadJobs() {
    try {
        const response = await fetch(`${API_BASE}/jobs`);
        const data = await response.json();
        
        const jobsList = document.getElementById('jobs-list');
        
        if (data.jobs.length === 0) {
            jobsList.innerHTML = '<p class="text-gray-500">No import history</p>';
            return;
        }
        
        let html = '';
        data.jobs.reverse().forEach(job => {
            const statusColors = {
                'completed': 'green',
                'processing': 'blue',
                'queued': 'yellow',
                'failed': 'red'
            };
            const color = statusColors[job.status] || 'gray';
            
            html += `
                <div class="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <div>
                        <p class="font-medium">Job ${job.job_id.slice(0, 8)}...</p>
                        <p class="text-sm text-gray-600">
                            Started: ${job.started_at ? new Date(job.started_at).toLocaleString() : 'N/A'}
                        </p>
                    </div>
                    <div class="flex items-center">
                        <span class="px-2 py-1 text-xs rounded bg-${color}-100 text-${color}-800">
                            ${job.status}
                        </span>
                        ${job.status === 'completed' || job.status === 'failed' ? 
                            `<button onclick="deleteJob('${job.job_id}')" class="ml-2 text-red-500 hover:text-red-700">
                                <i class="fas fa-trash"></i>
                            </button>` : ''}
                    </div>
                </div>
            `;
        });
        
        jobsList.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading jobs:', error);
    }
}

// Delete job
async function deleteJob(jobId) {
    if (!confirm('Delete this job from history?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/jobs/${jobId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadJobs();
        }
    } catch (error) {
        console.error('Error deleting job:', error);
    }
}

// Utility function to format bytes
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Refresh connection status every 30 seconds
setInterval(checkConnection, 30000);
