# 🏗️ Project Architecture: Fed Django FOMC Tracker

This document provides a comprehensive overview of the project's architecture, deployment strategy, and critical fixes. It is designed to help any developer or AI agent understand the system without reverse engineering.

---

## 🌟 Project Overview
This is a Django-based application designed to track and analyze **Federal Open Market Committee (FOMC)** news. It features:
*   An automated **Scraper/Scheduler** that fetches real-time articles from the Event Registry API.
*   A **PostgreSQL database** with `pgvector` for future semantic search capabilities.
*   A **Dockerized environment** for consistent local development and production parity.

---

## 🛠️ Technology Stack
*   **Backend**: Django (Python 3.12)
*   **Database**: PostgreSQL 16 + `pgvector`
*   **Task Scheduling**: Custom Python scheduler loop (`scheduler.py`)
*   **Dependency Management**: `uv` (Fastest Python package manager)
*   **Web Server**: Gunicorn (Production) / Django Runserver (Development optional)
*   **Static Files**: WhiteNoise (Handles Gzip compression and serving)
*   **Deployment**: Docker & Docker Compose

---

## 🐳 Docker Infrastructure

### 1. Dual-Purpose Architecture
The same Docker image is used for both the **Web Service** and the **Scheduler Service**.
*   **Web Service**: Runs the Django WSGI application via Gunicorn.
*   **Scheduler Service**: Runs the `scheduler.py` script.
*   **Entrypoint Logic**: The `entrypoint.sh` script decides what to run based on the arguments passed (e.g., `./entrypoint.sh scheduler`).

### 2. Critical Docker Fixes
*   **Windows CRLF Trap**: Because the project is developed on Windows, `entrypoint.sh` often picks up `\r` line endings. The `Dockerfile` includes a `sed` command to scrub these, preventing `no such file or directory` errors.
*   **Database Readiness**: The `entrypoint.sh` includes a loop that pings the database port until it is active before starting Django. This prevents migration failures during startup.
*   **Layer Optimization**: We use the official `uv` image and copy `pyproject.toml`/`uv.lock` first to leverage Docker's build cache.

---

## 🚀 Deployment Strategy

### PaaS (Railway) Setup
The project is currently configured for **Railway**.
*   **Networking**: Internal communication uses `.railway.internal` hostnames.
*   **Static Files**: `collectstatic` runs once during the Web Service startup.
*   **Environment Variables**:
    *   `SECRET_KEY`: Production secret.
    *   `DEBUG`: Must be `False`.
    *   `DATABASE_URL` (or split `POSTGRES_` variables): Connection to managed DB.
    *   `ALLOWED_HOSTS`: Set to `.up.railway.app`.

### Environment Parity
The application uses `os.getenv` with sensible defaults. 
*   **Local**: Connects to `db:5432`.
*   **Production**: Connects to the host provided by the Cloud provider.

---

## 📝 Key Files & Their Purposes
*   `Dockerfile`: Builds the universal image.
*   `docker-compose.yml`: Orchestrates DB, Web, and Scheduler for local dev.
*   `entrypoint.sh`: The "Brain" of the container startup.
*   `scheduler.py`: The loop that triggers article fetching.
*   `news/services.py`: Contains the logic for Event Registry API calls and data saving.
*   `core/settings.py`: Hardened for production with WhiteNoise and Env-var security.

---

## 🛑 Common Troubleshooting
1.  **"No such file or directory" for entrypoint**: This is a line-ending issue. Run `docker-compose build --no-cache` to let the `sed` fix apply.
2.  **Scheduler Failed Fetch**: Usually means the `EVENTREGISTRY_API_KEY` is missing from the environment variables of that specific service.
3.  **Static Files not loading**: Ensure `DEBUG=False` in production so WhiteNoise takes over serving from the `staticfiles/` directory.

---

**Version**: v1.1.0 
**Author**: Antigravity AI & User
**Last Updated**: 2026-01-28
