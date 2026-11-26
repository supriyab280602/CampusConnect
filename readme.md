# CampusConnect

### Your people. Your ideas. Your next opportunity.

A student-focused social and professional networking platform designed to connect university students, encourage technical discussions, and make academic networking easier.

---

## Overview

CampusConnect is a student networking platform that combines social interaction with professional identity and academic discovery.

Students can create profiles, connect with peers, share technical ideas, discover other students, and explore their academic network.

Unlike a conventional social platform, CampusConnect is designed around meaningful student connections and demonstrates core Data Structures and Algorithms through its implementation.

## Problem Statement

University students often struggle to discover peers with similar interests, build meaningful academic connections, and stay informed about the technical activities happening within their student community.

CampusConnect aims to provide a unified platform where students can:

- Build an academic and professional identity.
- Discover students with shared interests.
- Establish and manage connections.
- Share technical ideas and project updates.
- Explore relationships within their student network.

## Key Features

The following describes the approved product scope implemented in the platform.

### 1. Student Accounts
- Account registration and login.
- Secure password handling.
- Session-based authentication.

### 2. Student Profiles
- Personal and academic information.
- Programme and academic year.
- Bio and skills.
- Profile viewing and editing.

### 3. Connections
- Send connection requests.
- Accept or reject incoming requests.
- View sent and received requests.
- Manage accepted connections.

### 4. Student Feed
- Create text-based posts.
- View posts from accepted connections.
- Retrieve posts in chronological order.
- Delete own posts.

### 5. Student Discovery
- Search students by name or username.
- Prefix-based suggestions.
- Discover potential connections.

### 6. Network Exploration
- View mutual connections.
- Calculate direct connection degree.
- Find shortest connection paths.
- Generate potential connection recommendations.

---

## Data Structures and Algorithms

DSA is a central part of CampusConnect, not an additional decorative feature.

| Data Structure / Algorithm | Application |
|---|---|
| Graph using adjacency list | Represent accepted student connections |
| Breadth-First Search | Graph traversal and shortest paths |
| Trie | Prefix-based student search |
| Heap / Priority Queue | Merge chronologically ordered post streams |
| Recommendation algorithm | Identify potential connections |

### Graph Representation

Accepted connections are represented as an undirected graph.

```text
Student A ----- Student B
     |
     |
Student C
```

Pending connection requests remain directed records and are not added to the accepted-connection graph.

### BFS

Breadth-First Search is used for shortest-path calculations in an unweighted connection graph.

Time complexity:

`O(V + E)`

### Trie

A custom Trie supports prefix-based student lookup.

It allows the application to find matching usernames and display names without scanning every user record for each prefix query.

### Heap-Based Feed Merging

The feed engine merges multiple time-ordered post streams using a heap.

For P emitted posts from k ordered streams, the typical merge complexity is:

`O(P log k)`

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React |
| Build Tool | Vite |
| Backend | Python Flask |
| Database | SQLite |
| API | REST / JSON |
| Graph | Python adjacency list |
| Search | Custom Trie |
| Traversal | BFS |
| Feed merging | Heap / Priority Queue |

## Architecture

CampusConnect follows a modular monolithic architecture.

```text
                 React + Vite
                      |
                   REST API
                      |
                  Flask App
                      |
              Application Services
                      |
          +-----------+-----------+
          |           |           |
       DSA Core   Repositories  Auth
          |           |           |
          +-----------+-----------+
                      |
                    SQLite
```

The DSA core is a separate logical module inside the backend. Graph and Trie structures are reconstructed from persisted database records when the backend starts.

## Project Structure

```text
CampusConnect/
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── dsa/
│   │   ├── repositories/
│   │   ├── database/
│   │   └── utils/
│   ├── tests/
│   ├── run.py
│   └── requirements.txt
│
├── docs/
│
└── README.md
```

The structure represents the implemented application architecture.

---

## Getting Started

### Prerequisites

Install the following:

- Python 3.10 or later.
- Node.js and npm.
- Git.

The exact supported Python version should be confirmed against the backend dependencies before implementation is finalized.

### 1. Clone the repository

```bash
git clone <repository-url>
cd CampusConnect
```

### 2. Backend setup

Navigate to the backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the required environment variables using the backend configuration instructions.

Start the backend:

```bash
python run.py
```

### 3. Frontend setup

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open the local URL printed by Vite in your browser.

### 4. Database

SQLite is used for persistent storage.

The backend initializes the schema and reconstructs its graph and Trie indexes during startup.

Do not delete the database file to reset the application once real project data has been stored.

---

## Testing

Run backend tests from the backend directory:

```bash
pytest
```

Run frontend checks using the scripts configured in `package.json`.

Important testing areas:

- Account registration and authentication.
- Profile creation and updates.
- Connection request lifecycle.
- Accepted graph-edge invariants.
- BFS shortest paths.
- Trie prefix search.
- Heap-based feed ordering.
- Database transaction behavior.
- Persistence after backend restart.
- API validation and authorization.

Comprehensive automated test suites cover all core functionality and DSA invariants.

---

## Security

CampusConnect follows these baseline security practices:

- Password hashing.
- Server-managed sessions.
- Backend authorization checks.
- CSRF protection for session-authenticated state changes.
- Parameterized SQL queries.
- Input validation.
- Environment-based secret configuration.

