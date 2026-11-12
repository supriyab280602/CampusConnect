# CampusConnect — Debugging and Troubleshooting Guide

**Document:** debugging.md  
**Version:** 1.0  
**Status:** Draft — Awaiting Approval

---

## 1. Purpose

Defines a systematic process for identifying, reproducing, diagnosing, and resolving CampusConnect defects.

This guide is implementation-oriented but does not assume unverified source-code paths or functions.

## 2. Debugging Principles

1. Reproduce the issue before changing code.
2. Identify the affected layer.
3. Capture the exact error and request context.
4. Check recent changes.
5. Isolate the smallest failing component.
6. Fix the underlying cause rather than hiding the symptom.
7. Add a regression test.
8. Verify related functionality.
9. Update documentation if behavior or configuration changes.

Avoid changing multiple unrelated components while diagnosing one defect.

## 3. Identify the Layer

| Symptom | First area to inspect |
|---|---|
| Page does not load | Frontend/dev server |
| API request fails | Network/API/backend |
| Login fails | Authentication/session |
| Data disappears | Database/transaction |
| Connections incorrect | Graph synchronization |
| Search incomplete | Trie/index rebuilding |
| Feed order incorrect | Heap merge/sorting |
| UI does not update | Frontend state/API response |
| Works until restart | Persistence/index reconstruction |

## 4. Frontend Troubleshooting

Inspect:
- Browser console errors.
- Network request and response.
- API base URL.
- Frontend environment configuration.
- Component state.
- Loading and error states.
- JSON response shape.

Common issues:
- Incorrect API URL.
- Missing credentials on cookie-authenticated requests.
- Incorrect CSRF token handling.
- Unexpected null or missing response fields.
- Stale client-side state.
- Incorrect pagination cursor.

Do not solve backend defects by hardcoding fake frontend data.

## 5. Backend Troubleshooting

Inspect:
- Server startup logs.
- Flask route registration.
- Request validation.
- Session validation.
- Authorization decisions.
- Service-layer exceptions.
- Database errors.
- DSA module output.

Common issues:
- Missing environment variables.
- Invalid database path.
- Import errors.
- Route mismatch.
- Incorrect HTTP method.
- Unhandled exceptions.
- Invalid assumptions about authenticated identity.

Return safe API errors. Keep internal stack traces out of production responses.

## 6. Database Troubleshooting

Check:
- Database file path.
- Schema initialization.
- Foreign-key enforcement.
- Unique constraints.
- Transaction boundaries.
- Rollback behavior.
- Timestamp serialization.
- Data integrity after restart.

For suspected persistence failure:
1. Stop making destructive changes.
2. Preserve a copy of the database file.
3. Reproduce using a separate test database.
4. Inspect the relevant records and constraints.
5. Verify the transaction outcome.
6. Correct the underlying defect.
7. Run database and restart tests.

Never delete the database as the first debugging step.

## 7. Graph Debugging

When graph output is incorrect:
- Inspect persisted accepted connections.
- Confirm canonical connection records.
- Confirm each accepted edge appears in both adjacency lists.
- Check for self-edges or duplicate neighbors.
- Verify pending requests are not treated as accepted edges.
- Compare expected and actual graph structures.

If the graph is stale:
1. Mark graph-dependent operations unavailable.
2. Rebuild from SQLite.
3. Validate graph invariants.
4. Restore service only after successful verification.

Do not treat an in-memory graph as the authoritative record.

## 8. BFS Debugging

For incorrect path results:
- Confirm source and destination IDs.
- Verify graph connectivity.
- Check visited-set behavior.
- Check queue initialization.
- Confirm predecessor/distance updates.
- Verify disconnected-node handling.
- Ensure distance counts edges.

Test direct, multi-hop, same-node, and unreachable cases independently.

## 9. Trie Debugging

For search defects:
- Inspect normalized keys.
- Confirm insertion and deletion behavior.
- Verify terminal-node user-ID mappings.
- Check duplicate display-name handling.
- Confirm prefix traversal.
- Compare the Trie against source user records.
- Rebuild from SQLite if stale.

Do not discard duplicate user matches just because display names are identical.

## 10. Feed and Heap Debugging

For feed ordering defects:
- Inspect each input stream independently.
- Confirm each stream is sorted.
- Check heap comparison direction.
- Check timestamp parsing and timezone assumptions.
- Apply deterministic post-ID tie-breaking.
- Inspect cursor boundaries.
- Check for repeated or skipped records.

Do not assume timestamps are unique.

## 11. Authentication and Session Debugging

Inspect:
- Whether the login request succeeds.
- Whether the session cookie is issued.
- Cookie attributes.
- Whether the browser sends the cookie.
- Session record existence and expiry.
- CSRF token delivery and validation.
- Authorization checks for the requested resource.

Do not log session IDs, passwords, password hashes, or CSRF secrets.

## 12. CORS and Network Debugging

Check:
- Frontend origin.
- Backend allowed origin.
- Credential configuration.
- HTTP method and preflight behavior.
- Cookie SameSite/Secure attributes.
- API base URL.
- Backend availability.

CORS configuration does not replace authentication or CSRF protection.

## 13. Logging

Development logs should help diagnose:
- Application startup and shutdown.
- Database initialization.
- Graph and Trie rebuild outcomes.
- Request failures.
- Unexpected service exceptions.
- Test failures.

Production logs must avoid:
- Passwords
- Session identifiers
- Authentication cookies
- CSRF secrets
- Unnecessary personal information

Use structured, consistent log messages where practical.

## 14. Git-Safe Debugging

Before attempting risky fixes:
- Check `git status`.
- Review recent commits.
- Create a focused branch when appropriate.
- Avoid overwriting uncommitted work.
- Make small, reviewable changes.
- Run relevant tests before committing.

Do not use destructive Git commands as a generic troubleshooting shortcut.

## 15. Regression Prevention

Every confirmed defect should produce:
- A reproducible case.
- A root-cause explanation.
- A code fix.
- A regression test.
- A verification result.
- A documentation update when relevant.

A fix is not complete merely because the visible symptom disappears.

## 16. Escalation Criteria

Stop and reassess before proceeding when:
- Persistent data integrity is uncertain.
- Authentication may be compromised.
- Graph/Trie rebuild fails repeatedly.
- A fix would require changing a frozen architectural decision.
- A defect reveals a contradiction between approved documents.

Raise a change request instead of silently changing the approved baseline.

---

**End of Document — debugging.md v1.0**