from fastapi import FastAPI, Depends
from .auth import check_access, get_api_key
from .health.routes import router as health_router
from pydantic import BaseModel
from logging import getLogger

app = FastAPI()
logger = getLogger(__name__)

# Include the health router
app.include_router(health_router)

# Data model for writing to file
class TestData(BaseModel):
    content: str

# Read-only endpoint
@app.get("/getTest", dependencies=[Depends(check_access("/getTest"))])
async def get_test():
    try:
        with open("test.txt", "r") as f:
            content = f.read()
        return {"file_content": content}
    except FileNotFoundError:
        return {"file_content": "File not found"}

# Write endpoint (Only "write" role can access)
@app.post("/setTest", dependencies=[Depends(check_access("/setTest"))])
async def set_test(data: TestData, api_key_data: dict = Depends(get_api_key)):
    logger.info(f"API Call: /setTest | API Key: {api_key_data['role']} | Data: {data.content}")
    with open("test.txt", "w") as f:
        f.write(data.content)
    return {"message": "File updated successfully"}
