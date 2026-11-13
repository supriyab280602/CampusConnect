# CampusConnect — Database Design

**Document ID:** CC-DAT-004
**Version:** 1.2
**Status:** APPROVED
**Project:** CampusConnect — University-exclusive student networking platform
**Database:** SQLite
**Owner:** CampusConnect Project Team

---

## 1. Purpose and scope

This document defines the persistent data model and database operating rules for CampusConnect.

The database is the persistent source of truth for users, connection requests, accepted connections, posts, and user sessions. Graph and search structures used by the application are derived in-memory indexes. They must be rebuildable from persisted records and must not become an independent source of truth.

This specification covers the baseline project only. Chat, likes, comments, media uploads, groups, notifications, AI services, external graph databases, Redis, and multi-process graph synchronization are out of scope.

## 2. Architectural decisions

1. **SQLite is the persistent source of truth.**
2. **Python application code performs graph calculations.** Graph queries must not be delegated to database graph extensions or external graph databases.
3. **Accepted connections are undirected graph edges.**
4. **Pending connection requests are directed records and are not graph edges.**
5. **The graph and Trie are derived in-memory structures** rebuilt from SQLite at application startup.
6. **Foreign-key enforcement must be enabled on every database connection.**
7. **All SQL statements that include user-supplied values must be parameterized.**
8. **Database writes must use transactions** where more than one statement or a cross-record invariant is involved.
9. **Database commit must succeed before derived in-memory indexes are changed.**
10. **Schema changes must be versioned and migrated.** Do not silently modify an existing database schema.

## 3. Data model overview

The baseline schema contains five core tables:

| Table | Purpose |
|---|---|
| `users` | Account credentials and student profile data |
| `connection_requests` | Directed requests to connect with another user |
| `connections` | Canonical undirected accepted connections |
| `posts` | User-authored feed posts |
| `user_sessions` | Server-managed authenticated sessions |

### 3.1 Entity relationships

- One user can create many connection requests as sender and receive many as receiver.
- One user can have many accepted connections.
- One user can create many posts.
- One user can have many active or historical session records.
- Deleting a user removes that user's dependent records according to the deletion rules in this document.

## 4. Table specifications

### 4.1 `users`

Stores account identity, authentication data, and student profile information.

| Column | Type | Constraints / rules | Description |
|---|---|---|---|
| `user_id` | TEXT | Primary key | Application-generated unique user identifier |
| `username` | TEXT | NOT NULL | Display username |
| `username_key` | TEXT | NOT NULL, UNIQUE | Normalized username key used for case-insensitive uniqueness and lookup |
| `email` | TEXT | NOT NULL | User email address |
| `email_key` | TEXT | NOT NULL, UNIQUE | Normalized email key used for case-insensitive uniqueness and lookup |
| `password_hash` | TEXT | NOT NULL | Password hash; never store plaintext passwords |
| `full_name` | TEXT | NOT NULL | User's full name; not unique |
| `programme` | TEXT | NOT NULL | Academic programme |
| `academic_year` | INTEGER | NOT NULL | Current academic year |
| `bio` | TEXT | Nullable | Optional profile biography |
| `skills` | TEXT | NOT NULL | JSON-encoded list of skills; validate in application code |
| `created_at` | TEXT | NOT NULL | UTC creation timestamp |
| `updated_at` | TEXT | NOT NULL | UTC last-update timestamp |

**Normalization rules**

- Generate `username_key` and `email_key` in application code using a consistent Unicode-aware normalization and case-folding procedure.
- Enforce uniqueness on the normalized key columns, not by relying on SQLite's default `NOCASE` behavior for all Unicode text.
- Preserve the original `username`, `email`, and `full_name` values for display according to application validation rules.
- `full_name` is not unique.
- Validate `skills` as a JSON array of strings in application code before persistence.
- The exact allowed values and range for `academic_year` must be validated by the application according to the project's agreed academic-year rules.

### 4.2 `connection_requests`

Stores directed requests between users. A request is not an accepted connection until it is accepted and the corresponding undirected edge is created in `connections`.

