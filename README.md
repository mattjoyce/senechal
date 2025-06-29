# Senechal API

Senechal is a personal API designed to retrieve data from various sources and expose it through a structured FastAPI service. It features a unified LLM service for content processing, health data tracking, and learning management.

## **Features**
- **Unified LLM Service**: Process content from URLs or text using various AI models with flexible prompts
- **Health Data Integration**: Track rowing workouts and health metrics with automated data extraction
- **Learning Management**: Extract knowledge from content and save structured learning notes
- **Content Analysis**: Summarize, classify, extract key information, and analyze sentiment
- Secure API key-based authentication with role-based access control (RBAC)
- RESTful API design with comprehensive OpenAPI documentation
- Designed to be run as a systemd service for stability
- Reverse proxied via NGINX for HTTPS access
- Runs inside a Python virtual environment (venv) for dependency management

---

## **Installation & Setup**
### **1. Clone the Repository**
```bash
cd /home/ubuntu/api/
git clone https://github.com/yourusername/senechal.git
```

### **2. Set Up the Virtual Environment**
```bash
cd /home/ubuntu/api/senechal
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **3. Configure API Keys & Roles**
Modify `config/api_keys.yaml` and `config/api_roles.yaml`:

#### **`config/api_keys.yaml`**
```yaml
api_keys:
  "abc123": "read"
  "xyz789": "write"
```

#### **`config/api_roles.yaml`**
```yaml
roles:
  read:
    access:
      - "/getTest"
  write:
    access:
      - "/getTest"
      - "/setTest"
```

Ensure these files are **not publicly accessible** by setting permissions:
```bash
chmod 600 /home/ubuntu/api/senechal/config/api_keys.yaml
chmod 600 /home/ubuntu/api/senechal/config/api_roles.yaml
```

### **4. Set Up the Systemd Service**
Create the systemd service file:
```bash
sudo nano /etc/systemd/system/senechal.service
```

#### **`/etc/systemd/system/senechal.service`**
```ini
[Unit]
Description=Senechal API (FastAPI)
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/api/senechal
ExecStart=/home/ubuntu/api/senechal/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Reload and enable the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable senechal
sudo systemctl start senechal
sudo systemctl status senechal
```

---

## **NGINX Configuration**
Ensure that NGINX is correctly proxying requests to the FastAPI service. Edit the NGINX site configuration:
```bash
sudo nano /etc/nginx/sites-enabled/yourwebsite.conf
```

Add the following:
```nginx
location /api/senechal/ {
    proxy_pass http://127.0.0.1:8000/;
    rewrite ^/api/senechal(/.*)$ $1 break;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Test and reload NGINX:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## **API Endpoints**

### **Unified LLM Service**
All LLM operations are now consolidated under `/llm/` endpoints:

#### **Main Processing**
- `POST /llm/process` - Unified LLM processing with full parameter control
- `GET /llm/prompts` - List available named prompts  
- `GET /llm/list` - List all saved LLM results
- `GET /llm/file/{id}` - Retrieve saved result by ID
- `DELETE /llm/file/{id}` - Delete saved result

#### **Convenience Endpoints**
- `POST /llm/extract` - Extract learning points from content (equivalent to `/learning/scrape`)
- `POST /llm/analyze` - Analyze content with various types (summary, extraction, classification)
- `POST /llm/custom` - Process content with custom prompts

### **Health Data**
- `POST /health/rowing/submit` - Submit rowing workout image for data extraction
- `GET /health/rowing/get/{period}` - Get rowing workout data
- `GET /health/summary/{period}` - Get health metrics summary
- `GET /health/profile` - Get health profile

### **Legacy Endpoints (Backward Compatible)**
- `POST /learning/scrape` - Now uses unified LLM service internally
- `POST /analysis/analyze` - Now uses unified LLM service internally
- `GET /analysis/list` - List analysis results
- `GET /analysis/types` - Get available analysis types

## **Example Usage**

### **Extract Learning from URL**
```bash
curl -X POST "https://yoursite.com/api/senechal/llm/extract" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"query_url": "https://example.com/article", "save_result": true}'
```

### **Analyze Text Content**
```bash
curl -X POST "https://yoursite.com/api/senechal/llm/analyze" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "analysis_type": "summary",
    "query_text": "Your text content here",
    "save_result": false
  }'
```

### **Custom Prompt Processing**
```bash
curl -X POST "https://yoursite.com/api/senechal/llm/custom" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "custom_prompt": "Translate this to French:",
    "query_text": "Hello, how are you?",
    "save_result": false
  }'
```

### **List Available Prompts**
```bash
curl -H "X-API-Key: your-api-key" \
  "https://yoursite.com/api/senechal/llm/prompts"
```

---

## **Testing the API**
Test basic functionality:
```bash
curl -H "X-API-Key: HandwritingRepair" https://yourwebsite.com/api/senechal/getTest
```

Test unified LLM service:
```bash
curl -H "X-API-Key: HandwritingRepair" https://yourwebsite.com/api/senechal/llm/prompts
```

Expected prompts output:
```json
{
  "status": "success",
  "message": "Found 5 available prompts",
  "data": [
    {"name": "extract_learning", "description": "Extract key learning points", "category": "learning"},
    {"name": "analyze_summary", "description": "Generate comprehensive summary", "category": "analysis"}
  ]
}
```

If errors occur, check logs:
```bash
sudo journalctl -u senechal --no-pager --lines=50
sudo tail -f /var/log/nginx/error.log
```

---

## **Configuration**

### **Environment Variables** (`.env` file)
```bash
# Database Paths
WITHINGS_DB_PATH=/path/to/withings.db
SENECHAL_DB_PATH=/path/to/senechal.db

# File Locations  
LEARNING_CONTENT_PATH=/path/to/learning_content

# API Configuration
API_KEYS_PATH=/path/to/api_keys.yaml
API_ROLES_PATH=/path/to/api_roles.yaml
HEALTH_PROFILE_PATH=/path/to/health_profile.json

# API Endpoint
SENECHAL_API_URL=http://127.0.0.1:8000
SENECHAL_API_KEY=HandwritingRepair

# External APIs
JINAAI_API_KEY=your_jina_api_key
YOUTUBE_API_KEY=your_youtube_api_key
```

### **Required Roles** (`api_roles.yaml`)
Ensure your API roles include the new LLM endpoints:
```yaml
roles:
  admin:
    access:
      - "/health/profile"
      - "/health/rowing/submit" 
      - "/learning/scrape"
      - "/analysis/analyze"
      - "/llm/process"
      - "/llm/prompts"
      - "/llm/list"
      - "/llm/file"
      - "/llm/extract"
      - "/llm/analyze"
      - "/llm/custom"
```

---

## **Updating the API**
To pull new updates and restart:
```bash
cd /home/ubuntu/api/senechal
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart senechal
```

## **Running Tests**
Test all endpoints:
```bash
python test_api_endpoints.py
```

## **Development**
Start development server:
```bash
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## **API Documentation**
View interactive API docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI Spec: `http://localhost:8000/openapi.json`



