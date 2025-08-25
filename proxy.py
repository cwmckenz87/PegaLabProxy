from fastapi import FastAPI, Request
from fastapi.responses import Response
import httpx

app = FastAPI()

BACKEND_URL = "https://ey57.pegalabs.io"  # target AWS ELB

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(path: str, request: Request):
    # Forward headers except Host
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
    
    # Forward query params and body
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method=request.method,
            url=f"{BACKEND_URL}/{path}",
            headers=headers,
            params=request.query_params,
            content=await request.body(),
            timeout=30.0
        )
    # Return response as-is
    return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))
