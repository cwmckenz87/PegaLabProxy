from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse, StreamingResponse
import httpx
import os

app = FastAPI()

# Backend hostname to proxy to
BACKEND_HOSTNAME = os.environ.get("BACKEND_HOSTNAME", "ey57.pegalabs.io")

# === Healthcheck ===
@app.get("/health")
async def health():
    return {"status": "ok"}

# === Public IP endpoint ===
@app.get("/myip")
async def myip():
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get("https://ifconfig.me/ip")
            public_ip = resp.text.strip()
        except Exception as e:
            return JSONResponse({"error": f"Cannot determine IP: {e}"}, status_code=500)
    return {"public_ip": public_ip}

# === Passthrough proxy ===
from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse, JSONResponse
import httpx
import os

app = FastAPI()

BACKEND_HOSTNAME = os.environ.get("BACKEND_HOSTNAME", "ey57.pegalabs.io")

# --- Healthcheck ---
@app.get("/health")
async def health():
    return {"status": "ok"}

# --- My IP endpoint ---
@app.get("/myip")
async def myip():
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get("https://ifconfig.me/ip")
            return {"public_ip": resp.text.strip()}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

# --- Passthrough proxy ---
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy(path: str, request: Request):
    url = f"https://{BACKEND_HOSTNAME}/{path}"

    # Copy headers except hop-by-hop headers
    excluded_headers = {"host", "connection", "keep-alive", "transfer-encoding", "upgrade"}
    headers = {k: v for k, v in request.headers.items() if k.lower() not in excluded_headers}

    async with httpx.AsyncClient(timeout=30.0, verify=True) as client:
        try:
            async with client.stream(
                method=request.method,
                url=url,
                headers=headers,
                params=request.query_params,
                content=await request.body()
            ) as resp:

                response_headers = {
                    k: v for k, v in resp.headers.items() if k.lower() not in excluded_headers
                }

                # Stream only if Transfer-Encoding: chunked
                if resp.headers.get("transfer-encoding") == "chunked":
                    async def generator():
                        async for chunk in resp.aiter_bytes():
                            if chunk:
                                yield chunk
                    return StreamingResponse(
                        generator(),
                        status_code=resp.status_code,
                        headers=response_headers,
                        media_type=resp.headers.get("content-type")
                    )
                else:
                    body = await resp.aread()
                    return Response(
                        content=body,
                        status_code=resp.status_code,
                        headers=response_headers,
                        media_type=resp.headers.get("content-type")
                    )

        except httpx.ConnectTimeout:
            return JSONResponse({"error": "ConnectTimeout — cannot reach backend"}, status_code=504)
        except httpx.HTTPError as e:
            return JSONResponse({"error": f"HTTP error: {e}"}, status_code=502)

