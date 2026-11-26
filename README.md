# Predator — Face Auth Backend

Passwordless facial biometric authentication API built with **FastAPI**, **InsightFace**, and **MongoDB**. Clients capture and send facial images; the backend handles face detection, embedding generation (`buffalo_l`), cosine-similarity verification, JWT cookie sessions, member invitations, and usage telemetry.

---

## Key Features

- **Passwordless Face Authentication**: Sign up and log in using facial biometrics powered by InsightFace (`buffalo_l` ONNX runtime).
- **JWT Cookie Sessions**: Access and refresh token management with configurable `SameSite`, `Secure`, and expiration policies.
- **Member Invitations (SMTP)**: Invite team members via email with time-limited tokens and customizable email templates stored in MongoDB.
- **Role & Member Management**: List, update, and manage enrolled members.
- **Telemetry & Dashboard Analytics**: Logs authentication attempts and exposes aggregated metrics for the admin dashboard.
- **Production-Ready Containerization**: Multi-stage `python:3.11-slim` + `uv` Dockerfile with non-root user, health checks, and persistent InsightFace model caching.

---

## Tech Stack

| Layer                       | Technology                                                                                  |
| :-------------------------- | :------------------------------------------------------------------------------------------ |
| **Framework**         | FastAPI (`>=0.110.0`), Uvicorn (`>=0.27.0`)                                             |
| **Biometric Engine**  | InsightFace (`>=0.7.3`), ONNX Runtime, OpenCV (`opencv-python-headless`), NumPy, Pillow |
| **Database**          | MongoDB 7 (`pymongo>=4.6.0`)                                                              |
| **Auth & Validation** | PyJWT (`>=2.8.0`), Pydantic (`>=2.6.0`), `email-validator`                            |
| **Containerization**  | Docker & Docker Compose                                                                     |

---

## Project Structure

```text
backend/
├── app/
│   ├── config.py              # Environment configuration loader (FaceAuthConfig)
│   ├── core/                  # Domain models, custom exceptions, error handlers, timezone utils
│   ├── db/                    # MongoDB client & index initialization
│   ├── middleware/            # Auth & client metadata middleware
│   ├── routers/               # FastAPI route handlers (auth, dashboard, members, settings)
│   ├── schemas/               # Pydantic request/response schemas
│   └── services/              # Business logic (auth, engine, matching, email, dashboard, repository)
├── scripts/
│   ├── seed_email_templates.py     # Seeds default email templates into MongoDB
│   └── migrate_email_templates.py  # Email template migration utility
├── tests/
│   └── test_auth_services.py  # Service unit tests
├── .env.example               # Environment variable template
├── Dockerfile                 # Multi-stage production Docker image
├── docker-compose.yml         # MongoDB + Backend service orchestration
├── main.py                    # FastAPI application entrypoint
└── requirements.txt           # Python dependencies
```

---

## Prerequisites

- **Python 3.11+** (recommended for prebuilt `insightface` wheels)
- **Docker & Docker Compose** (for MongoDB in dev, or full-stack containers in production)

---

## Quick Start (Local Development)

In development mode, **MongoDB runs in Docker** while the **FastAPI service runs in your terminal** for fast hot-reloading.

### 1. Configure Environment Variables

**macOS / Linux:**

```bash
cp .env.example .env
```

**Windows (PowerShell):**

```powershell
Copy-Item .env.example .env
```

Update `.env` with your JWT secrets and SMTP credentials if you plan to send invite emails.

### 2. Start MongoDB in Docker

```bash
docker compose up -d mongo
```

This starts the `predator-mongo` container (`mongo:7`) with persistent volume `mongo_data` and exposes port `27017:27017` for the local backend.

### 3. Create Virtual Environment & Install Dependencies

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Run the Development Server

**macOS / Linux:**

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8090
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8090
```

### 5. Verify

- **Health Check:** `GET http://localhost:8090/auth/health`
- **Interactive API Docs (Swagger):** `http://localhost:8090/docs`

*(Note: On first startup, InsightFace will automatically download the `buffalo_l` model pack to `~/.insightface/models`.)*

---

## Production Deployment (Docker)

To run both MongoDB and the Backend API inside Docker containers:

```bash
docker compose up -d --build
```

- `predator-backend` connects to `predator-mongo` over the internal `predator-net` bridge network (`FACE_AUTH_MONGO_URI=mongodb://mongo:27017`).
- InsightFace models are persisted in the `insightface_models` Docker volume.
- The API is exposed on port `8090` with a built-in `/auth/health` healthcheck.

---

## Environment Variables

