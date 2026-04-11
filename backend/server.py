import csv
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
PREDICTIONS_FILE = ROOT / "predictions_2026.csv"
ASSEMBLY_FALLBACK_FILE = ROOT / "data_files" / "kerala_assembly_2026.csv"


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _load_rows_from_predictions_file():
    rows = []
    with PREDICTIONS_FILE.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            rows.append(
                {
                    "constituency": row.get("constituency", ""),
                    "district": row.get("district", ""),
                    "predicted": row.get("predicted", ""),
                    "confidence": _to_float(row.get("confidence", 0)),
                    "LDF": _to_float(row.get("LDF", 0)),
                    "UDF": _to_float(row.get("UDF", 0)),
                    "NDA": _to_float(row.get("NDA", 0)),
                    "OTHERS": _to_float(row.get("OTHERS", 0)),
                }
            )
    return rows


def _load_rows_from_assembly_fallback():
    if not ASSEMBLY_FALLBACK_FILE.exists():
        raise FileNotFoundError(
            f"Neither {PREDICTIONS_FILE.name} nor {ASSEMBLY_FALLBACK_FILE} was found. "
            "Run create_dataset.py and train.py before starting the server."
        )

    rows = []
    with ASSEMBLY_FALLBACK_FILE.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            shares = {
                "LDF": _to_float(row.get("proj_2026_ldf_pct", 0)),
                "UDF": _to_float(row.get("proj_2026_udf_pct", 0)),
                "NDA": _to_float(row.get("proj_2026_nda_pct", 0)),
                "OTHERS": _to_float(row.get("proj_2026_others_pct", 0)),
            }
            sorted_shares = sorted(shares.values(), reverse=True)
            confidence = sorted_shares[0] - sorted_shares[1] if len(sorted_shares) > 1 else 0.0

            predicted = row.get("proj_2026_winner", "")
            if predicted not in shares:
                predicted = max(shares, key=shares.get)

            rows.append(
                {
                    "constituency": row.get("constituency", ""),
                    "district": row.get("district", ""),
                    "predicted": predicted,
                    "confidence": confidence,
                    "LDF": shares["LDF"],
                    "UDF": shares["UDF"],
                    "NDA": shares["NDA"],
                    "OTHERS": shares["OTHERS"],
                }
            )
    return rows


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
        if PREDICTIONS_FILE.exists():
            return _load_rows_from_predictions_file()
        return _load_rows_from_assembly_fallback()

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


def main(host=None, port=None):
    bind_host = host if host is not None else os.getenv("HOST", "0.0.0.0")
    bind_port = int(port) if port is not None else int(os.getenv("PORT", "8001"))
    server = ThreadingHTTPServer((bind_host, bind_port), ElectionAPIHandler)
    print(f"Backend API running on http://{bind_host}:{bind_port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
