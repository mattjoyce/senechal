# Senechal API

Senechal is a personal API designed to retrieve data from various sources and expose it through a structured FastAPI service.

## **Features**
- Secure API key-based authentication
- Role-based access control (RBAC) using YAML configuration
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

## **Testing the API**
Ensure that the API responds correctly:
```bash
curl -H "X-API-Key: abc123" https://yourwebsite.com/api/senechal/getTest
```
Expected output:
```json
{"file_content": "Hello, Senechal!"}
```

If errors occur, check logs:
```bash
sudo journalctl -u senechal --no-pager --lines=50
sudo tail -f /var/log/nginx/error.log
```

---

## **Updating the API**
To pull new updates and restart:
```bash
cd /home/ubuntu/api/senechal
git pull origin main
sudo systemctl restart senechal
```



