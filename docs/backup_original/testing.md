# CampusConnect — Testing Strategy and Test Plan

**Document:** testing.md  
**Version:** 1.0  
**Status:** Draft — Awaiting Approval

---

## 1. Purpose

Defines how CampusConnect will be verified against its functional, technical, security, and academic requirements.

This is a planned test strategy. No test execution or passing result is claimed at this stage.

## 2. Testing Principles

- Test mandatory requirements before optional enhancements.
- Test DSA algorithms independently of the UI.
- Verify persistence across restart.
- Test authorization and invalid state transitions.
- Use deterministic test data.
- Test edge cases, not only happy paths.
- Do not claim tests passed unless they were executed.

## 3. Testing Layers

| Layer | Purpose |
|---|---|
| Unit | Validate individual functions and DSA algorithms |
| Database | Validate schema, constraints, and transactions |
| Service | Validate application rules |
| API | Validate endpoint contracts and status codes |
| Frontend | Validate components and user interactions |
| Integration | Validate component communication |
| End-to-end | Validate complete user journeys |
| Security | Validate authentication and authorization controls |

## 4. DSA Unit Tests

### Graph

Test:
- Add a valid connection.
- Reject self-connections.
- Reject duplicate connections.
- Remove an existing connection.
- Maintain undirected adjacency.
- Handle isolated users.
- Handle disconnected components.

### BFS

Test:
- Same source and destination.
- Direct connection.
- Multi-hop path.
- Disconnected users.
- Empty graph.
- Cyclic graph.
- Multiple equally short paths.

Expected properties:
- Shortest-path distance is measured in edges.
- BFS visits each reachable vertex at most once.
- Complexity is O(V + E) for adjacency-list representation.

### Mutual Connections

Test:
- No common neighbors.
- One common neighbor.
- Multiple common neighbors.
- Same-user query behavior.
- Results after connection removal.

### Trie

Test:
- Insert and find a username.
- Prefix matching.
- Case normalization.
- Whitespace normalization.
- Empty prefix handling.
- Multiple users sharing a display-name key.
- Missing prefix.
- Rebuild from persisted users.

### Heap-Based Feed Merge

Test:
- Single source stream.
- Multiple source streams.
- Empty streams.
- Equal timestamps.
- Deterministic post-ID tie-breaker.
- Cursor pagination.
- No duplicate posts.

## 5. Database Tests

Verify:
- Unique normalized username.
- Unique normalized email.
- Foreign-key constraints.
- Connection uniqueness.
- Request-state constraints.
- Transaction rollback.
- Session invalidation.
- Post ownership.
- Account deletion cleanup.
- UTC timestamp handling.

Restart test:
1. Create users.
2. Create accepted connections.
3. Create posts.
4. Stop the backend.
5. Restart the backend.
6. Verify persisted records.
7. Verify graph and Trie reconstruction.

## 6. Authentication and Security Tests

Test:
- Valid registration.
- Duplicate registration.
- Invalid credentials.
- Session creation.
- Session expiry.
- Logout.
- CSRF rejection.
- Unauthorized profile modification.
- Unauthorized post deletion.
- Unauthorized request transitions.
- Sensitive information not exposed in API responses.

## 7. API Tests

For every endpoint verify:
- HTTP method.
- Request validation.
- Response schema.
- Status code.
- Authentication requirement.
- Authorization requirement.
- Error response.
- Database side effects.
- DSA side effects where applicable.

Test pagination boundaries and malformed cursors.

## 8. Frontend Tests

Verify:
- Registration and login forms.
- Profile display and editing.
- Connection request actions.
- Post creation and deletion.
- Feed ordering.
- Search suggestions.
- Loading states.
- Empty states.
- Error states.
- Responsive layouts.
- Session expiry handling.

## 9. End-to-End Scenarios

### Scenario A — New user

Register → log in → complete profile → log out → log in again.

### Scenario B — Connection lifecycle

User A sends request → User B accepts → both users see the connection → graph reflects the edge.

### Scenario C — Network analysis

Create a multi-hop network → query degree → query shortest path → verify expected results.

### Scenario D — Posts and feed

Create posts from multiple connected users → request feed → verify ordering and ownership visibility.

### Scenario E — Search

Create users with different names → search prefixes → verify Trie results and duplicate display-name behavior.

### Scenario F — Persistence

Create data → restart application → verify records and derived indexes.

## 10. Test Data

Use deterministic test fixtures:
- Isolated user
- Directly connected pair
- Three-user chain
- Cyclic graph
- Disconnected graph
- Multiple users with similar names
- Multiple posts with equal timestamps
- Expired and valid sessions

Do not use real student passwords or sensitive personal information in test fixtures.

## 11. Test Tooling

Proposed tooling:
- pytest for backend tests.
- Flask test client for API tests.
- React Testing Library for frontend component tests.
- Browser-based end-to-end tooling if needed.

Exact dependencies and commands must be verified against the actual repository.

## 12. Test Commands

The following are provisional examples, not confirmed repository scripts:

```bash
pytest
```

```bash
npm test
```

```bash
npm run build
```

Replace or finalize these commands after test configuration is implemented.

## 13. Release Acceptance Gates

A release candidate must satisfy:
1. All mandatory feature acceptance criteria.
2. DSA unit tests pass.
3. Database constraints and restart tests pass.
4. Authentication and authorization tests pass.
5. API contract tests pass.
6. Frontend integration tests pass.
7. No known critical security defect remains.
8. Documentation matches implemented behavior.
9. The student can explain the core DSA implementation.

## 14. Defect Severity

- **Critical:** Data loss, account compromise, or core application unavailable.
- **High:** Mandatory feature broken or authorization bypass.
- **Medium:** Significant usability or non-critical functional defect.
- **Low:** Cosmetic or minor usability issue.

## 15. Test Reporting

Every test report should include:
- Test ID
- Feature/module
- Preconditions
- Input
- Expected result
- Actual result
- Pass/fail status
- Defect reference if failed

Never report a planned test as an executed test.

---

**End of Document — testing.md v1.0**