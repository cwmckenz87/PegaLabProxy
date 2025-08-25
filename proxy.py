from fastapi import FastAPI, Request
from fastapi.responses import Response
import httpx
import socket

app = FastAPI()

BACKEND_URL = "https://ey57.pegalabs.io"

# Custom HTTPX transport forcing IPv4
class IPv4Resolver(httpx.AsyncHTTPTransport):
    async def handle_async_request(self, request):
        # Resolve hostname to IPv4 only
        host = request.url.host
        port = request.url.port or 443

        # Get IPv4 addresses
        addrs = socket.getaddrinfo(host, port, family=socket.AF_INET, type=socket.SOCK_STREAM)
        ip = addrs[0][4][0]  # take the first IPv4

        # Replace the URL host with the IPv4 address
        url = request.url.copy_with(host=ip)
        # Set Host header so backend sees correct hostname
        request.headers["Host"] = host

        async with httpx.AsyncClient(transport=httpx.AsyncHTTPTransport()) as client:
            resp = await client.request(
                request.method,
                url,
                headers=request.headers,
                params=request.url.params,
                content=request.content,
                timeout=30.0
            )
        return resp

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(path: str, request: Request):
    async with IPv4Resolver() as client:
        resp = await client.handle_async_request(
            httpx.Request(
                method=request.method,
                url=f"{BACKEND_URL}/{path}",
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                content=await request.body()
            )
        )
    return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))
