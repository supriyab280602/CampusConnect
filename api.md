# CampusConnect — API Specification

**Document ID:** CC-API-005  
**Version:** 1.0  
**Status:** Draft — Awaiting Approval  
**API Style:** REST  
**Backend:** Python Flask  
**Communication:** HTTP + JSON  
**Database:** SQLite  
**Governing Documents:** PRD.md v1.0, design.md v1.1, architecture.md v1.1, database.md v1.1

---

## 1. Purpose

This document defines the API contract between the React frontend and Flask backend.

It specifies:
- API conventions.
- Authentication and authorization.
- Endpoint inventory.
- Request and response structures.
- Validation and error handling.
- Feed pagination.
- Search and connection workflows.

## 2. API Conventions

### Base URL

Development:

```text
http://localhost:5000/api/v1
```

Production base URL is determined by deployment configuration.

### Request format

```http
Content-Type: application/json
Accept: application/json
```

### Response format

Successful responses use JSON.

Example:

```json
{
  "success": true,
  "message": "Operation completed",
  "data": {}
}
```

Error responses:

```json
{
  "success": false,
  "message": "A clear error description",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": {}
  }
}
```

Do not expose stack traces, SQL errors, password hashes, or internal session information.

## 3. Authentication

**Selected mechanism:** Server-managed sessions.

### Session workflow

1. User submits login credentials.
2. Backend verifies the password hash.
3. Backend creates a session.
4. Backend sets a secure session cookie.
5. Browser includes the cookie in subsequent requests.
6. Backend authenticates protected requests using the session.

### Security requirements

- HttpOnly session cookie.
- Secure cookie in production.
- SameSite protection.
- CSRF protection for state-changing requests.
- Session invalidation on logout.
- Session expiry enforcement.
- No authentication based solely on frontend state.

For cross-origin development, configure credentials and CORS explicitly.

## 4. Endpoint Inventory

| Module | Method | Endpoint | Authentication |
|---|---|---|---|
| Auth | POST | `/auth/register` | Public |
| Auth | POST | `/auth/login` | Public |
| Auth | POST | `/auth/logout` | Required |
| Auth | GET | `/auth/me` | Required |
| Users | GET | `/users/:userId` | Required |
| Users | PUT | `/users/me` | Required |
| Connections | POST | `/connections/requests` | Required |
| Connections | GET | `/connections/requests/received` | Required |
| Connections | GET | `/connections/requests/sent` | Required |
| Connections | POST | `/connections/requests/:requestId/accept` | Required |
| Connections | POST | `/connections/requests/:requestId/reject` | Required |
| Connections | POST | `/connections/requests/:requestId/cancel` | Required |
| Connections | GET | `/connections` | Required |
| Connections | DELETE | `/connections/:userId` | Required |
| Posts | POST | `/posts` | Required |
| Posts | GET | `/posts/:postId` | Required |
| Posts | DELETE | `/posts/:postId` | Required |
| Feed | GET | `/feed` | Required |
| Search | GET | `/search/users` | Required |
| Network | GET | `/network/:userId/mutuals` | Required |
| Network | GET | `/network/:userId/degree` | Required |
| Network | GET | `/network/path` | Required |
| Network | GET | `/network/recommendations` | Required |

Network endpoints expose graph operations through the backend. They must not calculate graph results in the browser.

## 5. Authentication Endpoints

### 5.1 Register

`POST /auth/register`

Request:

```json
{
  "username": "student01",
  "email": "student@example.com",
  "password": "ExamplePassword123",
  "full_name": "Student Name"
}
```

Response — `201 Created`:

```json
{
  "success": true,
  "message": "Account created successfully",
  "data": {
    "user_id": 1,
    "username": "student01"
  }
}
```

Validation:
- Username required and unique after normalization.
- Email required and unique after normalization.
- Password must meet the selected password policy.
- Full name must not be empty.
- Password must be hashed before storage.

### 5.2 Login

`POST /auth/login`

Request:

```json
{
  "username": "student01",
  "password": "ExamplePassword123"
}
```

Response — `200 OK`:

```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user_id": 1,
    "username": "student01"
  }
}
```

The backend sets the session cookie.

Invalid credentials return `401 Unauthorized`. The response must not reveal whether the username or password was incorrect.

### 5.3 Logout

`POST /auth/logout`

Response — `200 OK`:

