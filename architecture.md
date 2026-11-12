# CampusConnect — System Architecture

**Document ID:** CC-ARC-003  
**Version:** 1.1  
**Status:** APPROVED & FROZEN  
**Governing Documents:** PRD.md v1.0, design.md v1.1  
**Architecture Style:** Modular Monolith with an Independent DSA Core

---

## 1. Purpose

This document defines the technical architecture of CampusConnect, including system boundaries, components, data flows, persistence, DSA responsibilities, and implementation decisions.

CampusConnect combines social networking, academic identity, professional profiles, and graph-based student discovery.

The architecture prioritizes:

- Clear separation between frontend, backend, DSA core, and persistence.
- Correct implementation and demonstration of data structures.
- Reliable persistence across application restarts.
- Explainable code suitable for individual academic evaluation.
- A manageable implementation scope without unnecessary infrastructure.

## 2. Requirements and Decision Classification

This document distinguishes three types of statements:

| Classification | Meaning |
|---|---|
| Assignment requirement | Explicitly derived from the academic assignment |
| Product requirement | Defined in the approved PRD or design specification |
| Architecture decision | Engineering choice proposed to implement the requirements |

Technology choices such as Flask, React, and SQLite are architecture decisions, not automatically assignment mandates.

## 3. Architecture Goals and Principles

1. Separate presentation, application logic, DSA, and persistence.
2. Execute graph operations in Python using in-memory structures.
3. Keep SQLite as the durable source of truth.
4. Reconstruct derived data structures from persisted records.
5. Keep business logic outside HTTP route handlers.
6. Make algorithms independently testable.
7. Avoid unnecessary external infrastructure.
8. Keep implementation understandable for the project demonstration and viva.

## 4. System Architecture

### 4.1 Architecture diagram

```text
                 CAMPUSCONNECT
                       |
                 React + Vite
                   Frontend
                       |
                  REST / JSON
                       |
                  Flask API
                       |
               Application Services
                       |
          +------------+------------+
          |            |            |
       DSA Core    Repositories   Auth
          |            |            |
          +------------+------------+
                       |
                    SQLite
                Persistent Data
```

The DSA core is a logical module inside the Flask backend. It is not a separate service or process.

### 4.2 Architectural layers

| Layer | Responsibility |
|---|---|
| Presentation | Screens, navigation, interactions |
| API | HTTP routing and request/response handling |
| Service | Business rules and operation orchestration |
| DSA Core | Graph, BFS, Trie, heap |
| Repository | Database operations |
| Persistence | Durable records in SQLite |

## 5. Technology Stack

| Component | Selected technology | Purpose |
|---|---|---|
| Frontend | React | User interface |
| Build tool | Vite | Frontend development |
| Backend | Python Flask | REST API |
| Database | SQLite | Persistent storage |
| Communication | HTTP + JSON | Frontend/backend boundary |
| DSA | Custom Python implementations | Required algorithmic operations |
| Authentication | Server-managed sessions | User authentication |

These are the selected implementation choices for the project baseline.

## 6. Project Structure

### 6.1 Frontend

```text
frontend/
└── src/
    ├── app/
    │   ├── App.jsx
    │   └── routes.jsx
    ├── components/
    │   ├── navigation/
    │   ├── feed/
    │   ├── profile/
    │   ├── connections/
    │   ├── search/
    │   └── common/
    ├── pages/
    │   ├── Home.jsx
    │   ├── Discover.jsx
    │   ├── Connections.jsx
    │   ├── Requests.jsx
    │   └── Profile.jsx
    ├── services/
    │   └── api.js
    ├── hooks/
    ├── context/
    ├── styles/
    └── main.jsx
```

Responsibilities:

- Render the approved CampusConnect interface.
- Handle navigation and responsive layouts.
- Collect user input.
- Display profiles, feed posts, search results, and network information.
- Communicate with Flask through the API service.
- Display loading, empty, error, and success states.

The frontend must not be responsible for authoritative graph calculations or authorization decisions.

### 6.2 Backend

```text
backend/
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── connections.py
│   │   ├── posts.py
│   │   ├── search.py
│   │   └── feed.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── connection_service.py
│   │   ├── post_service.py
│   │   ├── search_service.py
│   │   └── feed_service.py
│   ├── dsa/
│   │   ├── graph.py
│   │   ├── bfs.py
│   │   ├── trie.py
│   │   ├── heap.py
│   │   └── recommendations.py
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── connection_repository.py
│   │   ├── request_repository.py
│   │   └── post_repository.py
│   ├── database/
│   │   ├── connection.py
│   │   └── schema.sql
│   ├── utils/
│   └── config.py
├── tests/
├── run.py
└── requirements.txt
```

This structure defines logical responsibilities. Implementation may introduce additional files without changing those boundaries.

