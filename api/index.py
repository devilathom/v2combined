from http.server import BaseHTTPRequestHandler
import json
import requests
import re
import base64
from concurrent.futures import ThreadPoolExecutor

def _r(encoded):
    return base64.b64decode(encoded).decode()

RC_URL = _r(
    "aHR0cHM6Ly9iYWNrZW5kLnZhaGFuZGV0YWlscy5jb20vYXBpL2dldC1yYy1kZXRhaWxz"
)

CHALLAN_URL = _r(
    "aHR0cHM6Ly9iYWNrZW5kLnZhaGFuZGV0YWlscy5jb20vYXBpL2dldC1jaGFsbGFucy1kZXRhaWxz"
)

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "x-api-key": "Test_1234",
    "Origin": "https://vahandetails.com",
    "Referer": "https://vahandetails.com/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/148.0.0.0 Safari/537.36"
    )
}

def valid_rc(rc):
    return bool(
        re.match(
            r"^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$",
            rc
        )
    )

def fetch_rc(rc):
    try:
        r = requests.post(
            RC_URL,
            headers=HEADERS,
            json={"rc_number": rc},
            timeout=20
        )
        return r.json()
    except Exception as e:
        return {
            "status": False,
            "error": str(e)
        }

def fetch_challan(rc):
    try:
        r = requests.post(
            CHALLAN_URL,
            headers=HEADERS,
            json={"rc_number": rc},
            timeout=20
        )
        return r.json()
    except Exception as e:
        return {
            "status": False,
            "error": str(e)
        }

class handler(BaseHTTPRequestHandler):

    def do_GET(self):

        try:

            if "?number=" not in self.path:
                self.send_response(400)
                self.send_header(
                    "Content-Type",
                    "application/json"
                )
                self.end_headers()

                self.wfile.write(
                    json.dumps({
                        "status": False,
                        "message": "Vehicle number required"
                    }).encode()
                )
                return

            rc = self.path.split("?number=")[1]
            rc = rc.upper().replace(" ", "").replace("-", "")

            if not valid_rc(rc):
                self.send_response(400)
                self.send_header(
                    "Content-Type",
                    "application/json"
                )
                self.end_headers()

                self.wfile.write(
                    json.dumps({
                        "status": False,
                        "message": "Invalid RC format"
                    }).encode()
                )
                return

            with ThreadPoolExecutor(max_workers=2) as executor:

                rc_future = executor.submit(
                    fetch_rc,
                    rc
                )

                challan_future = executor.submit(
                    fetch_challan,
                    rc
                )

                rc_data = rc_future.result()
                challan_data = challan_future.result()

            result = {
                "status": True,
                "vehicle_number": rc,
                "rc_details": rc_data,
                "challan_details": challan_data
            }

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json"
            )
            self.send_header(
                "Access-Control-Allow-Origin",
                "*"
            )
            self.end_headers()

            self.wfile.write(
                json.dumps(result).encode()
            )

        except Exception as e:

            self.send_response(500)
            self.send_header(
                "Content-Type",
                "application/json"
            )
            self.end_headers()

            self.wfile.write(
                json.dumps({
                    "status": False,
                    "error": str(e)
                }).encode()
            )
