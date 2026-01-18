"""Admin API endpoints for system configuration."""
import logging
import os
import subprocess
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class APIKeyUpdate(BaseModel):
    """Request to update API key."""
    api_key: str


class APIKeyResponse(BaseModel):
    """Response for API key operations."""
    success: bool
    message: str
    key_preview: str = ""


def is_local_request(request: Request) -> bool:
    """Check if request is from localhost."""
    client_host = request.client.host if request.client else ""
    forwarded = request.headers.get("X-Forwarded-For", "")
    real_ip = request.headers.get("X-Real-IP", "")

    local_ips = ["127.0.0.1", "localhost", "::1", "172.18.0.1"]

    return (
        client_host in local_ips or
        any(ip in forwarded for ip in local_ips) or
        real_ip in local_ips
    )


@router.get("/api-key", response_model=APIKeyResponse)
async def get_api_key_status(request: Request):
    """Get current API key status (masked)."""
    if not is_local_request(request):
        raise HTTPException(status_code=403, detail="Admin endpoints only accessible from localhost")

    from app.config import get_settings
    settings = get_settings()

    key = settings.anthropic_api_key
    if key:
        # Show first 10 and last 4 characters
        preview = key[:10] + "..." + key[-4:] if len(key) > 14 else "***"
    else:
        preview = "(not set)"

    return APIKeyResponse(
        success=True,
        message="API key configured" if key else "API key not configured",
        key_preview=preview
    )


@router.post("/api-key", response_model=APIKeyResponse)
async def update_api_key(request: Request, data: APIKeyUpdate):
    """
    Update the Anthropic API key.

    This endpoint is restricted to localhost only for security.
    After updating, you need to restart the API container.
    """
    if not is_local_request(request):
        raise HTTPException(status_code=403, detail="Admin endpoints only accessible from localhost")

    new_key = data.api_key.strip()

    # Validate key format
    if not new_key.startswith("sk-ant-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid API key format. Key should start with 'sk-ant-'"
        )

    env_file = "/opt/jlegal/.env"

    try:
        # Read current .env file
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                lines = f.readlines()
        else:
            lines = []

        # Update or add the API key line
        key_found = False
        new_lines = []
        for line in lines:
            if line.startswith("ANTHROPIC_API_KEY="):
                new_lines.append(f"ANTHROPIC_API_KEY={new_key}\n")
                key_found = True
            else:
                new_lines.append(line)

        if not key_found:
            new_lines.append(f"ANTHROPIC_API_KEY={new_key}\n")

        # Write back
        with open(env_file, "w") as f:
            f.writelines(new_lines)

        preview = new_key[:10] + "..." + new_key[-4:]

        return APIKeyResponse(
            success=True,
            message="API key updated. Please restart the API container to apply changes.",
            key_preview=preview
        )

    except PermissionError:
        raise HTTPException(
            status_code=500,
            detail="Permission denied. Cannot write to .env file."
        )
    except Exception as e:
        logger.error(f"Error updating API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart")
async def restart_api(request: Request):
    """
    Signal that a restart is needed.

    Note: This doesn't actually restart - it just returns instructions.
    The actual restart must be done via docker-compose.
    """
    if not is_local_request(request):
        raise HTTPException(status_code=403, detail="Admin endpoints only accessible from localhost")

    return {
        "message": "To apply changes, run: docker-compose restart api",
        "command": "cd /opt/jlegal && docker-compose restart api"
    }
