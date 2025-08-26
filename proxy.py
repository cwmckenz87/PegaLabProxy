from fastapi import FastAPI, Request, Response
import httpx

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

    # Read the incoming body
    body_bytes = await request.body()

    # Copy headers, remove Host to avoid conflicts
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

    # Return the response fully buffered, with all headers
    response_headers = dict(resp.headers)
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=response_headers
    )
