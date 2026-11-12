# CAMPUSCONNECT

## Product Requirements Document (PRD)

**Document ID:** CC-PRD-001
**Version:** 1.0 — Draft for Review
**Status:** Awaiting Approval
**Project Category:** Data Structures and Algorithms Mini Project
**Institution:** Chanakya University, Bangalore
**Academic Year:** 2026–27
**Semester:** III Semester, B.Tech.
**Development Mode:** Individual implementation
**Primary Language for Core Engine:** Python

---

# 1. Executive Summary

CampusConnect is a university-exclusive student networking application designed to help students share technical ideas, showcase projects, discover peers and establish meaningful academic connections.

Inspired by the networking concepts of LinkedIn and the community-oriented experience of Instagram, CampusConnect provides students with a platform to create profiles, publish technical content, discover other students and navigate their academic network.

The distinguishing feature of CampusConnect is its underlying Data Structures and Algorithms engine.

Rather than relying on database queries or external graph-processing libraries for network calculations, the application maintains an in-memory graph implemented in Python. It uses appropriate data structures and algorithms to support connection management, shortest connection paths, recommendations, prefix-based search and feed generation.

The project will combine a functional user interface with a modular Python backend, ensuring that the core DSA engine remains independent of the presentation layer.

**Primary objective:** Build a functional student networking application that demonstrates meaningful, correct and explainable implementation of Data Structures and Algorithms.

# 2. Problem Statement

University students frequently work on technical projects, develop individual interests and seek opportunities to collaborate with other students.

However, discovering students with similar interests, understanding mutual connections and navigating relationships across a university community can be difficult without a centralized networking platform.

CampusConnect addresses this problem by providing:

- Student identity and profile management.
- Student-to-student networking.
- Technical project and idea sharing.
- Connection-based discovery.
- Mutual connection identification.
- Network-based recommendations.
- Search and autocomplete.
- A personalized feed containing posts from accepted connections.

The application also demonstrates how fundamental data structures and algorithms can support real-world application functionality.

# 3. Product Vision

To create a connected university ecosystem where students can discover people, share knowledge, showcase technical work and build meaningful academic relationships.

### Product positioning

CampusConnect is a student networking platform with an algorithm-driven connection engine.

It is not intended to be a generic social media clone. Its core identity is based on university networking, technical discovery and meaningful connections.

# 4. Project Objectives

## 4.1 Primary objectives

1. Develop a functional networking application for university students.
2. Implement a graph-based student connection network.
3. Demonstrate BFS-based shortest-path and degree-of-connection calculations.
4. Implement efficient student lookup and prefix-based search.
5. Generate a personalized feed from accepted connections.
6. Provide persistent storage across application restarts.
7. Maintain a clear separation between the DSA engine and the user interface.
8. Produce an implementation that can be independently understood and explained during evaluation.

## 4.2 Secondary objectives

- Establish a distinctive visual identity.
- Provide an intuitive student networking experience.
- Keep the application modular and maintainable.
- Make the architecture extensible for optional enhancements.

# 5. Target Users and Actors

## 5.1 Primary user — Student

A university student who uses CampusConnect to establish an academic identity and connect with peers.

The student can:

- Register and authenticate.
- Create and manage a profile.
- Discover other students.
- Send and manage connection requests.
- View connections and mutual connections.
- Explore recommended students.
- View connection paths.
- Publish technical posts.
- Search students.
- Browse the connection-based feed.

## 5.2 Project evaluator

The faculty evaluator assesses:

- Correctness of the core engine.
- Appropriate data structure selection.
- Algorithm implementation.
- Application functionality.
- Code organization.
- Understanding of the project and its implementation.

No separate evaluator-facing application role is specified by the assignment.

# 6. Scope Definition

## 6.1 Mandatory scope

The application must implement all six areas specified in the assignment:

1. Accounts.
2. Connections.
3. Posts and feed.
4. Search.
5. Persistence.
6. Interface.

## 6.2 Optional enhancements

The following are explicitly categorized as good-to-have enhancements in the assignment:

- Image posts.
- Likes and comments, including replies to comments.
- Notifications for connection requests, likes and comments.
- Trending posts among connections.
- Groups or communities of closely connected students.

These features are not part of the mandatory baseline.

They must only be introduced after the mandatory requirements are functional.

# 7. Functional Requirements

