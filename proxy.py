from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse
import httpx

app = FastAPI()

BACKEND_HOSTNAME = "ey57.pegalabs.io"

# ---------------------------
# Healthcheck endpoint
# ---------------------------
@app.get("/healthcheck")
async def healthcheck():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"https://{BACKEND_HOSTNAME}")
            return {"status": r.status_code, "reachable": r.status_code == 200}
    except Exception as e:
        return {"error": str(e), "reachable": False}

# ---------------------------
# "What is my IP" endpoint
# ---------------------------
@app.get("/myip")
async def my_ip():
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://ifconfig.me/ip")
            return {"public_ip": r.text.strip()}
    except Exception as e:
        return {"error": str(e)}

# ---------------------------
# Proxy endpoint
# ---------------------------
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(path: str, request: Request):
    url = f"https://{BACKEND_HOSTNAME}/{path}"

    # Preserve headers, except Host (let httpx handle Host automatically)
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}

    async with httpx.AsyncClient(timeout=30.0, verify=True) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                params=request.query_params,
                content=await request.body()
            )
        except httpx.ConnectTimeout:
            return JSONResponse({"error": "ConnectTimeout — cannot reach backend"}, status_code=504)
        except httpx.HTTPError as e:
            return JSONResponse({"error": f"HTTP error: {e}"}, status_code=502)

    return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))
