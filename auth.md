# CampusConnect — Authentication and Authorization Specification

**Document:** auth.md  
**Version:** 1.0  
**Status:** Draft — Awaiting Approval

---

## 1. Purpose

Defines how CampusConnect identifies users, manages sessions, protects authenticated operations, and handles account security.

This document follows the approved server-managed session architecture and database design.

## 2. Authentication Model

CampusConnect uses **server-managed sessions**, not JWT-based stateless authentication.

The backend:
- Validates credentials.
- Creates and stores session records.
- Issues a session cookie.
- Validates the session on protected requests.
- Invalidates the session during logout.

SQLite stores session records as defined in database.md.

## 3. Registration

Required behavior:
1. Receive registration details.
2. Validate required fields and formats.
3. Normalize username and email for uniqueness checks.
4. Validate password policy.
5. Hash the password using a modern password-hashing algorithm.
6. Persist the user.
7. Return a safe user representation.

Security requirements:
- Never store plaintext passwords.
- Never return password hashes in API responses.
- Do not expose whether an arbitrary email or username belongs to an account through unnecessarily detailed authentication errors.
- Apply reasonable request validation and abuse controls.

## 4. Password Storage

Use a dedicated password-hashing implementation such as Argon2id or an appropriately configured established password-hashing library.

Requirements:
- Unique salt per password.
- Computationally expensive password verification.
- No reversible password encryption.
- No custom cryptographic implementation.
- Password hashes must remain server-side.

The final algorithm and parameters must be recorded in implementation configuration.

## 5. Login

Expected flow:
1. Receive username/email and password.
2. Locate the account using normalized identity.
3. Verify the supplied password against the stored hash.
4. Create a cryptographically unpredictable session identifier.
5. Store the session record.
6. Set the session cookie.
7. Return a safe authenticated-user response.

Authentication failures must not create a session.

## 6. Session Lifecycle

Session records include the user association and required session metadata.

Requirements:
- Session identifiers must be unpredictable.
- Session expiry must be enforced server-side.
- Logout must invalidate the session.
- Expired or deleted sessions must be rejected.
- Session identifiers must not be exposed in JSON response bodies or application logs.
- Session identifiers should be rotated after successful authentication to prevent fixation.

The exact expiry duration is an implementation decision to be recorded before release.

## 7. Cookie Security

The session cookie must use:
- `HttpOnly`
- `SameSite` configured appropriately for the deployment model
- `Secure` in HTTPS production environments
- A restricted path and appropriate lifetime

Development HTTP behavior must not be copied into production configuration.

## 8. CSRF Protection

Because authentication uses cookies, state-changing operations require CSRF protection.

Requirements:
- Protect POST, PUT, PATCH, and DELETE operations.
- Validate the CSRF token on protected state-changing requests.
- Reject invalid or missing tokens.
- Do not treat CORS as a replacement for CSRF protection.

The exact token delivery and validation mechanism must be finalized during implementation and remain consistent with api.md.

## 9. Authorization

Authentication answers: "Who is the user?"

Authorization answers: "Is this user allowed to perform this operation?"

Examples:
- Only an authenticated user may create a post.
- A user may delete only their own posts.
- A user may update only their own profile.
- Only the recipient may accept or reject a connection request.
- Only the sender may cancel their pending request.
- Protected network operations must use the authenticated identity where appropriate.

Authorization must be enforced by the backend, not merely hidden in the frontend.

## 10. Logout

Logout must:
1. Identify the active session.
2. Invalidate or delete its server-side record.
3. Clear the browser cookie.
4. Return a successful logout response.

A previously invalidated session must not authorize future requests.

## 11. Account Deletion

Account deletion follows the approved controlled hard-deletion policy in database.md.

The operation must transactionally clean up:
- Sessions
- Connection requests
- Accepted connections
- Posts
- User record

The in-memory graph and Trie must be updated or rebuilt consistently after the database transaction.

## 12. Security Requirements

- Validate all authentication inputs.
- Use password hashing, never plaintext storage.
- Avoid logging credentials, password hashes, cookies, or session identifiers.
- Use parameterized database operations.
- Apply CSRF protection.
- Enforce authorization server-side.
- Use safe error messages.
- Restrict production cookies to HTTPS.
- Keep secrets out of source control.
- Use least-privilege access to local database files.

## 13. Authentication Test Requirements

Test:
- Successful registration
- Duplicate username/email
- Invalid registration data
- Successful login
- Invalid password
- Unknown account
- Session persistence within configured lifetime
- Expired session
- Logout invalidation
- Missing/invalid CSRF token
- Unauthorized profile update
- Unauthorized post deletion
- Connection-request permission violations
- Account deletion cleanup

## 14. Out of Scope

Not included in the current baseline:
- OAuth/social login
- Two-factor authentication
- Passwordless login
- External identity providers
- Multi-device session management UI
- Enterprise single sign-on

---

**End of Document — auth.md v1.0**