```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

The backend invalidates the session and expires the cookie.

### 5.4 Current user

`GET /auth/me`

Response:

```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "username": "student01",
    "full_name": "Student Name"
  }
}
```

## 6. User Profile Endpoints

### 6.1 Get profile

`GET /users/:userId`

Returns the permitted public profile fields.

Response:

```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "username": "student01",
    "full_name": "Student Name",
    "programme": "Computer Science",
    "academic_year": 3,
    "bio": "Interested in technology",
    "skills": ["Python", "React"]
  }
}
```

Password hashes and private authentication data must never be returned.

### 6.2 Update own profile

`PUT /users/me`

Request:

```json
{
  "full_name": "Updated Name",
  "programme": "Computer Science",
  "academic_year": 3,
  "bio": "Updated profile description",
  "skills": ["Python", "React", "SQL"]
}
```

Response:

```json
{
  "success": true,
  "message": "Profile updated successfully"
}
```

Only the authenticated user's profile may be modified through this endpoint.

Updating searchable fields must trigger the corresponding Trie update or controlled index rebuild.

## 7. Connection Endpoints

### 7.1 Send request

`POST /connections/requests`

Request:

```json
{
  "receiver_id": 2
}
```

Response — `201 Created`:

```json
{
  "success": true,
  "message": "Connection request sent",
  "data": {
    "request_id": 10,
    "status": "pending"
  }
}
```

Rules:
- Sender is obtained from the authenticated session.
- Self-requests are prohibited.
- Existing accepted connections are rejected.
- Duplicate pending requests are rejected.
- Reverse pending requests are rejected.
- A reverse request is allowed only after the existing pending request is resolved.

### 7.2 Received requests

`GET /connections/requests/received`

Returns pending requests addressed to the authenticated user.

### 7.3 Sent requests

`GET /connections/requests/sent`

Returns pending requests sent by the authenticated user.

### 7.4 Accept request

`POST /connections/requests/:requestId/accept`

Only the intended receiver may accept.

Response:

```json
{
  "success": true,
  "message": "Connection accepted"
}
```

The database transaction must create the canonical accepted edge and update the request status before updating the in-memory graph.

### 7.5 Reject request

`POST /connections/requests/:requestId/reject`

Only the intended receiver may reject.

### 7.6 Cancel request

`POST /connections/requests/:requestId/cancel`

Only the original sender may cancel.

### 7.7 List connections

`GET /connections`

Returns the authenticated user's accepted connections.

### 7.8 Remove connection

`DELETE /connections/:userId`

Removes the accepted connection between the authenticated user and the specified user.

Both graph directions must be removed after the database transaction succeeds.

## 8. Post Endpoints

### 8.1 Create post

`POST /posts`

Request:

```json
{
  "content": "Sharing my latest technical project."
}
```

Response — `201 Created`:

```json
{
  "success": true,
  "message": "Post created successfully",
  "data": {
    "post_id": 101,
    "content": "Sharing my latest technical project."
  }
}
```

The author is derived from the authenticated session, never trusted from the request body.

### 8.2 Get post

`GET /posts/:postId`

Returns a post and its permitted author information.

### 8.3 Delete post

`DELETE /posts/:postId`

Only the post owner may delete the post.

## 9. Feed Endpoint

### 9.1 Retrieve feed

`GET /feed`

Query parameters:

| Parameter | Purpose |
|---|---|
| limit | Maximum posts per page |
| cursor | Position from which the next page continues |

Example:

```http
GET /api/v1/feed?limit=10
```

Next page:

```http
GET /api/v1/feed?limit=10&cursor=ENCODED_CURSOR
```

Response:

```json
{
  "success": true,
  "data": {
    "posts": [
      {
        "post_id": 101,
        "user_id": 1,
        "content": "My latest project update",
        "created_at": "2026-11-11T14:30:00Z"
      }
    ],
    "next_cursor": "ENCODED_CURSOR",
    "has_more": true
  }
}
```

### Feed rules

- Include posts from the authenticated user and accepted connections as specified in the approved product requirements.
- Exclude posts from users who are not accepted connections.
- Sort newest first.
- Use post ID as a deterministic tie-breaker.
- Use cursor-based pagination.
- Use the heap-based merge strategy defined in architecture.md.

The cursor represents the last returned timestamp and post ID. Pagination does not guarantee a frozen snapshot when new posts are created during browsing.

The backend must validate cursor input and enforce a maximum page size.

## 10. Search Endpoint

### 10.1 Search users

`GET /search/users?q=san`

Query parameter:

| Parameter | Requirement |
|---|---|
| q | Required search prefix |
| limit | Optional result limit |

Response:

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "user_id": 1,
        "username": "sanjana",
        "full_name": "Sanjana"
      }
    ]
  }
}
```

