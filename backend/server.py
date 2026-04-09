import csv
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
PREDICTIONS_FILE = ROOT / "predictions_2026.csv"


class ElectionAPIHandler(BaseHTTPRequestHandler):
    server_version = "ElectionAPI/1.0"

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _load_predictions(self):
        if not PREDICTIONS_FILE.exists():
            raise FileNotFoundError(
                f"{PREDICTIONS_FILE} not found. Run train.py first to generate predictions_2026.csv"
            )

        rows = []
        with PREDICTIONS_FILE.open("r", encoding="utf-8", newline="") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                rows.append(
                    {
                        "constituency": row.get("constituency", ""),
                        "district": row.get("district", ""),
                        "predicted": row.get("predicted", ""),
                        "confidence": float(row.get("confidence", 0) or 0),
                        "LDF": float(row.get("LDF", 0) or 0),
                        "UDF": float(row.get("UDF", 0) or 0),
                        "NDA": float(row.get("NDA", 0) or 0),
                        "OTHERS": float(row.get("OTHERS", 0) or 0),
                    }
                )
        return rows

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/health":
            self._send_json({"status": "ok"})
            return

        if path == "/api/predictions":
            try:
                rows = self._load_predictions()
                self._send_json(rows)
            except FileNotFoundError as exc:
                self._send_json({"error": str(exc)}, status=404)
            except Exception as exc:
                self._send_json({"error": f"Unexpected server error: {exc}"}, status=500)
            return

        self._send_json(
            {
                "error": "Not found",
                "available_routes": ["/api/health", "/api/predictions"],
            },
            status=404,
        )


def main(host="127.0.0.1", port=8001):
    server = ThreadingHTTPServer((host, port), ElectionAPIHandler)
    print(f"Backend API running on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
