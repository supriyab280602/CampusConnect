# CampusConnect — Agent Instructions

**Document ID:** CC-AGT-006  
**Version:** 1.0  
**Status:** Draft — Awaiting Approval  
**Project:** CampusConnect  
**Governing Documents:** PRD.md v1.0, design.md v1.1, architecture.md v1.1, database.md v1.1, api.md v1.0

---

## 1. Purpose

This document establishes working instructions for AI coding agents and developers contributing to CampusConnect.

Its purpose is to ensure that implementation remains consistent with approved requirements, architecture, database design, API contracts, and UI specifications.

Agents must prioritize correctness, maintainability, explainability, and controlled changes over unnecessary complexity.

## 2. Project Context

CampusConnect is a student social and professional networking platform.

It combines:
- Student profiles and academic identity.
- Accepted connections and pending requests.
- A student post feed.
- Prefix-based student search.
- Graph-based network exploration.
- Connection recommendations.

The project is an individual academic DSA implementation. The code must be understandable and explainable by the student during evaluation.

## 3. Source-of-Truth Hierarchy

Agents must follow this document precedence:

1. Assignment requirements — highest authority for academic constraints.
2. PRD.md v1.0 — approved product requirements.
3. design.md v1.1 — approved visual and interaction specification.
4. architecture.md v1.1 — approved technical architecture.
5. database.md v1.1 — approved persistence model.
6. api.md v1.0 — approved API contract.
7. Implementation code — must conform to the documents above.

If two sources conflict:

- Do not silently choose one.
- Identify the conflicting statements.
- Explain the impact.
- Request a decision before changing frozen requirements.

An agent must never modify an approved document simply to justify an implementation that violates it.

## 4. Technology Constraints

The approved project baseline is:

| Layer | Technology |
|---|---|
| Frontend | React |
| Build tool | Vite |
| Backend | Python Flask |
| Database | SQLite |
| Communication | REST API / JSON |
| Graph | Python adjacency list |
| Traversal | BFS |
| Search | Custom Trie |
| Feed merge | Heap / priority queue |
| Authentication | Server-managed sessions |

Agents must not introduce the following without explicit approval:

- Microservices.
- Redis or distributed caching.
- NetworkX as a replacement for the custom graph.
- External AI services.
- Cloud databases.
- Unnecessary state-management frameworks.
- Additional infrastructure that does not solve a demonstrated problem.

## 5. Core Engineering Rules

### 5.1 Separation of concerns

- React handles presentation and user interaction.
- Flask routes handle HTTP request and response handling.
- Services implement business logic.
- Repositories handle SQLite access.
- The DSA core implements data structures and algorithms.

Do not place SQL queries inside React components.

Do not put graph algorithms inside route handlers.

Do not make the frontend responsible for authorization.

### 5.2 DSA implementation

The custom DSA implementations are central to the academic objective.

Agents must:

- Implement the adjacency-list graph explicitly.
- Implement BFS explicitly.
- Implement Trie operations explicitly.
- Implement heap-based feed merging explicitly.
- Keep algorithms independently testable.
- Document time and space complexity accurately.
- Avoid substituting library functionality for the required custom implementation.

Every algorithm must have meaningful test cases.

### 5.3 Persistence

SQLite is the persistent source of truth.

Graph and Trie are derived in-memory structures.

Agents must:

- Reconstruct derived structures at startup.
- Keep accepted connections undirected.
- Keep pending requests directed and separate.
- Follow the approved transaction and recovery strategy.
- Never silently serve stale indexes after a failed update.

### 5.4 API consistency

All API changes must follow api.md.

Agents must not:
- Change endpoint methods without approval.
- Rename response fields without approval.
- Introduce frontend-only mock behavior as if it were persisted backend functionality.
- Return sensitive database fields.
- Trust user IDs supplied by the frontend for authenticated actions.

## 6. UI and Design Rules

The approved design direction is:

**Premium Social Networking × Professional Student Community**

### Typography

- Newsreader: display and headline typography.
- Manrope: functional interface and body typography.

### Approved palette

| Name | Hex |
|---|---|
| Iron Grey | `#3E4E50` |
| Ash Grey | `#C6D8D3` |
| Deep Crimson | `#8E151F` |
| Vivid Tangerine | `#FF7F11` |
| Shadow Grey | `#272838` |
| Warm Porcelain | `#F5F2EA` |
| Soft Sand | `#E7DCCB` |

Agents must:

- Follow design.md rather than inventing another visual identity.
- Preserve responsive behavior.
- Avoid generic dashboard templates.
- Avoid unnecessary gradients, excessive shadows, and decorative clutter.
- Use consistent spacing and reusable components.
- Design meaningful loading, empty, error, and success states.
- Keep accessibility and readable contrast in mind.

Do not introduce optional social features as mandatory product functionality.