## 7. Component Responsibilities

### 7.1 API routes

Routes receive HTTP requests, perform request-level checks, invoke services, and return responses.

They must not contain complex business logic or DSA implementations.

### 7.2 Services

| Service | Responsibility |
|---|---|
| Auth | Registration, login, logout |
| User | Profile creation, retrieval, updates |
| Connection | Sending, accepting, rejecting, removing connections |
| Post | Creating, retrieving, deleting posts |
| Search | Search orchestration and Trie queries |
| Feed | Building the connection feed |

### 7.3 Repositories

Repositories isolate database access from business logic.

They are responsible for SQL operations, record mapping, and transaction participation.

### 7.4 DSA core

| Module | Structure / Algorithm | Responsibility |
|---|---|---|
| graph.py | Adjacency list | Accepted connection representation |
| bfs.py | Breadth-First Search | Traversal and shortest paths |
| trie.py | Trie | Prefix-based student lookup |
| heap.py | Heap / priority queue | Merging ordered post streams |
| recommendations.py | Recommendation logic | Candidate connection generation |

The DSA core must not import Flask request objects or execute SQL directly.

## 8. Connection Graph Architecture

### 8.1 Accepted connections

Accepted connections form an undirected graph.

```text
A -------- B
```

Adjacency representation:

```python
{
    "A": ["B"],
    "B": ["A"]
}
```

Every accepted edge must appear in both adjacency lists.

### 8.2 Pending requests

Pending requests are directed records.

```text
A --------> B
```

They must remain outside the accepted-connection graph until acceptance.

### 8.3 Graph invariants

- No self-connections.
- No duplicate accepted edges.
- Accepted edges are bidirectional.
- Pending requests are not graph edges.
- Removing a connection removes both adjacency entries.
- Vertices represent valid user identifiers.

### 8.4 Degree and shortest-path semantics

These are distinct operations and must not be confused.

**Degree:** The number of immediate accepted connections of a user.

For vertex \(v\):

\[
degree(v)=|Adj(v)|
\]

This can be retrieved directly from the adjacency list in \(O(1)\) average time, assuming constant-time dictionary access.

**Shortest-path distance:** The minimum number of accepted-connection edges between two users.

BFS calculates shortest paths in an unweighted graph.

\[
O(V+E)
\]

where V is the number of vertices and E is the number of edges.

If no path exists, the operation must return an explicit no-path result rather than an arbitrary distance.

## 9. Trie-Based Search

The search engine uses a custom Trie to support prefix-based student lookup.

### 9.1 Search behavior

Example:

```text
Prefix: "san"

Possible results:
- sanjay
- sanjana
- santhosh
```

### 9.2 Normalization rules

The search index will use a consistent normalization process:

1. Normalize Unicode text.
2. Apply case folding for case-insensitive matching.
3. Trim leading and trailing whitespace.
4. Apply the same transformation during insertion and lookup.

Usernames remain unique according to the database constraint.

Display names are not necessarily unique. Therefore, a Trie terminal must support multiple matching user identifiers rather than assuming one display name corresponds to one user.

### 9.3 Search responsibilities

The Trie stores searchable keys and references to user IDs.

The user repository retrieves current profile details for the matched IDs.

The Trie is an index, not the authoritative profile database.

## 10. Feed Architecture

The feed contains posts from accepted connections, according to the approved product requirements.

The feed must not include posts from users who are not accepted connections.

### 10.1 Heap-based merging

The proposed implementation merges multiple time-ordered post streams using a heap.

Workflow:

1. Identify the authenticated user.
2. Retrieve their accepted connections.
3. Obtain ordered post streams for those connections.
4. Insert the newest available item from each stream into the heap.
5. Extract the newest item.
6. Insert the next item from that item's stream.
7. Repeat until the page limit is reached or streams are exhausted.

Posts are ordered by:

1. Creation timestamp, newest first.
2. Post ID as a deterministic tie-breaker.

If P posts are emitted from k streams, the merge has typical complexity:

\[
O(P\log k)
\]

This assumes each input stream is already ordered and only the required number of posts is processed.

### 10.2 Pagination

The initial implementation should use cursor-based pagination rather than relying exclusively on large offset queries.

The cursor must represent the last returned ordering position, using timestamp and post ID.

The backend must apply the same deterministic ordering when retrieving subsequent pages.

A cursor does not create a full historical snapshot. New posts created while a user is paging may affect later results. The implementation must document this behavior and avoid duplicate posts across pages under the selected cursor rules.

## 11. Persistence Architecture

### 11.1 Source of truth

SQLite is the durable source of truth.

The following structures are derived in-memory indexes:

- Accepted-connection graph.
- Student-search Trie.

Feed ordering is calculated from persisted post records and does not require a permanent in-memory feed cache.

### 11.2 Startup reconstruction

