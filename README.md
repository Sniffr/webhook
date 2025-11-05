# Request Logger

A simple Python application using FastAPI that logs all incoming HTTP requests and displays them in a real-time web UI, similar to webhook.site.

## Features

- 🚀 Logs all HTTP requests (GET, POST, PUT, DELETE, PATCH, etc.)
- 📊 Real-time UI updates using Server-Sent Events (SSE)
- 📝 Captures complete request details:
  - HTTP method and path
  - Query parameters
  - Headers
  - Request body
  - Client IP
  - Timestamp
- 🎨 Clean, modern web interface
- 💾 In-memory storage (last 100 requests)
- 🔄 Auto-refresh capabilities

## Installation

1. Install Python 3.7 or higher

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the server:
```bash
python app.py
```

Or using uvicorn directly:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

3. Send HTTP requests to any endpoint (except `/`, `/events`, and `/api/requests`):
```bash
# Example requests
curl http://localhost:8000/test
curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d '{"key": "value"}'
curl http://localhost:8000/api/users?id=123
```

4. View the logged requests in the web UI in real-time!

## API Endpoints

- `GET /` - Web UI interface
- `GET /events` - Server-Sent Events stream for real-time updates
- `GET /api/requests` - Get all logged requests as JSON
- `ANY /{path}` - Catch-all route that logs the request

## How It Works

1. The application uses FastAPI to create a web server with a catch-all route
2. All incoming requests are logged to an in-memory deque (max 100 requests)
3. The web UI connects via Server-Sent Events (SSE) for real-time updates
4. When a new request arrives, it's immediately pushed to all connected clients
5. The UI displays requests with expandable details

## Development

The application is intentionally simple and self-contained:
- Single `app.py` file with both backend and frontend code
- No database required (in-memory storage)
- Minimal dependencies (just FastAPI and uvicorn)

## Customization

You can customize the application by modifying `app.py`:
- Change the maximum number of stored requests (default: 100)
- Modify the UI styling in the HTML template
- Add authentication if needed
- Persist requests to a database

## License

MIT
