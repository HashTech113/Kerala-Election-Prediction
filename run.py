import os
import signal
import socket
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))


def start_process(name, cmd, cwd=None, env=None):
    print(f"Starting {name}: {' '.join(cmd)}")
    return subprocess.Popen(cmd, cwd=cwd or ROOT, env=env, shell=True)


def _local_ipv4():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return None


def main():
    backend_host = os.getenv("HOST", "0.0.0.0")
    backend_port = os.getenv("PORT", "8001")
    frontend_host = os.getenv("FRONTEND_HOST", "0.0.0.0")
    frontend_port = os.getenv("FRONTEND_PORT", "5173")

    backend_env = os.environ.copy()
    backend_env.setdefault("HOST", backend_host)
    backend_env.setdefault("PORT", backend_port)

    backend_cmd = [sys.executable, os.path.join(ROOT, "backend", "server.py")]
    frontend_dir = os.path.join(ROOT, "frontend")
    frontend_cmd = ["npm", "run", "dev", "--", "--host", frontend_host, "--port", frontend_port]

    backend = start_process("backend", backend_cmd, env=backend_env)
    time.sleep(0.5)
    frontend = start_process("frontend", frontend_cmd, cwd=frontend_dir)

    local_ip = _local_ipv4()

    print("\nApp is live:")
    print(f"  Frontend (this machine): http://127.0.0.1:{frontend_port}")
    print(f"  Backend  (this machine): http://127.0.0.1:{backend_port}/api/predictions")
    if (
        local_ip
        and frontend_host in {"0.0.0.0", "::"}
        and backend_host in {"0.0.0.0", "::"}
    ):
        print(f"  Frontend (LAN):          http://{local_ip}:{frontend_port}")
        print(f"  Backend  (LAN):          http://{local_ip}:{backend_port}/api/predictions")
    print("\nPress Ctrl+C to stop both servers.\n")

    processes = [backend, frontend]

    def shutdown(*_):
        print("\nShutting down...")
        for proc in processes:
            if proc.poll() is None:
                proc.terminate()
        for proc in processes:
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while True:
        for proc in processes:
            if proc.poll() is not None:
                print(f"A server exited unexpectedly (code {proc.returncode}). Stopping all.")
                shutdown()
        time.sleep(0.5)


if __name__ == "__main__":
    main()
