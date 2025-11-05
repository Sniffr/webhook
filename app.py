"""
Simple Request Logger with FastAPI
Logs all incoming HTTP requests and displays them in a real-time web UI
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import json
import asyncio
from collections import deque
from typing import Dict, Any

app = FastAPI(title="Request Logger")

# In-memory storage for requests (keeping last 100 requests)
requests_log = deque(maxlen=100)

# Active SSE connections
sse_clients = []


async def format_request(request: Request, body: bytes) -> Dict[str, Any]:
    """Format request data for logging"""
    return {
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "headers": dict(request.headers),
        "body": body.decode('utf-8', errors='replace') if body else "",
        "client": request.client.host if request.client else "unknown"
    }


async def notify_clients(request_data: Dict[str, Any]):
    """Send new request data to all connected SSE clients"""
    message = f"data: {json.dumps(request_data)}\n\n"
    # Remove disconnected clients
    for client_queue in list(sse_clients):
        try:
            await client_queue.put(message)
        except:
            sse_clients.remove(client_queue)


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main UI"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Request Logger</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
        }
        
        .header {
            background: #2c3e50;
            color: white;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .header p {
            color: #bdc3c7;
            font-size: 14px;
        }
        
        .container {
            max-width: 1400px;
            margin: 20px auto;
            padding: 0 20px;
        }
        
        .controls {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .controls button {
            background: #e74c3c;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }
        
        .controls button:hover {
            background: #c0392b;
        }
        
        .request-item {
            background: white;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .request-header {
            padding: 15px 20px;
            background: #ecf0f1;
            border-left: 4px solid #3498db;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .request-header:hover {
            background: #d5dbdb;
        }
        
        .request-summary {
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .method {
            font-weight: bold;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            text-transform: uppercase;
        }
        
        .method.GET { background: #3498db; color: white; }
        .method.POST { background: #2ecc71; color: white; }
        .method.PUT { background: #f39c12; color: white; }
        .method.DELETE { background: #e74c3c; color: white; }
        .method.PATCH { background: #9b59b6; color: white; }
        
        .path {
            font-family: 'Courier New', monospace;
            font-size: 14px;
            color: #2c3e50;
        }
        
        .timestamp {
            color: #7f8c8d;
            font-size: 12px;
        }
        
        .request-details {
            padding: 20px;
            display: none;
            border-top: 1px solid #ecf0f1;
        }
        
        .request-details.visible {
            display: block;
        }
        
        .detail-section {
            margin-bottom: 20px;
        }
        
        .detail-section h3 {
            font-size: 14px;
            color: #7f8c8d;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        
        .detail-content {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #95a5a6;
        }
        
        .empty-state svg {
            width: 80px;
            height: 80px;
            margin-bottom: 20px;
            opacity: 0.3;
        }
        
        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #2ecc71;
            margin-right: 5px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔗 Request Logger</h1>
        <p><span class="status-indicator"></span> Listening for requests... Send HTTP requests to this URL</p>
    </div>
    
    <div class="container">
        <div class="controls">
            <button onclick="clearRequests()">Clear All Requests</button>
        </div>
        
        <div id="requests-container">
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
                </svg>
                <h2>No requests yet</h2>
                <p>Waiting for incoming HTTP requests...</p>
            </div>
        </div>
    </div>
    
    <script>
        const requestsContainer = document.getElementById('requests-container');
        
        function clearRequests() {
            requestsContainer.innerHTML = `
                <div class="empty-state">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
                    </svg>
                    <h2>No requests yet</h2>
                    <p>Waiting for incoming HTTP requests...</p>
                </div>
            `;
        }
        
        function toggleDetails(id) {
            const details = document.getElementById(`details-${id}`);
            details.classList.toggle('visible');
        }
        
        function formatJson(obj) {
            return JSON.stringify(obj, null, 2);
        }
        
        function addRequest(data) {
            // Remove empty state if present
            const emptyState = requestsContainer.querySelector('.empty-state');
            if (emptyState) {
                emptyState.remove();
            }
            
            const id = Date.now() + Math.random();
            const requestDiv = document.createElement('div');
            requestDiv.className = 'request-item';
            requestDiv.innerHTML = `
                <div class="request-header" onclick="toggleDetails('${id}')">
                    <div class="request-summary">
                        <span class="method ${data.method}">${data.method}</span>
                        <span class="path">${data.path}${data.query_params && Object.keys(data.query_params).length ? '?' + new URLSearchParams(data.query_params).toString() : ''}</span>
                        <span class="timestamp">${new Date(data.timestamp).toLocaleString()}</span>
                    </div>
                    <div>▼</div>
                </div>
                <div id="details-${id}" class="request-details">
                    ${data.query_params && Object.keys(data.query_params).length ? `
                    <div class="detail-section">
                        <h3>Query Parameters</h3>
                        <div class="detail-content">${formatJson(data.query_params)}</div>
                    </div>
                    ` : ''}
                    
                    <div class="detail-section">
                        <h3>Headers</h3>
                        <div class="detail-content">${formatJson(data.headers)}</div>
                    </div>
                    
                    ${data.body ? `
                    <div class="detail-section">
                        <h3>Body</h3>
                        <div class="detail-content">${data.body}</div>
                    </div>
                    ` : ''}
                    
                    <div class="detail-section">
                        <h3>Client IP</h3>
                        <div class="detail-content">${data.client}</div>
                    </div>
                </div>
            `;
            
            requestsContainer.insertBefore(requestDiv, requestsContainer.firstChild);
        }
        
        // Connect to SSE endpoint for real-time updates
        const eventSource = new EventSource('/events');
        
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            addRequest(data);
        };
        
        eventSource.onerror = function(error) {
            console.error('SSE connection error:', error);
            // Try to reconnect automatically after a delay
            setTimeout(() => {
                window.location.reload();
            }, 5000);
        };
        
        // Load existing requests on page load
        fetch('/api/requests')
            .then(response => response.json())
            .then(requests => {
                requests.reverse().forEach(req => addRequest(req));
            })
            .catch(error => console.error('Error loading requests:', error));
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.get("/events")
async def events(request: Request):
    """Server-Sent Events endpoint for real-time updates"""
    async def event_generator():
        client_queue = asyncio.Queue()
        sse_clients.append(client_queue)
        
        try:
            while True:
                # Check if client is still connected
                if await request.is_disconnected():
                    break
                    
                # Wait for new messages
                try:
                    message = await asyncio.wait_for(client_queue.get(), timeout=30.0)
                    yield message
                except asyncio.TimeoutError:
                    # Send keep-alive comment
                    yield ": keep-alive\n\n"
        finally:
            sse_clients.remove(client_queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/requests")
async def get_requests():
    """Get all logged requests"""
    return list(requests_log)


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def catch_all(request: Request, path: str):
    """Catch-all route to log any request"""
    # Skip logging for internal endpoints
    if path in ["", "events", "api/requests"]:
        return {"message": "This is an internal endpoint"}
    
    # Read request body
    body = await request.body()
    
    # Format and store request
    request_data = await format_request(request, body)
    requests_log.appendleft(request_data)
    
    # Notify SSE clients
    await notify_clients(request_data)
    
    # Return success response
    return {
        "status": "logged",
        "message": "Request has been logged successfully",
        "timestamp": request_data["timestamp"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