## FR-01: Account Management

**Priority:** Mandatory

The system must support student registration and authentication.

### Requirements

- FR-01.1: Students must be able to register using a unique username and password.
- FR-01.2: Duplicate usernames must be rejected.
- FR-01.3: Students must be able to log in.
- FR-01.4: Students must be able to log out.
- FR-01.5: Passwords must be stored only in hashed form.
- FR-01.6: Plaintext passwords must never be stored.
- FR-01.7: Each student must have an individual profile.

### Student profile attributes

| Attribute | Description                            |
| --------- | -------------------------------------- |
| Name      | Student's full name                    |
| Programme | Academic programme                     |
| Year      | Current academic year                  |
| Short bio | Brief personal or academic description |
| Skills    | Technical and personal skills          |

- FR-01.8: Other students must be able to view a student's profile.

## FR-02: Connection Management

**Priority:** Mandatory

The application must maintain a network of students and their accepted relationships.

### Connection operations

- FR-02.1: A student can send a connection request.
- FR-02.2: A recipient can accept a request.
- FR-02.3: A recipient can reject a request.
- FR-02.4: A sender can cancel a pending request.
- FR-02.5: Either participant can remove an existing accepted connection.
- FR-02.6: Students can view their accepted connections.
- FR-02.7: Students can view mutual connections shared with another student.
- FR-02.8: The application must display a People You May Know list.
- FR-02.9: Recommendations must be ranked using a selected similarity measure.
- FR-02.10: The application must display the degree of connection to another student.
- FR-02.11: The application must display one shortest chain of connections between two students.

### Graph representation

The student network must be modelled as:

G(V, E)

Where:

- V represents students.
- E represents accepted connections.

Each student is a vertex.

Each accepted connection is an undirected edge.

Pending connection requests are directed relationships from sender to recipient until accepted or rejected.

### Graph constraints

- No self-edges.
- No duplicate accepted edges.
- Accepted connections must be symmetric.
- Pending requests must not be treated as accepted connections.
- Graph data must be stored using adjacency lists.

## FR-03: Posts and Feed

**Priority:** Mandatory

Students must be able to publish technical content and view posts from their accepted connections.

### Post operations

- FR-03.1: Students can create text posts about projects or technical ideas.
- FR-03.2: Students can view their own posts.
- FR-03.3: Students can delete their own posts.
- FR-03.4: Students must not be able to delete another student's posts.

### Feed requirements

- FR-03.5: The application must provide a home feed.
- FR-03.6: The feed must contain posts from accepted connections.
- FR-03.7: Posts must be arranged in newest-first order.

### Algorithm consideration

The assignment suggests merging time-ordered connection post streams using a heap.

The implementation should use an actual heap-based merging algorithm if this approach is selected.

A simple global sort must not be presented as a heap-based implementation.

## FR-04: Student Search

**Priority:** Mandatory

Students must be able to discover other students using name or username.

### Requirements

- FR-04.1: Search students by full name.
- FR-04.2: Search students by username.
- FR-04.3: Display suggestions while the user types.
- FR-04.4: Support prefix-based search.
- FR-04.5: Display matching students.

### Algorithm consideration

A Trie is the suggested data structure for prefix-based name search.

The exact indexing and matching behavior must be documented during technical design.

## FR-05: Data Persistence

**Priority:** Mandatory

All application data must survive an application restart.

### Requirements

- FR-05.1: Persist user account information.
- FR-05.2: Persist profile information.
- FR-05.3: Persist accepted connections.
- FR-05.4: Persist pending connection requests.
- FR-05.5: Persist posts.
- FR-05.6: Restore the application's required state after restart.

### Storage constraints

The assignment permits any storage approach and recommends:

- SQLite.
- JSON files.
- MongoDB.

The selected implementation direction is SQLite.

**Critical constraint:** Storage must only maintain persistent data. All graph computations, including suggestions, degrees, paths and feed calculations, must run in Python using in-memory data structures, not through database queries.

## FR-06: User Interface

**Priority:** Mandatory

The application must provide a functional user interface.

The assignment permits:

- Flask.
- Streamlit.
- React.
- Similar frameworks.

A console-based menu application is also acceptable as a minimum interface.

### Selected implementation direction

- Frontend: React.
- Backend: Flask.
- Communication: REST API.

This selection is a project decision, not an explicit assignment mandate.

