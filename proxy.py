from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import httpx
import gzip
import zlib

app = FastAPI()

TARGET_HOST = "https://ey57.pegalabs.io"  # base URL of target system


@app.get("/myip")
async def my_ip(request: Request):
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get("https://ifconfig.me/ip")
            return {"public_ip": resp.text.strip()}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy(full_path: str, request: Request):
    target_url = f"{TARGET_HOST}/{full_path}"
    if request.query_params:
        target_url += f"?{request.query_params}"

    body_bytes = await request.body()
    headers = dict(request.headers)
    headers.pop("host", None)

    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method=request.method,
            url=target_url,
            content=body_bytes,
            headers=headers,
            timeout=30.0
        )

    # Start with the upstream content
    content = resp.content

    # Decompress if encoded
    encoding = resp.headers.get("content-encoding", "").lower()
    if encoding == "gzip":
        content = gzip.decompress(content)
    elif encoding == "deflate":
        content = zlib.decompress(content)

    # Copy headers but fix for decompression
    response_headers = dict(resp.headers)

    # Remove headers that no longer apply
    response_headers.pop("content-encoding", None)
    response_headers.pop("transfer-encoding", None)

    # Recalculate Content-Length
    response_headers["content-length"] = str(len(content))

    return Response(
        content=content,
        status_code=resp.status_code,
        headers=response_headers,
        media_type=resp.headers.get("content-type")
    )
