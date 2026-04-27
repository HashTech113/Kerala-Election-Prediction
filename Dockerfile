# Kerala Election 2026 backend — minimal runtime image.
#
# The server (backend/main.py + services.py + schemas.py + routers/) only
# imports fastapi / uvicorn / pydantic + stdlib. The heavier deps in
# requirements.txt (torch, transformers, sklearn, pandas, numpy, tqdm) are only
# used by training/preprocessing scripts that never run on Railway, so they are
# intentionally not installed here.
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN pip install \
    "fastapi>=0.110.0,<0.120.0" \
    "uvicorn[standard]>=0.29.0,<0.40.0" \
    "pydantic>=2.6.0,<3.0.0"

# Backend source (Python + the CSVs the server reads). Everything else is
# excluded via .dockerignore.
COPY backend/ /app/backend/

# No EXPOSE: Railway auto-detects the listening port from $PORT at runtime.
# A static EXPOSE here would mislead Railway's edge router into using the
# wrong target port and produce "service unavailable" 503s on healthcheck.
# Locally, `docker run -p 8000:8000` still works because of the default below.

# Railway injects $PORT at runtime. Default to 8000 for local `docker run`.
CMD ["sh", "-c", "uvicorn main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]
