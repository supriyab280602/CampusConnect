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

The following describes the approved product scope. Feature availability depends on implementation progress.

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

The structure represents the planned implementation layout and may evolve as development progresses.

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

Tests must be added as implementation progresses.

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

**Development status:** In planning and specification phase.

The approved documentation baseline currently defines the product requirements, design, architecture, database model, API contract, and agent instructions.

Implementation status must be updated as actual features are completed and tested. Planned functionality must not be represented as already implemented.

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