### Interface requirements

- Account registration and login.
- Student profiles.
- Student discovery.
- Connection management.
- Posts and home feed.
- Search and suggestions.
- Connection degree and shortest path presentation.

All displayed actions must correspond to actual application functionality.

# 8. Data Structures and Algorithms Requirements

This section is particularly important because the assignment allocates 30 marks to Core Engine and DSA Usage and 40 marks to Understanding and Viva.

## 8.1 Required graph model

| Element             | Representation        |
| ------------------- | --------------------- |
| Student             | Graph vertex          |
| Accepted connection | Undirected edge       |
| Pending request     | Directed relationship |
| Graph storage       | Adjacency list        |

## 8.2 Algorithm and data structure mapping

The assignment provides examples of appropriate data structure usage, but explicitly states that these examples are not mandatory rules.

The following is the proposed implementation mapping.

| Application functionality     | Proposed DSA                |
| ----------------------------- | --------------------------- |
| Student network               | Graph using adjacency lists |
| Shortest connection chain     | BFS                         |
| Degree of connection          | BFS                         |
| Pending requests              | Queue                       |
| Notifications, if implemented | Queue                       |
| Home feed                     | Heap                        |
| User lookup                   | Hash table                  |
| Name prefix search            | Trie                        |
| Undo and back navigation      | Stack                       |

Each selected structure must be justified based on its actual application use.

## 8.3 Recommendation algorithm

The assignment allows the developer to choose the ranking measure.

Two examples are provided:

- Jaccard's coefficient: overlap of neighbourhoods.
- Katz's score: number of paths between users, weighted by path length.

The final selection must be made during technical design.

The selected recommendation algorithm must:

- Exclude the current user.
- Exclude existing direct connections.
- Consider relevant network relationships.
- Produce a meaningful ranking.
- Be explainable during evaluation.

## 8.4 Algorithm independence

The core engine must be independent of the interface.

The same Python functions should be callable from either a console interface or a web frontend.

If React is used, the assignment recommends exposing the core through a small REST API in Flask or FastAPI.

# 9. User Journey Requirements

These journeys describe expected application behavior. They are not a commitment to a particular screen layout.

## Journey 1: Student registration

1. Student opens the application.
2. Student selects registration.
3. Student enters a unique username and password.
4. System validates the credentials.
5. Password is hashed and stored.
6. Student can log in.
7. Student can create or complete their profile.

## Journey 2: Discover and connect

1. Student opens the discovery section.
2. Student searches for another student or explores suggestions.
3. Student opens the selected profile.
4. Student sends a connection request.
5. Recipient receives or views the pending request.
6. Recipient accepts or rejects it.
7. If accepted, the graph is updated with an undirected edge.

## Journey 3: Explore network relationships

1. Student opens another student's profile.
2. Student views mutual connections.
3. Student checks the degree of connection.
4. System computes a shortest chain using the graph.
5. Application displays the resulting connection path.

## Journey 4: Publish technical content

1. Student opens the post composer.
2. Student writes a technical idea or project update.
3. Student publishes the post.
4. The post is persisted.
5. The post becomes visible in the appropriate feed.

## Journey 5: Search students

1. Student opens search.
2. Student enters a name or username prefix.
3. Application provides matching suggestions.
4. Student selects a result.
5. Application opens the corresponding profile.

## Journey 6: Feed consumption

1. Student opens the home feed.
2. System retrieves relevant posts from accepted connections.
3. Python feed logic merges the time-ordered streams.
4. The feed displays posts newest first.

# 10. Non-Functional Requirements

The assignment does not provide a formal non-functional requirements list. The following are proposed engineering quality requirements.

| ID     | Requirement     | Description                                                                |
| ------ | --------------- | -------------------------------------------------------------------------- |
| NFR-01 | Security        | Passwords must be hashed and sensitive data protected.                     |
| NFR-02 | Data integrity  | Accepted and pending connection states must remain consistent.             |
| NFR-03 | Persistence     | Data must survive application restarts.                                    |
| NFR-04 | Modularity      | Core DSA logic must remain separate from the interface.                    |
| NFR-05 | Maintainability | Code must have meaningful structure and comments.                          |
| NFR-06 | Usability       | Mandatory operations must be accessible through the UI.                    |
| NFR-07 | Reliability     | Invalid operations must be handled without application crashes.            |
| NFR-08 | Explainability  | The implementation must be understandable to the student presenting it.    |
| NFR-09 | Responsiveness  | The selected web interface should adapt to different screen sizes.         |
| NFR-10 | Consistency     | Persistent records and derived in-memory indexes must remain synchronized. |

