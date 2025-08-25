from fastapi import FastAPI
import socket

app = FastAPI()
BACKEND_HOSTNAME = "ey57.pegalabs.io"

@app.get("/healthcheck")
async def healthcheck():
    """
    Resolve all IPv4 addresses for the backend hostname and return them.
    """
    try:
        # Resolve IPv4 addresses only
        addrs = socket.getaddrinfo(BACKEND_HOSTNAME, 443, socket.AF_INET, socket.SOCK_STREAM)
        ipv4_list = [a[4][0] for a in addrs]
        return {
            "hostname": BACKEND_HOSTNAME,
            "ipv4_addresses": ipv4_list,
            "count": len(ipv4_list)
        }
    except Exception as e:
        return {"error": str(e)}

# Optional root route
@app.get("/")
async def root():
    return {"message": "Proxy healthcheck service running. Use /healthcheck to test connectivity."}