| Column | Type | Constraints / rules | Description |
|---|---|---|---|
| `request_id` | TEXT | Primary key | Application-generated request identifier |
| `sender_id` | TEXT | NOT NULL, FK to `users.user_id` ON DELETE CASCADE | User who sent the request |
| `receiver_id` | TEXT | NOT NULL, FK to `users.user_id` ON DELETE CASCADE | User who received the request |
| `status` | TEXT | NOT NULL | `pending`, `accepted`, `rejected`, or `cancelled` |
| `created_at` | TEXT | NOT NULL | UTC creation timestamp |
| `updated_at` | TEXT | NOT NULL | UTC last-update timestamp |

**Integrity rules**

- A user cannot send a request to themselves (`sender_id` must differ from `receiver_id`).
- Only one pending request may exist for the same sender/receiver direction.
- If A has a pending request to B, B cannot create a reverse pending request to A. The existing request must first be accepted, rejected, or cancelled.
- The reverse-direction check and request insertion must run in one write transaction. Use `BEGIN IMMEDIATE` so competing writes cannot both pass the check before either inserts.
- Historical resolved requests may remain in this table.
- A pending request must not be inserted into the accepted-connections graph.
- Accepting a request must create exactly one canonical row in `connections` and update the request status in the same transaction.
- Rejecting or cancelling a request must update its status without creating a connection edge.

### 4.3 `connections`

Stores accepted connections as canonical undirected edges.

| Column | Type | Constraints / rules | Description |
|---|---|---|---|
| `connection_id` | TEXT | Primary key | Application-generated connection identifier |
| `user_id_low` | TEXT | NOT NULL, FK to `users.user_id` ON DELETE CASCADE | Lower-sorted user identifier |
| `user_id_high` | TEXT | NOT NULL, FK to `users.user_id` ON DELETE CASCADE | Higher-sorted user identifier |
| `created_at` | TEXT | NOT NULL | UTC acceptance timestamp |

**Integrity rules**

- Store each undirected pair once, using canonical ordering: `user_id_low` is the lower identifier and `user_id_high` is the higher identifier under the application's consistent identifier ordering.
- Enforce `user_id_low < user_id_high`.
- Enforce uniqueness on `(user_id_low, user_id_high)`.
- Self-connections are prohibited.
- The graph layer must interpret each row as two adjacency entries: low-to-high and high-to-low.
- Removing a connection deletes the canonical row. The graph index is updated only after the database transaction commits.

### 4.4 `posts`

Stores text posts authored by users.

| Column | Type | Constraints / rules | Description |
|---|---|---|---|
| `post_id` | TEXT | Primary key | Application-generated post identifier |
| `user_id` | TEXT | NOT NULL, FK to `users.user_id` ON DELETE CASCADE | Author of the post |
| `content` | TEXT | NOT NULL | Post body |
| `created_at` | TEXT | NOT NULL | UTC creation timestamp |
| `updated_at` | TEXT | NOT NULL | UTC last-update timestamp |

**Integrity rules**

- A post must have a valid existing author.
- Reject empty or whitespace-only content in application code.
- Enforce the product's configured content-length limit in application code.
- Only the post owner may edit or delete the post, enforced by backend authorization.
- The baseline feed includes the current user's posts and posts by accepted connections.

### 4.5 `user_sessions`

Stores server-managed session records. The browser receives a random session token; the database stores only a cryptographic hash of that token.

| Column | Type | Constraints / rules | Description |
|---|---|---|---|
| `session_id` | TEXT | Primary key | Hash of the random session token; never the raw token |
| `user_id` | TEXT | NOT NULL, FK to `users.user_id` ON DELETE CASCADE | Session owner |
| `csrf_token_hash` | TEXT | Nullable | Hash of the session's CSRF token, where the selected CSRF strategy uses one |
| `created_at` | TEXT | NOT NULL | UTC creation timestamp |
| `expires_at` | TEXT | NOT NULL | UTC expiry timestamp |

**Session security rules**

- Generate session tokens using a cryptographically secure random generator with sufficient entropy.
- Send the raw token only to the client in a cookie; never persist or log the raw token.
- Store a cryptographic hash of the token in `session_id` and hash the presented token before lookup.
- Session cookies must be `HttpOnly` and use an appropriate `SameSite` policy. Set `Secure` in production over HTTPS.
- Apply the CSRF protection strategy defined by the authentication specification. If using a synchronizer token, store only its hash in `csrf_token_hash`.
- Expired sessions must be rejected.
- Logout must invalidate the relevant session record.
- Password changes and account deletion must invalidate all sessions for the affected user.
- Session cleanup may periodically delete expired records.