# 11. Product Design Direction

**Design identity:** Industrial Editorial × Contemporary Campus Culture.

The application should have a distinctive, premium and editorial appearance without sacrificing usability.

### Agreed colour palette

| Name            | Hex code  |
| --------------- | --------- |
| Iron Grey       | `#3E4E50` |
| Ash Grey        | `#C6D8D3` |
| Deep Crimson    | `#8E151F` |
| Vivid Tangerine | `#FF7F11` |
| Shadow Grey     | `#272838` |
| Warm Porcelain  | `#F5F2EA` |
| Soft Sand       | `#E7DCCB` |

### Typography

Not finalized.

The final typography system must be approved separately after visual comparisons in actual application screens.

### Design expectations

- Distinctive typography.
- Editorial visual hierarchy.
- Premium spacing and composition.
- Consistent components.
- Restrained colour usage.
- Responsive layouts.
- Meaningful transitions and interactions.
- No decorative controls that do not work.

Detailed design specifications will be maintained in `design.md`.

# 12. Technical Constraints and Decisions

## 12.1 Assignment-derived constraints

1. The network must use adjacency lists.
2. Accepted connections are undirected.
3. Pending requests are directed.
4. There must be no self-edges or multiple edges.
5. All graph computations must run in Python memory.
6. All data must survive application restart.
7. Core engine and interface must be separate.
8. Students must be able to explain submitted code.
9. Code must include meaningful comments and a brief design description.

## 12.2 Proposed technical decisions

| Layer          | Proposed selection            | Status                                  |
| -------------- | ----------------------------- | --------------------------------------- |
| Frontend       | React + Vite                  | Proposed                                |
| Backend        | Python Flask                  | Proposed                                |
| API            | REST                          | Proposed                                |
| Persistence    | SQLite                        | Proposed                                |
| Graph          | Custom Python adjacency lists | Assignment requirement                  |
| Shortest path  | BFS                           | Proposed                                |
| Search         | Custom Trie                   | Proposed                                |
| Feed merging   | Heap                          | Proposed                                |
| Authentication | Secure password hashing       | Hashing is required; method to finalize |

The selected stack must be confirmed in the architecture document.

# 13. Project Scope Exclusions

The following are outside the mandatory baseline:

- Real-time chat.
- Video calls.
- AI-powered recommendations.
- Machine-learning-based student matching.
- External social media integrations.
- University single sign-on.
- Payment functionality.
- Production-grade enterprise deployment.

These exclusions do not prohibit future expansion, but they must not distract from the assignment requirements.

# 14. Project Risks and Mitigation

| Risk                              | Impact | Mitigation                                       |
| --------------------------------- | ------ | ------------------------------------------------ |
| Incomplete DSA implementation     | High   | Build and test core algorithms independently     |
| Incorrect graph updates           | High   | Enforce symmetric accepted-edge invariants       |
| Database and memory inconsistency | High   | Define transaction and index-update behavior     |
| Overengineering optional features | High   | Prioritize mandatory requirements                |
| Poor code explainability          | High   | Document algorithms and implementation decisions |
| UI consumes development time      | Medium | Establish design system before page development  |
| Incomplete integration            | High   | Integrate incrementally                          |
| Inadequate testing                | High   | Maintain algorithm and workflow test coverage    |

# 15. Dependencies

The project depends on:

- Python environment.
- Frontend development environment.
- Backend framework.
- Database initialization.
- Core DSA implementation.
- REST API integration.
- Functional interface.
- Testing and validation.

External services are not required by the assignment.

# 16. Acceptance Criteria

The project is considered functionally complete when the following mandatory conditions are satisfied.

### Accounts

- [ ] Unique username registration.
- [ ] Login and logout.
- [ ] Passwords stored only as hashes.
- [ ] Student profiles created and viewable.

### Connections

- [ ] Send, accept, reject and cancel requests.
- [ ] Remove accepted connections.
- [ ] View connections.
- [ ] View mutual connections.
- [ ] Display ranked recommendations.
- [ ] Display degree of connection.
- [ ] Display one shortest connection chain.
- [ ] Graph uses adjacency lists.
- [ ] Correct directed and undirected relationship behavior.

