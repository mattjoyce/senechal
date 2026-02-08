"""FastAPI application with middleware for logging requests and handling API keys."""
import logging
import time

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from .auth import check_access, get_api_key
from .health.routes import router as health_router
from .learning.routes import router as learning_router
from .analysis.routes import router as analysis_router
from .llm.routes import router as llm_router
from .logging_config import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)
api_logger = logging.getLogger("api")


# API request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log API requests and their processing time."""
    async def dispatch(self, request: Request, call_next):
        """Log incoming requests and their processing time."""
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

# Optional prefix stripping for reverse proxy paths like /api/senechal
class StripPrefixMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, prefix: str):
        super().__init__(app)
        self.prefix = prefix

    async def dispatch(self, request: Request, call_next):
        path = request.scope.get("path", "")
        if path.startswith(self.prefix):
            new_path = path[len(self.prefix):] or "/"
            request.scope["path"] = new_path
        return await call_next(request)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(StripPrefixMiddleware, prefix="/api/senechal")

# Mount static files directory
app.mount("/static", StaticFiles(directory="app/static"), name="senechal-static")

# Include the health router
app.include_router(health_router)
# Add this line to include the learning router
app.include_router(learning_router)
# Include the analysis router
app.include_router(analysis_router)
# Include the unified LLM router
app.include_router(llm_router)

# Data model for writing to file
class TestData(BaseModel):
    """Data model for writing to a file"""
    content: str


# Read-only endpoint
@app.get("/getTest", dependencies=[Depends(check_access("/getTest"))])
async def get_test():
    """Read data from a file"""
    try:
        with open("test.txt", "r", encoding="utf-8") as file:
            content = file.read()
        return {"file_content": content}
    except FileNotFoundError:
        return {"file_content": "File not found"}


# Write endpoint (Only "write" role can access)
@app.post("/setTest", dependencies=[Depends(check_access("/setTest"))])
async def set_test(data: TestData, api_key_data: dict = Depends(get_api_key)):
    """Write data to a file"""
    logger.info(
        f"API Call: /setTest | API Key: {api_key_data['role']} | Data: {data.content}"
    )
    with open("test.txt", "w", encoding="utf-8") as file:
        file.write(data.content)
    return {"message": "File updated successfully"}
