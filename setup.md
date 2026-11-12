# CampusConnect — Development Setup Guide

**Document ID:** CC-SET-009  
**Version:** 1.0  
**Status:** Draft — Awaiting Approval  
**Project:** CampusConnect  
**Governing Documents:** PRD.md v1.0, design.md v1.1, architecture.md v1.1, database.md v1.1, api.md v1.0, agents.md v1.0, readme.md v1.0, plan.md v1.0

---

## 1. Purpose

This guide explains how to prepare a local development environment for CampusConnect.

It covers:

- Required software.
- Repository setup.
- Backend configuration.
- Frontend configuration.
- Database initialization.
- Application startup.
- Verification.
- Common setup issues.

This is a development setup guide. Production deployment configuration is outside its scope.

## 2. Prerequisites

Install the following software before beginning.

| Software | Purpose | Version |
|---|---|---|
| Python | Backend development | 3.10+ proposed; verify dependencies |
| Node.js | Frontend runtime | Current supported LTS |
| npm | Frontend package management | Bundled with Node.js |
| Git | Version control | Current stable |
| VS Code | Recommended editor | Current stable |

**Version note:** The exact Python and Node.js versions must be verified against the final dependency files. The versions above are initial setup guidance, not a tested compatibility guarantee.

## 3. Verify Installations

Open a terminal and execute:

```bash
python --version
```

```bash
node --version
```

```bash
npm --version
```

```bash
git --version
```

If a command is not recognized, install the corresponding software and reopen the terminal.

## 4. Clone the Repository

```bash
git clone <repository-url>
```

Navigate into the project:

```bash
cd CampusConnect
```

Expected structure:

```text
CampusConnect/
├── frontend/
├── backend/
├── docs/
└── README.md
```

The actual repository structure should be checked against the implemented project before following the remaining steps.

## 5. Backend Setup

### 5.1 Navigate to backend

```bash
cd backend
```

### 5.2 Create a virtual environment

Windows:

```bash
python -m venv venv
```

Activate:

```bash
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
```

Activate:

```bash
source venv/bin/activate
```

### 5.3 Install dependencies

```bash
pip install -r requirements.txt
```

If dependency installation fails, verify the Python version and inspect the error before installing packages individually.

### 5.4 Configure environment variables

Create a local `.env` file if the implementation uses environment-based configuration.

Example:

```env
FLASK_ENV=development
SECRET_KEY=replace-with-a-local-secret
DATABASE_PATH=instance/campusconnect.db
FRONTEND_ORIGIN=http://localhost:5173
```

These names are proposed configuration examples. The final variable names must match `config.py`.

Security rules:

- Never commit the actual `.env` file.
- Provide a `.env.example` containing placeholder values.
- Generate a strong local secret.
- Never reuse production secrets in development.

### 5.5 Database initialization

The backend must initialize the SQLite schema using its configured initialization or migration process.

Expected database location:

```text
backend/
└── instance/
    └── campusconnect.db
```

The exact location depends on the final database configuration.

Verify:
- Database file is created.
- Foreign-key enforcement is enabled.
- Schema version is valid.
- Required tables and indexes exist.
- Graph and Trie reconstruction completes successfully.

Do not manually create tables if the backend already provides schema initialization.

### 5.6 Start the backend

Use the configured entry point:

```bash
python run.py
```

The expected development API origin is:

```text
http://localhost:5000
```

This is a proposed local address. Confirm the actual host and port from the Flask configuration.

## 6. Frontend Setup

Open a separate terminal.

### 6.1 Navigate to frontend

```bash
cd CampusConnect/frontend
```

### 6.2 Install packages

```bash
npm install
```

### 6.3 Configure API origin

If the frontend uses Vite environment variables, create a local `.env` file.

Example:

```env
VITE_API_BASE_URL=http://localhost:5000/api/v1
```

The variable name must match the frontend API service implementation.

Do not hardcode production API addresses inside components.

### 6.4 Start the frontend

```bash
npm run dev
```

Vite will display the development URL in the terminal.

Open that URL in the browser.

The typical default is:

```text
http://localhost:5173
```

The actual port may differ if the default is unavailable.

## 7. Running the Complete Application

The frontend and backend run as separate development processes.

**Terminal 1 — Backend**

```bash
cd CampusConnect/backend
```

Activate the virtual environment, then:

```bash
python run.py
```

**Terminal 2 — Frontend**