### Posts and feed

- [ ] Create text posts.
- [ ] View own posts.
- [ ] Delete own posts.
- [ ] Connection-based home feed.
- [ ] Newest-first ordering.

### Search

- [ ] Search by name.
- [ ] Search by username.
- [ ] Prefix suggestions.

### Persistence

- [ ] All relevant data survives restart.
- [ ] Graph calculations run in Python memory.

### Interface

- [ ] Functional interface.
- [ ] Core engine separated from UI.
- [ ] React frontend communicates with Python backend if the selected web stack is retained.

### Academic readiness

- [ ] Meaningful code comments.
- [ ] Brief design description.
- [ ] Appropriate DSA justification.
- [ ] Implementation can be explained during viva.

# 17. Evaluation Alignment

The project must be developed with the assignment's marking structure in mind.

| Evaluation category       |   Marks | Development implication                   |
| ------------------------- | ------: | ----------------------------------------- |
| Core Engine and DSA Usage |      30 | Correct data structures and algorithms    |
| Implementation            |      20 | Working application and integration       |
| Report                    |      10 | Accurate documentation                    |
| Understanding and Viva    |      40 | Independent understanding and explanation |
| **Total**                 | **100** |                                           |

The highest combined emphasis is on technical understanding and DSA correctness.

Consequently, implementation must not become a process of blindly generating code without understanding its behavior.

# 18. Assumptions and Open Decisions

The following are not fully specified by the assignment and must be resolved in subsequent documents.

| Decision                    | Current status                                     |
| --------------------------- | -------------------------------------------------- |
| Application name            | CampusConnect — selected project name              |
| Frontend framework          | React + Vite proposed                              |
| Backend framework           | Flask proposed                                     |
| Database                    | SQLite proposed                                    |
| Recommendation measure      | Not finalized                                      |
| Trie implementation details | To be designed                                     |
| Heap feed implementation    | To be designed                                     |
| Hash-table implementation   | To be designed                                     |
| Queue implementation        | To be designed                                     |
| Stack implementation        | To be designed if undo/back navigation is included |
| Authentication mechanism    | To be finalized                                    |
| Typography                  | Not finalized                                      |
| Hosting/deployment          | Not selected                                       |
| Optional enhancements       | Deferred                                           |

### Important deadline clarification

The supplied assignment prints **27 November 2026** as the submission date and three weeks as the total duration.

The separate internal target of 30 November must be confirmed. The assignment date remains the authoritative date in this PRD unless faculty announces a change.

# 19. Document Dependencies

This PRD establishes the baseline for the remaining project documents.

| Document        | Dependency on PRD                             |
| --------------- | --------------------------------------------- |
| design.md       | Product experience and interface requirements |
| architecture.md | System boundaries and stack decisions         |
| database.md     | Persistence and entity requirements           |
| api.md          | Functional operations and service contracts   |
| agents.md       | Implementation rules and constraints          |
| README.md       | Product overview                              |
| plan.md         | Development phases and priorities             |
| setup.md        | Selected development environment              |
| features.md     | Feature inventory and acceptance criteria     |
| auth.md         | Account and security requirements             |
| mcp.md          | Integration necessity and scope               |
| integrations.md | Component communication                       |
| testing.md      | Acceptance criteria and expected behavior     |
| debugging.md    | Known technical invariants and failure modes  |

# 20. PRD Approval Checklist

Before this PRD is frozen, confirm:

- [ ] Product scope correctly represents the assignment.
- [ ] All six mandatory areas are covered.
- [ ] Optional enhancements are correctly separated.
- [ ] DSA examples are not incorrectly represented as mandatory assignment rules.
- [ ] Individual implementation constraints are respected.
- [ ] React + Flask + SQLite are accepted as proposed technology choices.
- [ ] Recommendation algorithm is left open for technical evaluation.
- [ ] Visual direction is accurately represented.
- [ ] Deadline is confirmed.
- [ ] No additional functionality has been silently introduced.

---

**END OF DOCUMENT — PRD.md**

**Document owner:** CampusConnect Project Team / Individual Developer
**Approval status:** Pending project-owner review
**Next document:** `design.md` — Design System and User Experience Specification