| Variable                               | Default                                      | Description                                                 |
| :------------------------------------- | :------------------------------------------- | :---------------------------------------------------------- |
| `HOST`                               | `0.0.0.0`                                  | Server bind host                                            |
| `PORT`                               | `8090`                                     | Server listen port                                          |
| `FACE_AUTH_MODEL`                    | `buffalo_l`                                | InsightFace model pack name                                 |
| `FACE_AUTH_CTX_ID`                   | `-1`                                       | Execution context (`-1` for CPU, `0+` for CUDA GPU)     |
| `FACE_AUTH_MATCH_THRESHOLD`          | `0.40`                                     | Cosine similarity threshold for face verification           |
| `FACE_AUTH_MONGO_URI`                | `mongodb://localhost:27017`                | MongoDB connection URI                                      |
| `FACE_AUTH_MONGO_DB`                 | `predator`                                 | MongoDB database name                                       |
| `FACE_AUTH_USERS_COLLECTION`         | `users`                                    | Collection for user profiles & face embeddings              |
| `FACE_AUTH_INVITES_COLLECTION`       | `invites`                                  | Collection for member invitations                           |
| `FACE_AUTH_USAGE_LOGS_COLLECTION`    | `usage_logs`                               | Collection for authentication logs                          |
| `FACE_AUTH_APP_SETTINGS_COLLECTION`  | `app_settings`                             | Collection for email templates & app settings               |
| `FACE_AUTH_SECRET_KEY`               | —                                           | Access token signing secret (use 32+ random chars in prod)  |
| `FACE_AUTH_REFRESH_SECRET_KEY`       | —                                           | Refresh token signing secret (use 32+ random chars in prod) |
| `FACE_AUTH_JWT_ALGORITHM`            | `HS256`                                    | JWT signing algorithm                                       |
| `FACE_AUTH_ACCESS_TOKEN_EXPIRE_MIN`  | `60`                                       | Access token lifetime in minutes                            |
| `FACE_AUTH_REFRESH_TOKEN_EXPIRE_HRS` | `24`                                       | Refresh token lifetime in hours                             |
| `FACE_AUTH_COOKIE_SAMESITE`          | `lax`                                      | Cookie `SameSite` policy                                  |
| `FACE_AUTH_COOKIE_SECURE`            | `false`                                    | Set `true` behind HTTPS in production                     |
| `FACE_AUTH_SMTP_SERVER`              | `smtp.gmail.com`                           | SMTP server hostname                                        |
| `FACE_AUTH_SMTP_PORT`                | `587`                                      | SMTP TLS port                                               |
| `FACE_AUTH_SMTP_USERNAME`            | —                                           | SMTP username                                               |
| `FACE_AUTH_SMTP_PASSWORD`            | —                                           | SMTP password / app password                                |
| `FACE_AUTH_FROM_EMAIL`               | —                                           | Sender email address                                        |
| `FACE_AUTH_FROM_ALIAS`               | `PREDATOR Security`                        | Sender display name                                         |
| `FACE_AUTH_INVITE_LINK_BASE`         | `http://localhost:3000/auth/accept-invite` | Base URL for invitation links                               |
| `FACE_AUTH_INVITE_TTL_HOURS`         | `48`                                       | Invitation expiration in hours                              |

---

## API Endpoints Overview

### Authentication (`/auth`)

- `POST /auth/signup` — Enroll a new user with facial capture
- `POST /auth/face-login` — Authenticate an existing user via face image
- `POST /auth/invite` — Send an email invitation to a new member
- `POST /auth/accept-invite` — Complete registration via invite token & face capture
- `POST /auth/logout` — Clear session cookies
- `GET /auth/me` — Get current authenticated user
- `GET /auth/health` — Service health check

### Dashboard (`/dashboard`)

- `GET /dashboard/cards` — Aggregated authentication & user summary metrics
- `GET /dashboard/usage-logs` — Recent authentication telemetry logs

### Members (`/members`)

- `GET /members` — List enrolled members
- `PUT / PATCH /members/{user_id}` — Update member details/status

### Settings (`/settings`)

- `GET /settings/email-templates` — Retrieve email templates
- `PUT /settings/email-templates/{template_id}` — Update an email template
- `POST /settings/email-templates/reset` — Reset templates to defaults
- `POST /settings/email-templates/preview` — Render an email template preview

---

## Scripts & Testing

- **Seed Default Email Templates:**
  ```bash
  python scripts/seed_email_templates.py
  ```
- **Run Unit Tests:**
  ```bash
  python -m unittest discover -s tests
  ```
