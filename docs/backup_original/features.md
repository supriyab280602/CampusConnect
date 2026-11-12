# CampusConnect — Feature Specification

**Document:** features.md  
**Version:** 1.0  
**Status:** Draft — Awaiting Approval  
**Project:** CampusConnect  
**Baseline:** PRD v1.0, Design v1.1, Architecture v1.1, Database v1.1, API v1.0

---

## 1. Purpose

This document defines the functional feature inventory, expected user behavior, priorities, and acceptance criteria for CampusConnect.

It translates the approved PRD into implementation-oriented feature specifications. It does not introduce additional mandatory scope.

## 2. Priority Definitions

- **P0 — Mandatory:** Required for the assignment's core functionality and evaluation.
- **P1 — Supporting:** Important for a complete and usable experience.
- **P2 — Optional:** Enhancement that must not delay mandatory functionality.

## 3. Feature Inventory

| ID | Feature | Priority |
|---|---|---|
| F01 | User registration | P0 |
| F02 | Login and logout | P0 |
| F03 | User profile management | P0 |
| F04 | View user profiles | P0 |
| F05 | Send connection request | P0 |
| F06 | Accept/reject/cancel requests | P0 |
| F07 | Accepted connections graph | P0 |
| F08 | Mutual connections | P0 |
| F09 | Network degree and shortest path | P0 |
| F10 | Create and delete own posts | P0 |
| F11 | Connection-based feed | P0 |
| F12 | Username/name search | P0 |
| F13 | Prefix suggestions using Trie | P0 |
| F14 | Persistent storage | P0 |
| F15 | Discover and recommendation experience | P1 |
| F16 | Responsive interface | P1 |
| F17 | Optional engagement features | P2 |

## 4. Functional Specifications

### F01 — Registration

A visitor can create an account using the required registration fields.

Expected behavior:
- Validate required fields.
- Enforce unique normalized username and email.
- Hash passwords before persistence.
- Reject invalid or duplicate registration attempts.
- Create a persistent user record.

Acceptance criteria:
- Valid registration creates exactly one account.
- Duplicate normalized usernames and emails are rejected.
- Plaintext passwords are never stored.
- Invalid input receives a useful validation response.

### F02 — Authentication

A registered user can log in and log out.

Expected behavior:
- Verify credentials against stored password hashes.
- Establish a server-managed session.
- Reject unauthenticated access to protected operations.
- Invalidate the session on logout.

Acceptance criteria:
- Correct credentials establish an authenticated session.
- Incorrect credentials do not establish a session.
- Logout invalidates the active session.
- Session behavior follows the approved auth and API specifications.

### F03 — Profile Management

Users can view and update their own profile.

Profile information includes:
- Full display name
- Username
- Programme
- Academic year
- Bio
- Skills

Acceptance criteria:
- Users can update permitted profile fields.
- Username uniqueness is maintained.
- Profile changes persist after restart.
- Users cannot modify another user's profile through ordinary profile operations.

### F04 — Profile Viewing

Users can view another user's public CampusConnect profile.

Acceptance criteria:
- Profile information is returned for valid users.
- Missing users produce a not-found response.
- Sensitive authentication information is never exposed.

### F05–F06 — Connection Requests

Users can send and manage connection requests.

Rules:
- Users cannot send requests to themselves.
- Duplicate requests are prohibited.
- Reverse pending requests are prohibited.
- A pending request may be accepted, rejected, or cancelled by the authorized actor.
- Accepted connections are undirected.

Acceptance criteria:
- Valid requests persist.
- Invalid transitions are rejected.
- Accepted connections appear in both users' graph adjacency lists.
- Rejected and cancelled requests do not create graph edges.

### F07 — Connection Graph

The backend maintains an adjacency-list representation of accepted connections.

Acceptance criteria:
- Each accepted connection is represented for both users.
- No self-edges exist.
- No duplicate neighbors exist.
- The in-memory graph is rebuilt from SQLite during startup.