At startup:

1. Open the SQLite database.
2. Verify the schema.
3. Load valid user identifiers.
4. Load accepted connections.
5. Construct the adjacency-list graph.
6. Load searchable user fields.
7. Construct the Trie.
8. Validate index invariants.
9. Mark the application ready to serve dependent requests.

If reconstruction fails, the backend must fail readiness and report the error. It must not silently serve incomplete graph or search results.

### 11.3 Mutation consistency strategy

SQLite is authoritative. In-memory structures are derived state.

The mutation workflow is:

1. Validate the operation.
2. Validate business rules.
3. Acquire the application-level mutation lock.
4. Begin a database transaction.
5. Perform persistent changes.
6. Commit the transaction.
7. Apply the corresponding in-memory update.
8. Release the lock.
9. Return success.

If the database transaction fails, roll back and leave the in-memory structures unchanged.

If the database commit succeeds but the in-memory update fails:

- Do not report the operation as fully successful.
- Mark the affected index unavailable.
- Block dependent reads and writes that require that index.
- Rebuild the affected index from SQLite.
- Restore readiness only after validation succeeds.

This recovery approach prevents the application from knowingly serving stale graph or Trie data.

For the initial single-process architecture, a process-level mutation lock is sufficient to serialize index-changing operations. SQLite transactions still protect persistent data.

**Multi-process deployment is not supported by this in-memory synchronization model.**

### 11.4 Operation mapping

| Operation | SQLite mutation | Derived-state action |
|---|---|---|
| Register user | Insert user | Insert Trie entries |
| Accept request | Update request and persist accepted connection | Add undirected graph edge |
| Remove connection | Delete accepted relationship | Remove both graph directions |
| Update searchable profile fields | Update user | Update or rebuild Trie entries |
| Create post | Insert post | No mandatory graph update |
| Delete post | Delete post | Subsequent feed reads reflect deletion |

Database transactions must cover all related persistent changes in a multi-record operation.

## 12. Authentication and Session Management

**Selected approach: Server-managed sessions.**

This is appropriate for the initial React + Flask application because it avoids unnecessary token lifecycle complexity.

The backend will:

- Authenticate credentials.
- Create and invalidate sessions.
- Store session identifiers in secure cookies.
- Enforce authentication on protected routes.
- Verify ownership and authorization on sensitive operations.

Cookie settings should include:

- HttpOnly.
- SameSite protection.
- Secure in production over HTTPS.

CSRF protection must be implemented for state-changing requests when cookie-based sessions are used.

The frontend must not treat a locally stored user ID as proof of authentication.

Passwords must be hashed using an established password-hashing implementation. Plaintext passwords must never be stored.

## 13. API Boundary

The frontend communicates with Flask through JSON-based REST endpoints.

The backend owns:

- Input validation.
- Authentication.
- Authorization.
- Business rules.
- DSA execution.
- Database access.
- Response formatting.

The frontend owns presentation and user interaction.

Endpoint paths, request schemas, response schemas, and HTTP status codes belong in **api.md**.

## 14. Error Handling

| Category | Example | Expected behavior |
|---|---|---|
| Validation | Invalid username | Client error |
| Authentication | Invalid credentials | Reject authentication |
| Authorization | Unauthorized post deletion | Forbidden response |
| Not found | Missing profile | Not-found response |
| Conflict | Duplicate request | Conflict or existing-state response |
| Persistence | Failed database transaction | Rollback |
| DSA | Invalid graph operation | Controlled domain error |
| Index consistency | Failed in-memory update | Mark index unavailable and rebuild |
| Internal | Unexpected exception | Log internally and return generic error |

Sensitive internal details must not be exposed to users.

## 15. Security

Minimum requirements:

- Password hashing.
- Server-side input validation.
- Parameterized SQL queries.
- Backend authorization checks.
- Secure session configuration.
- CSRF protection for cookie-authenticated state changes.
- Controlled CORS configuration.
- Secrets stored outside source control.
- Safe error responses.
- No reliance on frontend-only validation.

## 16. Configuration

Configuration must be separated from application code.

| Configuration | Purpose |
|---|---|
| Database path | SQLite file location |
| Environment | Development or production |
| Secret key | Session signing |
| Frontend origin | CORS and API configuration |
| Debug mode | Development-only debugging |

Actual secret values must never be committed to the repository.

## 17. Testing Architecture

### DSA unit tests

- Graph insertion and deletion.
- Undirected-edge invariants.
- Degree calculation.
- BFS shortest paths.
- Unreachable vertices.
- Trie insertion and prefix lookup.
- Duplicate display-name matches.
- Trie updates and rebuilding.
- Heap ordering.
- Feed tie-breaking and merging.

### Service tests

- Registration and authentication.
- Connection request lifecycle.
- Graph synchronization.
- Post ownership.
- Feed membership.
- Feed ordering and pagination.
- Search result resolution.

