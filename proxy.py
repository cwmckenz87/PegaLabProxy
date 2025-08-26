from fastapi import FastAPI, Request, Response
import httpx

app = FastAPI()

TARGET_URL = "https://ey57.pegalabs.io/oauth/token"  # OAuth token endpoint

@app.post("/proxy/token")
async def proxy_token(request: Request):
    # Read the incoming body
    body_bytes = await request.body()

    # Copy headers, removing host to avoid conflicts
    headers = dict(request.headers)
    headers.pop("host", None)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TARGET_URL,
            content=body_bytes,
            headers=headers,
            timeout=30.0
        )

    # Forward response headers exactly
    response_headers = dict(resp.headers)

    # Return the response fully buffered
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=response_headers,
        media_type=resp.headers.get("content-type")
    )
