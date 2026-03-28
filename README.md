# ☕ ecspresso

![ecspresso Logo](ecspreso.png)

**ecspresso** is a DevOps tool designed to centralize and automate the management of environment variables, secrets (AWS SSM), and container *Task Definition* templates for deployments on Amazon ECS (Elastic Container Service).

It allows Development and DevOps teams to manage configurations for multiple applications and environments (`development`, `staging`, `production`) through a robust API and an interactive, visually stunning Command-Line Interface (CLI).

---

## 🚀 Key Features

- **Centralized Management:** Define all your base ECS JSON container templates in one place.
- **Variables & Secrets Merging:** Automatically injects environment variables and secret references (from AWS Systems Manager Parameter Store).
- **Rich CLI Tool:** Built with `click` and `rich` to provide syntax-highlighted and colored console outputs directly in your terminal.
- **Dual Authentication:**
  - Web UI protected by **JWT** and Password Hashing (`bcrypt`).
  - API protected by **API Key** (perfect for automated use in CI/CD pipelines and by the CLI).
- **Production Ready:**
  - Containerized App (unprivileged `Dockerfile`).
  - Dedicated Health Check endpoint (`/health`).
  - Easily deployable locally with `docker-compose`.
  - Clean Database Abstraction Layer (Repository / CRUD Pattern).

---

## 🛠️ Technology Stack

- **Backend:** FastAPI, Uvicorn
- **Database:** PostgreSQL, SQLAlchemy (ORM)
- **Security:** PyJWT, Bcrypt
- **CLI:** Click, Rich, Requests
- **Infrastructure:** Docker, Docker Compose

---

## 🏃‍♂️ Installation & Quick Start

### 1. Environment & AWS Configuration (SSM)
This project uses a `.env` file to manage secrets, Database credentials, and AWS configurations securely (preventing them from leaking into the repository).

Copy the example file to create your local environment:
```bash
cp .env.example .env
```
Then edit `.env` by adding your real AWS credentials (so `boto3` can interact with the Parameter Store) and altering passwords if necessary.

### 2. Spin Up Local Infrastructure

Clone the repository and bring up both the PostgreSQL database and the API using Docker Compose. Using `--build` ensures your image is built from scratch securely without root privileges.

```bash
sudo docker compose up -d --build
```

The FastAPI backend will now be exposed at `http://localhost:8000`.

### 3. Populate Database (Seed)
To log in locally or inspect pre-loaded data, run the main seed script against the container.

```bash
sudo docker exec -it ecspresso-api-1 python seed.py
```
*(This sets up the `admin` user with the password `admin`)*

**Mock Data (Optional Test):**
If you want to load fake data for testing (like a `payment-service` template with local mock secrets instead of hitting real AWS infrastructure), add the `--mock` flag:

```bash
sudo docker exec -it ecspresso-api-1 python seed.py --mock
```

---

## 💻 Usage in CI/CD & Local CLI (API Key Auth)

Both your local command-line interface and your CI/CD pipelines (such as **GitHub Actions** or **Jenkins**) interact with `ecspresso` via **API Key** authentication. This prevents managing sessions or JWT Token expirations in automated environments.

### 1. Generating a new Pipeline API Key

The API Key travels as plain text from the client (your CLI or pipeline), but on the server database (`docker-compose.yml` or `.env` file) it is kept securely as a `bcrypt` hash.

If you wish to create your own secure key (e.g. `my-super-secret-key`), you must first generate its hash using Python on your terminal:

```bash
python -c 'import bcrypt; print(bcrypt.hashpw(b"my-super-secret-key", bcrypt.gensalt()).decode().replace("$", "$$"))'
```

Copy the output hash (starting with `$$2b$$...`) and configure the `API_KEY_HASH` variable in your `.env` file. Then, restart your docker containers.

### 2. Pipeline / Local CLI Setup

Once the backend is aware of the secure hash, configure your pipeline (or local terminal session) by injecting the raw text key via environment variables:

```bash
export ECSPRESSO_API_KEY="my-super-secret-key"
export ECSPRESSO_URL="http://localhost:8000" # Optional, defaults to this
```
*(In GitHub Actions, you would save `my-super-secret-key` as a GitHub Secret and map it into the job's `env:` block).*

### 3. CLI Commands

Once authenticated, use your terminal to manage your ecosystem:

#### Get a Task Definition
Generates the final ECS JSON with variables mapped, outputting it with rich syntax highlights suitable for piping.

```bash
python cli.py td get --app payment-service --env development
```
*To save the output into a file, append the `--output td.json` or `-o td.json` flag.*

#### Set an Environment Variable
Automatically creates the application (if it doesn't exist) and registers the variable on the fly:

```bash
python cli.py set-var --app my-app --env development --key DB_HOST --value localhost
```

#### Set a Remote Secret (AWS SSM)
Creates an AWS Systems Manager Parameter Store secret and returns the ARN:

```bash
python cli.py set-secret --app my-app --env development --key STRIPE_API_KEY --value sk_test_1234
```

---

## 🔗 Main API Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/` | Returns the static HTML dashboard | - |
| `GET` | `/health` | Health Check (verifies DB connection) | - |
| `POST`| `/api/v1/auth/login` | Grants JWT Token for frontend | Basic HTTP |
| `GET` | `/api/v1/apps/{app}/td` | Generates merged ECS JSON | *JWT* or *API Key* |

---

## 🔐 Design & Security Notes

- The `Dockerfile` has been crafted using production-grade security standards, removing root flags and operating under an isolated `appuser`.
- All passwords and pipeline tokens are encrypted using standard 1-way hashing algorithms (`bcrypt`). 

---
*Built to improve developer experience in modern DevOps Ecosystems.*