## 5. Indexes and constraints

Create indexes to support common lookups and preserve data integrity.

| Table | Index / constraint | Purpose |
|---|---|---|
| `users` | UNIQUE(`username_key`) | Case-insensitive username uniqueness |
| `users` | UNIQUE(`email_key`) | Case-insensitive email uniqueness |
| `connection_requests` | Partial UNIQUE(`sender_id`, `receiver_id`) WHERE status = 'pending' | Prevent duplicate pending requests in the same direction |
| `connection_requests` | (`receiver_id`, `status`, `created_at`) | Retrieve incoming requests |
| `connection_requests` | (`sender_id`, `status`, `created_at`) | Retrieve outgoing requests |
| `connections` | UNIQUE(`user_id_low`, `user_id_high`) | Prevent duplicate accepted edges |
| `connections` | (`user_id_low`) | Find edges for the low endpoint |
| `connections` | (`user_id_high`) | Find edges for the high endpoint |
| `posts` | (`user_id`, `created_at`, `post_id`) | Retrieve a user's posts in feed order |
| `posts` | (`created_at`, `post_id`) | Support time-ordered post retrieval |
| `user_sessions` | (`user_id`) | Find and invalidate a user's sessions |
| `user_sessions` | (`expires_at`) | Find expired sessions |

SQLite partial indexes are supported by the project's SQLite baseline. Verify the actual SQLite runtime version during setup and tests.

## 6. Database transaction rules

Use transactions for operations that modify related records or enforce invariants across multiple rows.

| Operation | Required transaction behavior |
|---|---|
| User registration | Insert user atomically; uniqueness conflicts must fail cleanly |
| Session creation | Insert session record atomically |
| Connection request creation | `BEGIN IMMEDIATE`; check both request directions and existing connection; insert only if valid |
| Accept request | Verify pending request; create canonical connection; update request status atomically |
| Reject request | Verify pending request and update status atomically |
| Cancel request | Verify sender ownership and pending status; update status atomically |
| Remove connection | Delete canonical connection row atomically |
| Create post | Insert post atomically |
| Delete post | Verify ownership and delete atomically |
| Delete user | Delete user and all dependent records atomically |

**Failure handling**

- Roll back the transaction if any required statement fails.
- Do not report success to the client until the database commit succeeds.
- Use short write transactions; do not perform expensive graph computation while holding a write lock.
- Use parameterized SQL for all values.
- Enable foreign keys on every connection using `PRAGMA foreign_keys = ON`.
- After a successful database commit, update the relevant in-memory indexes.
- If an in-memory index update fails, mark that index unavailable and rebuild it from committed database state before serving operations that depend on it. Do not roll back or misrepresent an already committed database transaction.

## 7. Derived in-memory data structures

The database remains authoritative. These structures are derived from persisted records and must be reconstructible.

### 7.1 Accepted-connections graph

- Build the graph from rows in `connections` at application startup.
- Use an adjacency-list representation in Python.
- Treat every accepted connection as an undirected edge by inserting both directions into adjacency lists.
- Do not add pending requests to the graph.
- Calculate degree from adjacency-list length.
- Use BFS to calculate unweighted shortest connection paths.
- Calculate mutual connections using adjacency-list intersections.
- After a committed connection acceptance or removal, update the graph.
- Rebuild the graph from SQLite if it becomes inconsistent or unavailable.

### 7.2 User search Trie

- Build the Trie from persisted user profile records at startup.
- Index normalized usernames and full names according to the agreed search behavior.
- A terminal Trie node must support multiple user IDs where multiple users share the same indexed full name.
- Do not assume full names are unique.
- Update the Trie only after the corresponding database transaction commits.
- Rebuild the Trie from SQLite if it becomes inconsistent or unavailable.

### 7.3 Feed merge using a heap

- The baseline feed contains the current user's posts and posts from accepted connections.
- Retrieve each author's posts in time order.
- Merge the ordered author streams using a heap-based k-way merge.
- Return newest posts first.
- Use `created_at` as the primary ordering key and `post_id` as a deterministic tie-breaker.
- Use a stable cursor containing both timestamp and post ID for pagination so posts with identical timestamps are not skipped or duplicated.

## 8. Timestamp and identifier conventions