## 7. Coding Standards

### Frontend

- Use reusable React components.
- Keep API communication in service modules.
- Avoid oversized components with unrelated responsibilities.
- Use clear component and variable names.
- Handle asynchronous loading and errors.
- Avoid hardcoded production API URLs.
- Keep secrets out of frontend source code.

### Backend

- Use clear route, service, repository, and DSA boundaries.
- Validate all incoming data server-side.
- Use parameterized SQL queries.
- Use transactions for multi-record operations.
- Handle exceptions explicitly.
- Avoid unnecessary global mutable state.
- Keep application configuration outside business logic.

### Python

- Use descriptive function and variable names.
- Add type hints where useful.
- Keep functions focused.
- Add docstrings to important algorithms and service functions.
- Explain non-obvious complexity or implementation choices.
- Avoid excessive abstraction for simple operations.

## 8. Security Rules

Agents must:

- Hash passwords using an established password-hashing implementation.
- Use server-managed sessions.
- Protect state-changing session-authenticated operations against CSRF.
- Apply authorization checks on every protected operation.
- Never expose password hashes or session identifiers.
- Validate all user input.
- Use secure cookie settings in production.
- Keep secrets in environment configuration.
- Avoid logging credentials or sensitive session data.

Security must not depend on frontend validation.

## 9. Development Workflow

Agents must follow this sequence for every implementation task:

1. Read the relevant approved documents.
2. Inspect the existing code before editing.
3. Identify affected modules and dependencies.
4. Define the smallest implementation plan.
5. Implement the required change.
6. Run relevant tests.
7. Check for regressions.
8. Review the final changes against the requirements.
9. Report modified files, verification results, and unresolved issues.

Do not rewrite entire modules when a targeted change is sufficient.

Do not overwrite existing working functionality without a clear reason.

## 10. Change Management

Before making a change, classify it:

| Change type | Action |
|---|---|
| Bug fix within approved requirements | Implement and test |
| Internal refactoring without behavior change | Implement and verify |
| UI refinement within design specification | Implement and verify |
| API contract modification | Request approval |
| Database schema modification | Request approval and migration plan |
| New feature | Check PRD scope and obtain approval |
| Architecture modification | Request approval and document impact |
| Technology replacement | Explicit approval required |

Frozen documents must not be silently edited.

Any approved change to a frozen document requires a new version and an explanation of the change.

## 11. Testing Responsibilities

Every agent must verify the behavior it changes.

Minimum expectations:

### DSA
- Graph edge invariants.
- BFS shortest-path correctness.
- Trie prefix lookup.
- Heap ordering.

### Backend
- Input validation.
- Authentication and authorization.
- Database transactions.
- Connection request lifecycle.
- Error responses.

### Frontend
- Component rendering.
- API integration.
- Loading and error states.
- Responsive layout.
- User interaction behavior.

### Integration
- Registration and login.
- Profile updates.
- Connection request acceptance.
- Feed retrieval.
- Search.
- Restart persistence.

Never claim tests passed if they were not executed.

## 12. Prohibited Practices

Agents must not:

1. Invent requirements.
2. Silently change frozen documents.
3. Replace required custom DSA implementations with external libraries.
4. Introduce unnecessary dependencies.
5. Use mock data as a substitute for completed backend integration.
6. Hardcode credentials or secrets.
7. Bypass authentication or authorization.
8. Ignore failed tests.
9. Delete existing functionality without approval.
10. Claim implementation is complete without verification.
11. Generate large amounts of unexplained code.
12. Make unrelated changes outside the assigned task.

## 13. Agent Reporting Format

After completing a task, report:

**Task:** What was implemented.

**Files changed:** Exact files modified or created.

**Implementation:** How the change works.

**Verification:** Tests and commands actually executed, with results.

**Known issues:** Remaining bugs, limitations, or blockers.

**Documentation impact:** Whether any approved document requires a versioned update.

**Next dependency:** What must happen before the next implementation step.

## 14. Definition of Done

A task is complete only when:

- [ ] It satisfies the assigned requirement.
- [ ] It follows the approved architecture.
- [ ] It respects the database and API contracts.
- [ ] It does not break existing functionality.
- [ ] Relevant tests pass.
- [ ] Errors are handled appropriately.
- [ ] Security requirements are respected.
- [ ] Code is understandable and explainable.
- [ ] Changes are reported accurately.
- [ ] Required documentation updates are identified.

---

## Document Control

**Document ID:** CC-AGT-006  
**Version:** 1.0  
**Status:** DRAFT — AWAITING APPROVAL  
**Governing baseline:** PRD.md v1.0, design.md v1.1, architecture.md v1.1, database.md v1.1, api.md v1.0

This document defines implementation behavior for AI agents and developers. It does not expand the approved product scope.