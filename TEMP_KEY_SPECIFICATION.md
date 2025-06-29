# Temporary API Key Management for Senechal

## Overview

This enhancement adds temporary API key management to Senechal, allowing the owner to create time-limited API keys for specific roles. These keys can be listed, revoked, and managed through a secure API interface.

## API Endpoints

### 1. Create Temporary API Key

```
POST /admin/keys/temporary
```

**Request:**
```json
{
  "role": "read",
  "duration": 3600,
  "note": "Claude session 2025-02-27"
}
```

**Parameters:**
- `role` (string, required): Existing role name from api_roles.yaml
- `duration` (integer, required): Duration in seconds until key expiration
- `note` (string, optional): Description for this key's purpose

**Response:**
```json
{
  "key": "temp_a1b2c3d4e5f6",
  "role": "read",
  "expires_at": "2025-02-27T15:45:30Z",
  "access_paths": ["/getTest", "/health/profile"],
  "note": "Claude session 2025-02-27"
}
```

### 2. List Temporary API Keys

```
GET /admin/keys/temporary
```

**Response:**
```json
{
  "keys": [
    {
      "key_id": "temp_a1b2c3d4e5f6",
      "role": "read",
      "created_at": "2025-02-27T14:45:30Z",
      "expires_at": "2025-02-27T15:45:30Z", 
      "active": true,
      "note": "Claude session 2025-02-27"
    },
    {
      "key_id": "temp_f6e5d4c3b2a1",
      "role": "write",
      "created_at": "2025-02-26T10:30:00Z",
      "expires_at": "2025-02-26T12:30:00Z",
      "active": false,
      "note": "Test key"
    }
  ]
}
```

### 3. Revoke Temporary API Key

```
DELETE /admin/keys/temporary/{key_id}
```

**Response:**
```json
{
  "key_id": "temp_a1b2c3d4e5f6",
  "status": "revoked",
  "revoked_at": "2025-02-27T15:15:22Z"
}
```

### 4. Get Temporary API Key Details

```
GET /admin/keys/temporary/{key_id}
```

**Response:**
```json
{
  "key_id": "temp_a1b2c3d4e5f6",
  "role": "read",
  "created_at": "2025-02-27T14:45:30Z",
  "expires_at": "2025-02-27T15:45:30Z",
  "active": true,
  "access_paths": ["/getTest", "/health/profile"],
  "note": "Claude session 2025-02-27"
}
```

## Implementation Details

### Database Schema

Add a new table to store temporary keys:

```sql
CREATE TABLE IF NOT EXISTS temp_api_keys (
  key_id TEXT PRIMARY KEY,
  key_value TEXT NOT NULL,
  role TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  revoked_at TIMESTAMP,
  note TEXT
);
```

### Security Considerations

1. **Authentication**: All key management endpoints should require owner authentication (separate from normal API authentication)
2. **Key Storage**: Store only hashed values of keys in the database
3. **Expiration**: Implement a background task to clean up expired keys
4. **Rate Limiting**: Implement rate limiting on temporary key creation
5. **Logging**: Log all key creation, usage, and revocation events

### Implementation Plan

1. Create a new module in the Senechal codebase:
```
app/
  admin/
    __init__.py
    keys.py
    routes.py
```

2. Update auth.py to verify both permanent and temporary API keys
3. Add database migration for the new temp_api_keys table
4. Implement the REST endpoints with appropriate authorization
5. Add key cleanup background task to the application startup

## CLI Usage Examples

### Create a temporary key:
```bash
curl -X POST https://your-senechal-api.com/admin/keys/temporary \
  -H "Authorization: Bearer your-admin-token" \
  -H "Content-Type: application/json" \
  -d '{"role": "read", "duration": 3600, "note": "Claude session"}'
```

### List all temporary keys:
```bash
curl -X GET https://your-senechal-api.com/admin/keys/temporary \
  -H "Authorization: Bearer your-admin-token"
```

### Revoke a key:
```bash
curl -X DELETE https://your-senechal-api.com/admin/keys/temporary/temp_a1b2c3d4e5f6 \
  -H "Authorization: Bearer your-admin-token"
```

## Integration with MCP

This temporary key functionality pairs well with the MCP integration, allowing you to create short-lived keys specifically for AI model sessions. Consider implementing:

1. A convenience endpoint that returns both a temporary key and the MCP definition in one call
2. Automatic key generation for new AI sessions
3. Usage tracking to understand how AI models are utilizing your API