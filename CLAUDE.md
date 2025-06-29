# SENECHAL DEVELOPMENT GUIDE

## Build and Run Commands
- Start server: `uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Run single test: `python test_health.py` or `python app/etl/test.py`
- Initialize database: `python app/etl/init_db.py`
- Run ETL process: `python app/etl/run.py` (Garmin) or `python app/etl/withings_run.py` (Withings)

## Code Style Guidelines
- **Structure**: FastAPI app with modular organization under `/app` directory
- **Imports**: Standard lib → Third-party → Local (alphabetized within groups)
- **Typing**: Use full type annotations with `typing` module, Pydantic models for validation
- **Naming**: snake_case for variables/functions, CamelCase for classes, UPPERCASE for constants
- **Error Handling**: Use HTTP exceptions with status codes, try-except with specific handling
- **Documentation**: Docstrings for functions/classes, comments for complex logic
- **API Design**: RESTful endpoints, consistent response models, proper validation
- **Database**: Use parameterized queries, handle connection errors appropriately
- **Authentication**: API key validation with role-based access control

Follow these guidelines when extending the codebase to maintain consistency.

## MCP Configuration
```json
{
  "mcpServers": {
    "senechal": {
      "url": "https://strangelooping.xyz/api/senechal/mcp/definition",
      "headers": {
        "x-api-key": "HandwritingRepair"
      }
    }
  }
}
```