import logging
import time

from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from .auth import check_access, get_api_key
from .health.routes import router as health_router
from .logging_config import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)
api_logger = logging.getLogger('api')

# API request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get client IP - considers X-Forwarded-For header for proxy setups
        client_ip = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
            
        # Get request details
        method = request.method
        path = request.url.path
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log the request details
            api_logger.info(
                f"REQUEST: {client_ip} - {method} {path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
            
            return response
            
        except Exception as exception:
            api_logger.error(
                f"REQUEST ERROR: {client_ip} - {method} {path} - "
                f"Error: {str(exception)}"
            )
            raise

app = FastAPI()

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include the health router
app.include_router(health_router)

# Data model for writing to file
class TestData(BaseModel):
    content: str

# Read-only endpoint
@app.get("/getTest", dependencies=[Depends(check_access("/getTest"))])
async def get_test():
    try:
        with open("test.txt", "r", encoding="utf-8") as file:
            content = file.read()
        return {"file_content": content}
    except FileNotFoundError:
        return {"file_content": "File not found"}

# Write endpoint (Only "write" role can access)
@app.post("/setTest", dependencies=[Depends(check_access("/setTest"))])
async def set_test(data: TestData, api_key_data: dict = Depends(get_api_key)):
    logger.info(f"API Call: /setTest | API Key: {api_key_data['role']} | Data: {data.content}")
    with open("test.txt", "w", encoding="utf-8") as file:
        file.write(data.content)
    return {"message": "File updated successfully"}