### Repository tests

- Record insertion and retrieval.
- Database constraints.
- Transaction rollback.
- Multi-record transaction behavior.
- Persistence after restart.

### Integration tests

Verify the complete frontend/backend/database workflow.

A mandatory architecture-level test must:

1. Create users.
2. Create and accept a connection.
3. Stop the backend.
4. Restart the backend.
5. Verify that the accepted connection exists in the reconstructed graph.
6. Verify that Trie search still returns the expected users.

## 18. Deployment and Runtime

Initial runtime:

```text
React + Vite
     |
     | HTTP / JSON
     v
Flask Backend
     |
     +---- DSA Core
     |
     +---- SQLite
```

The initial architecture assumes one backend process.

The SQLite database must be stored in a persistent location and excluded from accidental source-control commits when it contains real user data.

Production deployment must account for:

- Persistent database storage.
- Database backups.
- HTTPS.
- Session security.
- Environment configuration.

SQLite is suitable for the expected academic workload. It is not intended to provide large-scale concurrent-write performance.

## 19. Logging and Observability

Record:

- Application startup and shutdown.
- Database initialization failures.
- Unexpected exceptions.
- Authentication failures without credentials.
- DSA operation failures.
- Index reconstruction failures.
- Application readiness transitions.

Never log passwords, session tokens, or unnecessary personal data.

Structured application logging is sufficient for the initial scope.

## 20. Scalability and Limitations

Known limitations:

1. Graph and Trie memory usage increases with users and connections.
2. Startup reconstruction takes time proportional to the records being indexed.
3. SQLite may become a write bottleneck under heavy concurrency.
4. Multiple backend processes cannot safely share independent in-memory indexes without additional synchronization architecture.
5. Feed performance depends on the number of connection streams and posts retrieved.
6. Trie prefix queries can produce large result sets for broad prefixes.

These limitations are acceptable for the initial project scope.

No distributed cache, microservices, or external graph infrastructure will be introduced without a demonstrated requirement.

## 21. Architecture Decisions Register

| Decision | Final position |
|---|---|
| Frontend | React + Vite |
| Backend | Flask |
| Database | SQLite |
| Architecture | Modular monolith |
| DSA engine | Separate logical Python module |
| Graph | In-memory adjacency list |
| Graph traversal | BFS |
| Search | Custom Trie |
| Feed merge | Heap / priority queue |
| Authentication | Server-managed sessions |
| Persistence authority | SQLite |
| Derived indexes | Graph and Trie |
| Index recovery | Rebuild from SQLite |
| Runtime | Single backend process |
| Recommendation algorithm | Open pending evaluation |
| Database access library | To be selected during implementation |

### Recommendation algorithm decision criteria

The recommendation implementation must be selected after evaluating:

- Assignment expectations.
- Available graph data.
- Algorithm correctness.
- Computational complexity.
- Explainability during viva.
- Meaningfulness of generated recommendations.

Jaccard similarity and Katz centrality remain candidates. Neither is declared final in this version.

## 22. Requirements Traceability

| Requirement | Responsible component |
|---|---|
| Account registration and login | Auth service |
| Student profiles | User service and repository |
| Connection requests | Connection service and request repository |
| Accepted connections | Connection service and graph |
| Posts | Post service and repository |
| Connection feed | Feed service and heap |
| Prefix search | Trie and search service |
| Shortest connection paths | Graph and BFS |
| Recommendations | Recommendation module |
| Persistence | SQLite repositories |
| Core engine separate from UI | Flask backend and DSA module |

## 23. Architecture Acceptance Criteria

- [ ] Frontend and backend responsibilities are separated.
- [ ] DSA implementations are independent of HTTP and SQL concerns.
- [ ] Accepted connections are represented as undirected edges.
- [ ] Pending requests remain separate directed records.
- [ ] Graph and Trie can be reconstructed from SQLite.
- [ ] Failed database transactions do not modify derived indexes.
- [ ] Failed in-memory updates trigger controlled recovery.
- [ ] BFS, Trie, and heap implementations have independent tests.
- [ ] Session authentication and authorization are enforced server-side.
- [ ] Feed ordering is deterministic.
- [ ] Feed pagination uses a defined cursor.
- [ ] The architecture supports the frozen PRD and design specification.
- [ ] The implementation remains explainable for academic evaluation.

---

## Document Control

**Document:** architecture.md  
**Document ID:** CC-ARC-003  
**Version:** 1.1  
**Status:** APPROVED & FROZEN  
**Supersedes:** architecture.md v1.0  
**Governing baseline:** PRD.md v1.0 and design.md v1.1

Any future architectural change must be recorded as a new version. Changes to this document must not silently alter the requirements or design decisions in the frozen governing documents.