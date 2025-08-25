from fastapi import FastAPI
import socket

app = FastAPI()
BACKEND_HOSTNAME = "ey57.pegalabs.io"

@app.get("/healthcheck")
async def healthcheck():
    try:
        addrs = socket.getaddrinfo(BACKEND_HOSTNAME, 443, socket.AF_INET, socket.SOCK_STREAM)
        ipv4_list = [a[4][0] for a in addrs]

        results = []
        for ip in ipv4_list:
            try:
                s = socket.create_connection((ip, 443), timeout=5)
                s.close()
                results.append({"ip": ip, "reachable": True})
            except Exception:
                results.append({"ip": ip, "reachable": False})

        return {"hostname": BACKEND_HOSTNAME, "results": results}

    except Exception as e:
        return {"error": str(e)}