```bash
cd CampusConnect/frontend
```

Then:

```bash
npm run dev
```

Both processes must remain running while using the application.

## 8. Initial Verification

After startup, verify the following.

### Backend

- [ ] Flask starts without import errors.
- [ ] SQLite opens successfully.
- [ ] Schema initialization succeeds.
- [ ] Graph reconstruction succeeds.
- [ ] Trie reconstruction succeeds.
- [ ] Authentication routes respond.
- [ ] Backend logs contain no unresolved startup errors.

### Frontend

- [ ] Vite starts successfully.
- [ ] Browser loads the application.
- [ ] No critical console errors appear.
- [ ] API requests reach Flask.
- [ ] CORS and session-cookie behavior work.
- [ ] The UI displays backend errors appropriately.

### End-to-end smoke test

1. Register a development account.
2. Log in.
3. View the profile.
4. Update profile information.
5. Create a second development account.
6. Send a connection request.
7. Accept the request.
8. Verify the accepted relationship.
9. Create a post.
10. Verify feed retrieval.
11. Search using a username prefix.
12. Restart the backend.
13. Verify persisted records and reconstructed indexes.

Use development accounts and non-sensitive test data only.

## 9. Database Reset for Development

Database resets are destructive.

Before resetting:

1. Stop the backend.
2. Confirm that the database contains only disposable development data.
3. Back up the database if needed.
4. Use the project's approved reset or migration process.
5. Restart the backend.
6. Verify schema and index reconstruction.

Never delete the database to apply a schema change. Use migrations.

## 10. Git and Local Configuration

Recommended `.gitignore` entries:

```gitignore
# Python
__pycache__/
*.py[cod]
venv/
.env

# SQLite
*.db
*.sqlite
*.sqlite3

# Node
node_modules/
dist/

# Editor
.vscode/

# Logs
*.log
```

If the repository intentionally tracks a database fixture, adjust the ignore rules accordingly.

Never commit:
- Real user records.
- Session data.
- Passwords.
- Secret keys.
- Local environment files.

## 11. Common Setup Problems

| Problem | Likely cause | Resolution |
|---|---|---|
| `python` not recognized | Python missing from PATH | Install Python and configure PATH |
| `npm` not recognized | Node.js missing or PATH issue | Install Node.js and reopen terminal |
| Dependency installation fails | Incompatible runtime or package | Check version and package error |
| Flask import error | Missing dependencies or wrong environment | Activate virtual environment and reinstall |
| SQLite database locked | Concurrent access or unclosed transaction | Inspect connections and transaction handling |
| Frontend cannot reach API | Incorrect API origin | Verify Vite environment configuration |
| CORS error | Incorrect backend origin configuration | Configure allowed frontend origin |
| Session not retained | Cookie or credential configuration issue | Check credentials, SameSite, Secure, and CORS settings |
| Graph results incorrect after restart | Reconstruction or persistence defect | Inspect accepted-connection records and rebuild logic |
| Search suggestions missing | Trie initialization or normalization mismatch | Inspect index construction and search normalization |

## 12. Development Rules

- Run frontend and backend in separate terminals.
- Keep the virtual environment activated during backend work.
- Restart the backend after configuration changes.
- Do not commit local secrets.
- Do not modify frozen database or API contracts without versioned approval.
- Run relevant tests after changes.
- Keep development data separate from real data.
- Verify startup reconstruction after database-related changes.

## 13. Setup Acceptance Criteria

- [ ] Required software is installed.
- [ ] Repository clones successfully.
- [ ] Backend virtual environment works.
- [ ] Backend dependencies install.
- [ ] Environment configuration is valid.
- [ ] SQLite initializes successfully.
- [ ] Graph and Trie reconstruct successfully.
- [ ] Frontend dependencies install.
- [ ] Frontend starts successfully.
- [ ] Frontend communicates with backend.
- [ ] Session authentication works.
- [ ] Basic end-to-end smoke test passes.

---

## Document Control

**Document ID:** CC-SET-009  
**Version:** 1.0  
**Status:** DRAFT — AWAITING APPROVAL  
**Governing baseline:** PRD.md v1.0, design.md v1.1, architecture.md v1.1, database.md v1.1, api.md v1.0, agents.md v1.0, readme.md v1.0, plan.md v1.0

**Implementation note:** Commands, environment variable names, ports, and runtime versions must be verified against the actual repository configuration before this guide is treated as a tested installation procedure.