- Store timestamps in UTC.
- Use one fixed-width ISO-8601 representation: `YYYY-MM-DDTHH:MM:SS.ffffffZ`.
- Generate timestamps consistently in backend code.
- Use the same identifier comparison rule whenever canonical ordering is required.
- Identifiers must be unique and generated using a collision-resistant application strategy.

## 9. User deletion and referential integrity

The baseline account deletion policy is controlled hard deletion.

- Delete the user inside a transaction.
- Foreign-key cascades remove that user's sessions, connection requests, accepted connections, and posts.
- Ensure `PRAGMA foreign_keys = ON` is active for the connection performing the deletion.
- After commit, remove the user from the in-memory graph and Trie, and update affected graph entries.
- If derived-index updates fail, rebuild the affected index from the database before using it.
- Do not perform manual multi-step deletion outside a transaction.

## 10. Startup, recovery, and database operations

At application startup:

1. Open the SQLite database.
2. Enable foreign-key enforcement on the connection.
3. Check the schema version.
4. Apply only the required, versioned migrations.
5. Load persisted accepted connections and rebuild the graph.
6. Load persisted user search fields and rebuild the Trie.
7. Ensure derived indexes are ready before enabling endpoints that depend on them.

Operational rules:

- Use a consistent database path configured for the application environment.
- Do not commit local database files containing real user data to the repository.
- Back up the database before destructive migrations, resets, or debugging operations that may alter persistent data.
- Keep write transactions short.
- Handle SQLite errors without exposing SQL details, credentials, password hashes, session hashes, or other internal data to clients.
- Use a single-process backend deployment for the baseline implementation. Multi-process or multi-worker synchronization of in-memory graph and Trie indexes is out of scope; do not enable it without redesigning index ownership and synchronization.

## 11. Schema versioning and migrations

- Track the schema version using SQLite `PRAGMA user_version`.
- Every schema change must have an explicit migration from the previous supported version.
- Migrations must be deterministic, tested, and safe to rerun only where explicitly designed to be idempotent.
- Back up persistent data before destructive migrations.
- Do not silently recreate or wipe a database when a migration fails.
- Preserve the prior approved database specification in the documentation backup/archive when replacing this version.

## 12. Explicitly out of scope

The following are not part of this database baseline:

- Direct messages or chat
- Likes and comments
- Image, video, or file uploads
- Groups or communities
- Notifications
- AI/ML services
- Redis or external caching infrastructure
- External graph databases or graph-query engines
- Multi-process in-memory graph synchronization

These features require a separately reviewed scope and schema change.

## 13. Acceptance criteria

The database implementation is considered compliant with this specification when all of the following are verified:

- [ ] SQLite is the persistent source of truth.
- [ ] All five core tables are created with the specified columns and constraints.
- [ ] Foreign-key enforcement is enabled on every database connection.
- [ ] Username and email uniqueness is enforced through normalized key columns.
- [ ] Passwords are stored only as secure password hashes.
- [ ] Raw session tokens are never stored in the database.
- [ ] Duplicate pending requests in the same direction are prevented.
- [ ] Reverse-direction pending requests are prevented transactionally.
- [ ] Pending requests do not appear as graph edges.
- [ ] Accepted connections are stored once using canonical user-ID ordering.
- [ ] Graph adjacency lists contain both directions for every accepted connection.
- [ ] BFS shortest paths, degree, and mutual-connection calculations run in Python.
- [ ] Trie search indexes are rebuilt from persisted user records.
- [ ] Feed streams are merged using a heap and deterministic ordering.
- [ ] Feed pagination uses a stable timestamp-plus-post-ID cursor.
- [ ] User deletion removes dependent records atomically.
- [ ] Database failures roll back incomplete transactions.
- [ ] Derived indexes are updated only after commit and can be rebuilt.
- [ ] Schema migrations are versioned and tested.
- [ ] Tests verify persistence across application restarts.

## 14. Change control

This document is **Version 1.2 — APPROVED**.

Version 1.2 supersedes Version 1.1 as the active database design specification. Preserve the original Version 1.1 document in the project's documentation backup/archive. Any future change to table structure, constraints, transaction invariants, persistence behavior, or derived-index responsibilities requires an explicit document revision and corresponding migration review.

---

**End of CC-DAT-004 v1.2**