Never commit credentials, secret keys, or real user data.

---

## Academic Context

CampusConnect is developed as a Data Structures and Algorithms mini-project.

Its implementation emphasizes practical applications of graph structures, BFS, Trie-based searching, and priority queues within a student networking platform.

The system is designed to demonstrate how data structures support real application functionality rather than existing only as isolated algorithm exercises.

---

## Project Status

**Development status:** Implementation Complete & Release Verified.

All core product requirements, the Academic Salon responsive user interface across all five views, custom in-memory DSA algorithms (Graph, BFS, Trie, Min-Heap), and SQLite persistence have been fully implemented, integrated, and verified through comprehensive end-to-end QA regression testing.

## Future Enhancements

Potential extensions, subject to project scope and evaluation priorities:

- Richer post interactions.
- Image-based posts.
- Notifications.
- Community groups.
- Additional discovery capabilities.

These are not part of the mandatory initial implementation baseline.

---

## License

License selection and repository publication terms are to be decided before public distribution.

---

## Production Deployment (Vercel Frontend + Render Free Backend)

CampusConnect uses a split hosting architecture:

- **Frontend:** Vercel (React + Vite static build)
- **Backend:** Render Free Web Service (Python + Flask + Gunicorn)
- **Database:** SQLite (`/tmp/campusconnect.db` on Render Free)
- **CI:** GitHub Actions (`.github/workflows/ci.yml`)

### 1. Vercel Frontend Setup

Configure a Vercel project connected to `https://github.com/supriyab280602/CampusConnect` (`main` branch):

- **Root Directory:** `frontend`
- **Framework Preset:** `Vite`
- **Install Command:** `npm ci`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **SPA Routing:** Configured in `frontend/vercel.json` (`/(.*) -> /index.html`, preserving `?tab=` query parameters).
- **Environment Variable (Production & Preview):**
  - `VITE_API_BASE_URL=https://campusconnect-backend-9o12.onrender.com/api/v1`

### 2. Render Backend Setup (Free Tier)

Configured in `render.yaml` (`campusconnect-backend`):

- **Root Directory:** `backend`
- **Runtime:** `python`
- **Plan:** `free` (no paid Persistent Disk)
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn -w 1 --threads 4 --bind 0.0.0.0:$PORT "app:create_app()"`
  - Must run with **1 worker (`-w 1`)** because `DSAManager` (`UndirectedGraph` and `PrefixTrie`) is process-local in memory.
- **Health Check Path:** `/api/v1/health`
- **Required Environment Variables:**
  - `FLASK_ENV=production`
  - `FLASK_DEBUG=0`
  - `SECRET_KEY` — cryptographically random string (at least 32 characters)
  - `DATABASE_PATH=/tmp/campusconnect.db`
  - `CORS_ORIGINS` — exact Vercel production origin (`https://campconct.vercel.app`, no `*` wildcard)

### 3. SQLite & Ephemeral Storage Limitation on Render Free

On Render's Free tier, persistent disks are not available. `DATABASE_PATH=/tmp/campusconnect.db` uses the container's writable ephemeral filesystem (`backend/app/db/connection.py` safely ensures parent directories exist and initializes the schema and in-memory DSA indices on startup).

> **Important:** Data stored in SQLite on Render Free is **temporary** and will be reset whenever the service spins down due to inactivity, restarts, or redeploys. For persistent production data, upgrade the backend service to a paid Render plan with a Persistent Disk mounted at `/var/data` (`DATABASE_PATH=/var/data/campusconnect.db`).

### 4. CORS & Authentication

- `CORS_ORIGINS` is set in the Render Dashboard and `render.yaml` to `https://campconct.vercel.app,https://campusconnect-frontend-bzwf.onrender.com`.
- Never use wildcard `*` with `supports_credentials=True`.
- Cross-origin deployments preserve `SameSite=None; Secure; HttpOnly` cookies, `X-Session-Token` / `Authorization: Bearer` fallback, `X-Requested-With: XMLHttpRequest` CSRF protection, and auth rate limiting.

### 5. Deployment Sequence & Live Verification

1. Deploy the `frontend` project on Vercel at `https://campconct.vercel.app`.
2. In the Render Dashboard for `campusconnect-backend`, set `CORS_ORIGINS=https://campconct.vercel.app` (or comma-separated with previous frontend) and `DATABASE_PATH=/tmp/campusconnect.db`, then deploy.
3. Verify `GET https://campusconnect-backend-9o12.onrender.com/api/v1/health` returns `HTTP 200` (`status: "healthy"`).
4. Verify `OPTIONS` preflight with `Origin: https://campconct.vercel.app` returns `Access-Control-Allow-Origin: https://campconct.vercel.app`.
5. Open `https://campconct.vercel.app` in a browser and verify registration, login, reload persistence, profile update, post creation/deletion, Trie search, connection requests, graph recommendations/BFS, and logout with zero console/5xx errors.

## Documentation

Refer to the project documentation for detailed specifications:

- `PRD.md` — Product requirements.
- `design.md` — UI/UX and design system.
- `architecture.md` — System architecture.
- `database.md` — Database specification.
- `api.md` — API contract.
- `agents.md` — Development and AI-agent instructions.

---

**CampusConnect — Building meaningful connections, one student at a time.**