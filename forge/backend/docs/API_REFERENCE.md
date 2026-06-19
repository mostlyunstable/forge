# Forge Backend API Reference

## Base URL
```
http://localhost:8000
```

## Authentication
All endpoints require JWT Bearer token authentication.

```bash
# Get token (for development)
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' | jq -r '.access_token')

# Use token
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/projects
```

## Endpoints

### Health Check
```
GET /health
```
Response: `{"status": "ok"}`

### Metrics
```
GET /metrics
```
Prometheus metrics endpoint.

---

## Projects

### Create Project
```
POST /api/v1/projects
```
```json
{
  "name": "My Project",
  "description": "A sample project",
  "stack": ["python", "fastapi"],
  "goals": ["Build API", "Add tests"],
  "repository_url": "https://github.com/user/repo"
}
```

### List Projects
```
GET /api/v1/projects?skip=0&limit=100
```

### Get Project
```
GET /api/v1/projects/{project_id}
```

---

## Memory

### Save Decision
```
POST /api/v1/memory/decisions
```
```json
{
  "project_id": "uuid",
  "title": "Use FastAPI",
  "decision": "We chose FastAPI for performance",
  "reason": "Benchmark results showed 3x faster than Flask",
  "alternatives": ["Flask", "Django"]
}
```

### Save Bug
```
POST /api/v1/memory/bugs
```
```json
{
  "project_id": "uuid",
  "title": "Auth token expiration",
  "problem": "Users logged out unexpectedly",
  "root_cause": "Token TTL was 5 minutes",
  "solution": "Extended TTL to 30 minutes",
  "affected_files": ["auth.py", "middleware.py"],
  "severity": "high"
}
```

### Save Preference
```
POST /api/v1/memory/preferences
```
```json
{
  "key": "code_style",
  "value": "black",
  "confidence": 0.9
}
```

### Get Preferences
```
GET /api/v1/memory/preferences
```

### Search Memories
```
GET /api/v1/memory/search?q=authentication&project_id=uuid
```

---

## Code

### Index Repository
```
POST /api/v1/code/index
```
```json
{
  "project_id": "uuid",
  "repo_path": "/path/to/repo"
}
```

### Search Code
```
GET /api/v1/code/search?q=function_name&project_id=uuid
```

### Get File Entries
```
GET /api/v1/code/files/{project_id}/{file_path}
```

---

## Dependencies

### Build Dependency Graph
```
POST /api/v1/dependencies/build
```
```json
{
  "project_id": "uuid",
  "indexed_files": [
    {
      "file_path": "src/main.py",
      "content": "import utils\n",
      "entries": []
    }
  ]
}
```

### Get Import Graph
```
GET /api/v1/dependencies/import-graph/{project_id}?file_path=src/main.py
```

### Get Call Graph
```
GET /api/v1/dependencies/call-graph/{project_id}?entry_name=my_function
```

---

## Git

### Analyze Commits
```
GET /api/v1/git/commits/{project_id}?limit=50
```

---

## Chat

### Send Message
```
POST /api/v1/chat
```
```json
{
  "project_id": "uuid",
  "message": "What authentication pattern should I use?"
}
```

---

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message"
}
```

Status codes:
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `409` - Conflict
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error
