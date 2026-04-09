import os
import signal
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))


def start_process(name, cmd, cwd=None):
    print(f"Starting {name}: {' '.join(cmd)}")
    return subprocess.Popen(cmd, cwd=cwd or ROOT, shell=True)


def main():
    backend_cmd = [sys.executable, os.path.join(ROOT, "backend", "server.py")]
    frontend_dir = os.path.join(ROOT, "frontend")
    frontend_cmd = ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"]

    backend = start_process("backend", backend_cmd)
    time.sleep(0.5)
    frontend = start_process("frontend", frontend_cmd, cwd=frontend_dir)

    print("\nApp is live:")
    print("  Frontend : http://127.0.0.1:5173")
    print("  Backend  : http://127.0.0.1:8001/api/predictions")
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
