from fastapi import FastAPI, Request
from fastapi.responses import Response
import httpx
import socket

app = FastAPI()

# Replace with your backend's IPv4 address and original hostname
BACKEND_IP = "143.244.220.150"
BACKEND_HOSTNAME = "ey57.pegalabs.io"

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(path: str, request: Request):
    # Copy headers and set Host to original hostname
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
    headers["Host"] = BACKEND_HOSTNAME

    # Build the full URL using IP
    url = f"https://{BACKEND_IP}/{path}"

    # Use HTTPX AsyncClient with IPv4 only
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.query_params,
            content=await request.body(),
            timeout=30.0
        )

    # Forward response
    return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))
