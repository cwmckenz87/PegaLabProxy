from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import os

app = FastAPI()

# Backend hostname you want to proxy to
BACKEND_HOSTNAME = os.environ.get("BACKEND_HOSTNAME", "ey57.pegalabs.io")

# === Healthcheck ===
@app.get("/health")
async def health():
    return {"status": "ok"}

# === My public IP endpoint ===
@app.get("/myip")
async def myip():
    # use a public service to detect outbound IP
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get("https://ifconfig.me/ip")
            public_ip = resp.text.strip()
        except Exception as e:
            return JSONResponse({"error": f"Cannot determine IP: {e}"}, status_code=500)
    return {"public_ip": public_ip}

# === Proxy passthrough ===
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy(path: str, request: Request):
    url = f"https://{BACKEND_HOSTNAME}/{path}"
    
    # Copy headers except host
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}

    async with httpx.AsyncClient(timeout=30.0, verify=True) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                params=request.query_params,
                content=await request.body(),
                stream=True  # Stream the response
            )
        except httpx.ConnectTimeout:
            return JSONResponse({"error": "ConnectTimeout — cannot reach backend"}, status_code=504)
        except httpx.HTTPError as e:
            return JSONResponse({"error": f"HTTP error: {e}"}, status_code=502)

        # Forward all headers except hop-by-hop headers
        excluded_headers = {"connection", "keep-alive", "transfer-encoding", "upgrade"}
        response_headers = {k: v for k, v in resp.headers.items() if k.lower() not in excluded_headers}

        return StreamingResponse(
            resp.aiter_bytes(),
            status_code=resp.status_code,
            headers=response_headers,
            media_type=resp.headers.get("content-type")
        )