Search rules:
- Use the custom Trie for prefix lookup.
- Normalize query text using the same rules as indexing.
- Support multiple matches for identical display names.
- Retrieve current profile details from the user repository.
- Apply result limits.
- Do not expose private account information.

## 11. Network Endpoints

### 11.1 Mutual connections

`GET /network/:userId/mutuals`

Returns users connected to both the authenticated user and the specified user.

### 11.2 Degree

`GET /network/:userId/degree`

Returns the immediate accepted-connection count.

Response:

```json
{
  "success": true,
  "data": {
    "user_id": 2,
    "degree": 8
  }
}
```

### 11.3 Shortest path

`GET /network/path?targetUserId=2`

The authenticated user is the source.

Response:

```json
{
  "success": true,
  "data": {
    "path": [1, 4, 7, 2],
    "distance": 3
  }
}
```

If no path exists, return a successful response with an explicit no-path result, rather than inventing a distance.

### 11.4 Recommendations

`GET /network/recommendations`

Returns candidate connections generated by the selected recommendation algorithm.

The final scoring method remains subject to the algorithm decision recorded in architecture.md.

## 12. HTTP Status Codes

| Code | Meaning |
|---|---|
| 200 | Successful retrieval or operation |
| 201 | Resource created |
| 204 | Successful deletion with no response body |
| 400 | Invalid request |
| 401 | Authentication required or invalid credentials |
| 403 | Authenticated but unauthorized |
| 404 | Resource not found |
| 409 | Conflict with existing state |
| 422 | Valid JSON but invalid field values |
| 429 | Rate limit exceeded, if rate limiting is implemented |
| 500 | Unexpected server error |
| 503 | Required application index unavailable during recovery |

## 13. Validation Rules

All request data must be validated on the backend.

Examples:

- Required fields must be present.
- IDs must be valid integers.
- Text content must not be empty after trimming.
- Username and email must follow normalization rules.
- Academic year must satisfy the selected valid range.
- Skills must be a valid JSON-compatible string array.
- Pagination limits must be bounded.
- Cursors must be valid and safely parsed.
- Users cannot perform actions on behalf of another user by changing request-body IDs.

## 14. Error Handling

Standard response:

```json
{
  "success": false,
  "message": "The requested operation could not be completed",
  "error": {
    "code": "CONNECTION_CONFLICT",
    "details": {}
  }
}
```

Error categories:

| Error code | Meaning |
|---|---|
| VALIDATION_ERROR | Invalid input |
| AUTHENTICATION_REQUIRED | Missing session |
| INVALID_CREDENTIALS | Login failure |
| FORBIDDEN | Unauthorized operation |
| RESOURCE_NOT_FOUND | Missing resource |
| CONNECTION_CONFLICT | Duplicate or invalid connection state |
| DUPLICATE_ACCOUNT | Username/email already exists |
| INDEX_UNAVAILABLE | Graph or Trie rebuilding |
| INTERNAL_ERROR | Unexpected backend error |

## 15. API Security Requirements

- Authenticate protected endpoints.
- Enforce ownership and authorization server-side.
- Use CSRF protection for state-changing session-authenticated requests.
- Validate every request.
- Use parameterized database queries.
- Never return password hashes.
- Never expose session IDs in API response bodies.
- Configure CORS explicitly.
- Do not expose internal exception details.

## 16. Endpoint Acceptance Criteria

- [ ] Every endpoint has a defined method and path.
- [ ] Protected endpoints require a valid session.
- [ ] Authorization is checked server-side.
- [ ] Request and response formats are consistent.
- [ ] Connection lifecycle follows database.md v1.1.
- [ ] Reverse pending requests are rejected.
- [ ] Accepted connection operations synchronize the graph.
- [ ] Search uses Trie prefix lookup.
- [ ] Feed uses deterministic ordering and cursor pagination.
- [ ] Network operations execute in the Python DSA core.
- [ ] Errors use consistent response structures.
- [ ] Sensitive data is never returned.

---

**Document Control**

**Document ID:** CC-API-005  
**Version:** 1.0  
**Status:** DRAFT — AWAITING APPROVAL  
**Governing baseline:** PRD.md v1.0, design.md v1.1, architecture.md v1.1, database.md v1.1