### F08 — Mutual Connections

The system identifies common connections between two users.

Acceptance criteria:
- Results contain only users connected to both queried users.
- Duplicate results are impossible.
- Results reflect the current accepted-connection graph.

### F09 — Degree and Shortest Path

The system provides:
- Degree: immediate accepted-connection count.
- Shortest path: minimum number of connection edges between two users.

BFS is used for shortest-path calculation.

Acceptance criteria:
- Degree matches the adjacency-list neighbor count.
- Same-user path distance is zero.
- Unreachable users return a clearly defined no-path result.
- Path distance is measured in edges, not number of displayed vertices.

### F10 — Posts

Users can create and delete their own text posts.

Acceptance criteria:
- Valid posts persist.
- Empty or invalid posts are rejected.
- Users can delete only their own posts.
- Deleted posts no longer appear in subsequent feed responses.

### F11 — Connection Feed

The feed contains posts from the authenticated user and accepted connections.

Expected behavior:
- Newest posts appear first.
- Timestamp ties use a deterministic post-ID tie-breaker.
- Multiple ordered streams are merged using a heap.
- Cursor pagination prevents reliance on unstable page offsets.

Acceptance criteria:
- Posts from unrelated users are excluded.
- Feed ordering is deterministic.
- Pagination does not duplicate records under an unchanged dataset.
- The feed remains correct after application restart.

### F12–F13 — Search and Prefix Suggestions

Users can search by username or display name.

Expected behavior:
- A custom Trie supports prefix search.
- Search normalization follows the architecture specification.
- Duplicate display names may return multiple users.
- Search results expose only permitted profile information.

Acceptance criteria:
- Matching prefixes return relevant users.
- Case differences do not cause inconsistent matches.
- Multiple users with identical display names are supported.
- Trie data can be rebuilt from SQLite.

### F14 — Persistence

SQLite is the authoritative source of truth.

Acceptance criteria:
- Users, requests, connections, and posts persist.
- Data remains available after a clean restart.
- Graph and Trie indexes are reconstructed from persisted records.
- Index reconstruction failures prevent dependent operations from being served with stale data.

### F15 — Discovery and Recommendations

The product may provide user discovery and connection recommendations.

The recommendation algorithm is intentionally unresolved. Jaccard and Katz are candidate approaches and must be compared before selection.

Acceptance criteria:
- Recommendations must be based on a documented, explainable algorithm.
- The selected algorithm must use the accepted-connection graph.
- Results must exclude the current user and existing connections.
- Algorithm selection must be recorded before implementation.

## 5. User Stories

- As a student, I want to create an account so I can join CampusConnect.
- As a user, I want to build my academic profile so others can understand my interests.
- As a user, I want to connect with other students.
- As a user, I want to discover mutual connections.
- As a user, I want to understand my network through degree and shortest-path information.
- As a user, I want to publish technical updates and project posts.
- As a user, I want to see posts from my network.
- As a user, I want to find students by name or username.
- As a user, I want relevant connection recommendations.

## 6. Optional Enhancements

These are not part of the mandatory delivery baseline:

- Image posts
- Likes
- Comments and replies
- Notifications
- Trending posts
- Groups and communities

They must not displace P0 work.

## 7. Explicit Exclusions

Unless formally approved through change control, the project does not include:
- Real-time chat
- Video calls
- External social-network synchronization
- AI-generated recommendations
- Cloud-hosted graph databases
- Microservice infrastructure
- Payment functionality

## 8. Definition of Feature Completion

A feature is complete only when:
1. Its behavior matches this specification.
2. Input validation and authorization are implemented.
3. Relevant persistence behavior is verified.
4. Relevant tests pass.
5. API and UI behavior are integrated.
6. Documentation is updated where required.
7. The implementation can be explained during viva.

---

**End of Document — features.md v1.0**