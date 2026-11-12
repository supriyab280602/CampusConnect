# CampusConnect — Integration Specification

**Document:** integrations.md  
**Version:** 1.0  
**Status:** Draft — Awaiting Approval

---

## 1. Purpose

Defines how CampusConnect's frontend, backend, database, authentication, and DSA components interact.

## 2. Integration Principles

- Keep the frontend independent of internal DSA implementation.
- Keep graph calculations inside the backend.
- Treat SQLite as the authoritative source of truth.
- Use explicit API contracts between frontend and backend.
- Keep derived in-memory indexes consistent with persisted data.
- Avoid unnecessary external services.

## 3. Component Boundaries

### Frontend

Technology: React + Vite.

Responsibilities:
- Render pages and reusable UI components.
- Collect user input.
- Display API results.
- Manage client-side interface state.
- Send REST requests.
- Handle loading, validation, empty, and error states.

The frontend must not independently calculate authoritative graph results.

### Backend

Technology: Python + Flask.

Responsibilities:
- Authentication and authorization.
- Request validation.
- Application services.
- REST API responses.
- Database transactions.
- Coordination of DSA operations.
- Rebuilding and maintaining derived indexes.

### Database

Technology: SQLite.

Responsibilities:
- Persist users, sessions, connection requests, accepted connections, and posts.
- Enforce applicable constraints.
- Provide transactional writes.

SQLite is the source of truth, not the in-memory graph or Trie.

### DSA Core

Responsibilities:
- Adjacency-list graph.
- BFS traversal.
- Mutual-connection calculation.
- Degree and shortest-path calculation.
- Trie prefix search.
- Heap-based feed merge.
- Recommendation algorithm after selection.

DSA modules should not directly own HTTP concerns or browser state.

## 4. Data Flow

Typical request flow:

1. User performs an action in the frontend.
2. Frontend sends an HTTP request to the Flask API.
3. Backend validates session and authorization.
4. Application service validates business rules.
5. Database is read or updated as required.
6. DSA modules are invoked for graph/search/feed operations.
7. Backend serializes the result.
8. Frontend renders the response.

## 5. Database and In-Memory Index Synchronization

SQLite is authoritative.

On startup:
- Load accepted connections.
- Rebuild adjacency-list graph.
- Load searchable user identity data.
- Rebuild Trie.
- Verify index initialization before readiness.

On mutations:
- Commit the database transaction first.
- Apply corresponding in-memory index updates.
- If index update fails, mark the dependent service unavailable.
- Rebuild the affected index from SQLite before serving dependent requests.

The approved architecture assumes a single backend process.

## 6. Frontend and Backend Integration

Frontend API configuration must use one central API base URL.

Requirements:
- Use JSON request/response contracts.
- Handle HTTP status codes consistently.
- Include credentials when using cookie-based sessions.
- Include CSRF tokens for protected state-changing requests.
- Avoid hardcoding API URLs across components.
- Keep API calls in a dedicated client/service layer.

## 7. CORS and Session Integration

During local development:
- Frontend and backend may run on different local origins.
- Backend must explicitly allow the configured frontend origin.
- Credentialed requests must be enabled where needed.
- Wildcard origins must not be used with credentialed requests.

Production must use a deliberate HTTPS and cookie configuration.

## 8. External Integrations

No external integrations are required in the current baseline.

Not included:
- OAuth providers
- Third-party social networks
- External graph databases
- Cloud storage
- AI model APIs
- MCP services
- Redis
- External notification services

Any addition requires a documented use case and approval through change control.

## 9. Integration Failure Handling

The system must handle:
- Backend unavailable
- Database unavailable
- Session expired
- CSRF validation failure
- Invalid API response
- Graph or Trie initialization failure
- Database transaction failure
- Frontend network failure

Failures must not silently produce misleading graph or feed results.

## 10. Integration Acceptance Criteria

- Frontend can communicate with backend through the documented API.
- Authentication survives page navigation within the configured session lifetime.
- CSRF protection works for state-changing requests.
- SQLite writes are reflected in application behavior.
- Graph and Trie indexes reflect persisted state.
- Restart reconstructs indexes correctly.
- Backend errors are represented safely in the frontend.

---

**End of Document — integrations.md v1.0**