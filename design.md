# CampusConnect — Design System & UX Specification

**Document ID:** CC-DES-002  
**Version:** 1.1 — Revised Draft  
**Status:** Awaiting Approval  
**Product:** CampusConnect  
**Governing document:** PRD.md v1.0

---

# 1. Product Design Vision

CampusConnect is a student networking and social discovery platform combining the engaging experience of Instagram with the professional identity and networking functionality of LinkedIn.

The product must balance three dimensions:

1. Social engagement — students share ideas, discover content and interact with their community.
2. Professional identity — students showcase academic backgrounds, skills, projects and achievements.
3. Network discovery — students discover peers, understand mutual relationships and build meaningful connections.

## Design positioning

**Premium Social Networking × Professional Student Community**

The product should feel:
- Modern and sophisticated.
- Social but not childish.
- Professional but not corporate.
- Expressive but not visually chaotic.
- Information-rich but not overwhelming.

The design must be recognizable as CampusConnect rather than a reskinned copy of another social platform.

# 2. Brand Identity

## Brand name
CampusConnect

## Brand personality
- Sophisticated.
- Creative.
- Intellectual.
- Approachable.
- Contemporary.
- Confident.

## Brand messaging direction

Suggested brand statement:

"Your people. Your ideas. Your next opportunity."

The product should communicate the value of connecting students, discovering talent and sharing knowledge.

# 3. Approved Colour System

## Core palette

| Colour | Hex | Usage |
|---|---|---|
| Iron Grey | #3E4E50 | Structural surfaces |
| Ash Grey | #C6D8D3 | Muted panels |
| Deep Crimson | #8E151F | Editorial emphasis |
| Vivid Tangerine | #FF7F11 | Signature accent and primary actions |
| Shadow Grey | #272838 | Primary text and dark surfaces |

## Supporting neutrals

| Colour | Hex | Usage |
|---|---|---|
| Warm Porcelain | #F5F2EA | Primary canvas |
| Soft Sand | #E7DCCB | Secondary surfaces |

## Colour application

Warm Porcelain should dominate the main interface.

Shadow Grey should provide readable typography and structural contrast.

Vivid Tangerine should identify important actions and selected highlights.

Deep Crimson should remain a restrained accent.

Ash Grey and Soft Sand should establish surface variation.

Do not make every component orange. The accent must remain meaningful.

## Accessibility

Target WCAG 2.2 AA:
- Normal text contrast: 4.5:1.
- Large text contrast: 3:1.
- Meaningful controls and graphical elements: 3:1 target.
- Visible focus indicators.
- Never communicate state through colour alone.

# 4. Typography System

**Status: FINALIZED**

## Display typography — Newsreader

Usage:
- Hero headlines.
- Main page headings.
- Editorial section headings.
- Featured statements.
- Selected promotional content.

Approved weights:
- 400.
- 500.
- 600 where available.

Italic styles may be used for selective editorial emphasis.

## Interface typography — Manrope

Usage:
- Navigation.
- Buttons.
- Search.
- Student profiles.
- Feed content.
- Forms.
- Metadata.
- Notifications and supporting information.

Approved weights:
- 400.
- 500.
- 600.
- 700.

## Typography hierarchy

| Element | Desktop | Mobile |
|---|---:|---:|
| Hero headline | 56–72px | 36–44px |
| Page heading | 36–44px | 28–34px |
| Section heading | 24–30px | 21–26px |
| Card heading | 18–22px | 17–20px |
| Body | 15–17px | 14–16px |
| Supporting text | 13–14px | 12–13px |
| Metadata | 11–12px | 11–12px |

Newsreader is for visual identity. Manrope is for everyday usability.

Avoid excessive serif usage inside dense feed content.

# 5. Design Principles

## 5.1 Content first

The home feed is the primary destination.

Content must be readable, easy to scan and visually organized.

## 5.2 Identity first

Student profiles must communicate personality and academic credibility.

A student should be able to understand who someone is, what they study, what they can do and what they are interested in.

## 5.3 Discovery without friction

Searching and discovering other students should require minimal navigation.

## 5.4 Visual consistency

All application screens must use the same colour, typography, spacing and component rules.

## 5.5 Meaningful interactions

Buttons, menus, connection actions and search results must perform real functions.

# 6. Application Information Architecture

## Primary navigation

1. Home.
2. Discover.
3. Connections.
4. Requests.
5. My Profile.

Search should be globally accessible.

Account settings and logout should be accessible through the account menu.

## Desktop layout

Recommended structure:

- Left navigation: persistent application navigation.
- Centre content: main feed, discovery results or selected screen.
- Right contextual panel: suggested students, mutual network information and relevant discovery content.

The right panel must adapt to the active page rather than display irrelevant information everywhere.

## Mobile layout

- Compact top navigation.
- Full-width main content.
- Bottom navigation.
- Accessible search.
- Appropriate touch targets.
- Responsive profile sections.

Do not compress the desktop layout into mobile.

# 7. Home Feed UX

**Priority: Highest**

The home feed must combine social content discovery with professional and academic updates.

## Feed composition

### A. Welcome section
- Brief personalized greeting.
- Contextual introductory statement.
- Access to discovery.

### B. Post composer
- Current student's identity.
- Text input.
- Post creation action.
- Clear submission state.

### C. Main feed
Each post should contain:
- Author identity.
- Profile navigation.
- Academic context where relevant.
- Timestamp.
- Post content.
- Appropriate visual hierarchy.

### D. Contextual discovery
Suggested students and network information may appear in the supporting desktop column.

## Feed behavior

- Display posts from accepted connections.
- Newest-first ordering.
- Clear empty state.
- Loading feedback.
- Error recovery.
- Actual backend data.

## Optional future interactions

Likes, comments, replies and image posts may be incorporated later, subject to PRD scope approval.

Do not represent these as mandatory baseline functionality.

# 8. Discover Experience

The Discover page should be one of the strongest parts of the product.

It must make finding people feel intuitive and useful.

## Discover components

- Search field.
- Prefix-based suggestions.
- Student directory.
- Recommended students.
- Student identity cards.
- Programme and academic year.
- Skills.
- Mutual connections.
- Connection status.
- Profile navigation.

## Student discovery card

A student card should prioritize:
1. Name and profile identity.
2. Programme and year.
3. Skills and interests.
4. Mutual connections.
5. Connection action.

Avoid displaying excessive information on every card.

## Search behavior

- Support name and username prefixes.
- Show relevant suggestions.
- Handle no-result cases.
- Distinguish existing connections and pending requests.
- Avoid fabricated search results.

# 9. Student Profile Experience

The profile is a combination of social identity and professional portfolio.

## Profile hierarchy

### Identity section
- Profile image or initials fallback.
- Full name.
- Programme.
- Academic year.
- Short bio.
- Connection status.

### Academic and professional information
- Skills.
- Interests.
- Projects and technical contributions through posts.

### Network information
- Accepted connections.
- Mutual connections.
- Connection degree and path where relevant.

### Content section
- Student's posts.
- Chronological presentation.

## Profile variants

Own profile:
- Edit profile.
- View own posts.
- Manage personal information.

Other student's profile:
- Connect or manage connection.
- View public profile information.
- View mutual connections.
- View posts.

Do not add unapproved privacy settings or profile fields as mandatory requirements.

# 10. Connections and Requests

## Connections

Display accepted relationships.

Include:
- Student identity.
- Programme and year.
- Profile access.
- Remove connection action.

## Incoming requests

Display:
- Request sender.
- Profile access.
- Accept action.
- Reject action.

## Outgoing requests

Display:
- Recipient identity.
- Pending state.
- Cancel action.

Incoming and outgoing requests must be visually distinguishable.

Provide confirmation before destructive actions.

# 11. Network Exploration

This section communicates CampusConnect's distinctive graph functionality.

It must present:
- Mutual connections.
- Suggested connections.
- Degree of connection.
- Shortest connection chain.

## Path presentation

A readable path should show the sequence of students connecting the source and destination.

A visual graph may be included as a secondary visualization.

Requirements:
- Use actual backend data.
- Never invent relationships.
- Display the shortest path returned by the backend.
- Handle users with no available path.
- Provide a textual equivalent to visual representations.

# 12. Component System

Build a consistent reusable component library.

## Navigation
- Desktop sidebar.
- Mobile navigation.
- Search trigger.
- Account menu.
- Active navigation state.

## Identity
- Avatar.
- Student identity block.
- Student profile card.
- Skill tags.

## Feed
- Post composer.
- Post item.
- Author information.
- Timestamp.
- Feed loading state.

## Discovery
- Search field.
- Autocomplete.
- Student result card.
- Recommendation section.

## Networking
- Connect button.
- Pending request state.
- Accept/reject controls.
- Mutual connection indicator.
- Connection path display.

## Common components
- Buttons.
- Inputs.
- Modals.
- Toasts.
- Empty states.
- Error states.
- Loading skeletons.

All components must support appropriate interaction states.

# 13. Layout and Spacing

Use a 4px base spacing system.

| Token | Value |
|---|---:|
| space-1 | 4px |
| space-2 | 8px |
| space-3 | 12px |
| space-4 | 16px |
| space-5 | 20px |
| space-6 | 24px |
| space-8 | 32px |
| space-10 | 40px |
| space-12 | 48px |
| space-16 | 64px |
| space-20 | 80px |
| space-24 | 96px |

## Grid

Desktop:
- 12-column grid.
- Maximum content width approximately 1440px.
- Horizontal gutters of 32–48px.

Mobile:
- 4-column conceptual grid.
- Horizontal gutters of 16–20px.

## Radius

| Element | Radius |
|---|---:|
| Small controls | 6px |
| Buttons | 8px |
| Inputs | 8px |
| Standard cards | 12px |
| Featured cards | 16px |
| Modals | 18px |

Avoid excessive pill shapes and unnecessary card borders.

# 14. Motion and Interactions

Motion must be purposeful.

Recommended starting durations:

| Interaction | Duration |
|---|---:|
| Hover/focus | 120–180ms |
| Button interaction | 120–160ms |
| Dropdown | 150–200ms |
| Modal | 180–240ms |
| Page transition | 180–250ms |

Respect reduced-motion preferences.

Avoid excessive parallax, continuous animation and decorative effects that interfere with content consumption.

# 15. Responsive Design

| Category | Width |
|---|---:|
| Small mobile | Below 480px |
| Large mobile | 480–767px |
| Tablet | 768–1023px |
| Laptop | 1024–1439px |
| Desktop | 1440px+ |

Requirements:
- Responsive navigation.
- No horizontal overflow.
- Readable feed.
- Appropriate touch targets.
- Adaptable profile composition.
- Search suggestions constrained to viewport.
- Contextual panels hidden or repositioned when necessary.

# 16. Accessibility

Target WCAG 2.2 AA.

- Semantic HTML.
- Keyboard-operable controls.
- Accessible labels.
- Visible focus states.
- Adequate contrast.
- Reduced-motion support.
- Meaningful error feedback.
- Text alternatives for visual information.

# 17. Content and Interface States

Every data-driven page must support:

Loading:
- Skeletons or appropriate loading indicators.

Empty:
- Clear explanation.
- Relevant next action.

Error:
- Understandable feedback.
- Retry where applicable.

Success:
- Immediate confirmation.
- Updated interface state.

Disabled:
- Clearly communicated restrictions.

Suggested interface messages:
- "Your network is quiet. Discover students to get started."
- "No students found for this search."
- "Connection request sent."
- "You're now connected."
- "No connection path found between these students."

# 18. Implementation Guidelines

- Use centralized design tokens.
- Use Newsreader and Manrope consistently.
- Build reusable React components.
- Use Lucide icons consistently.
- Avoid excessive third-party UI dependencies.
- Keep typography and colour configuration centralized.
- Use real API data.
- Never fabricate users or connections.
- Keep all visible controls functional.
- Do not introduce unapproved brand colours.

# 19. Visual Quality Assurance

Verify:
- Brand consistency.
- Typography hierarchy.
- Feed readability.
- Profile clarity.
- Discovery usability.
- Navigation consistency.
- Responsive behavior.
- Contrast.
- Keyboard navigation.
- Loading, empty and error states.
- Functional controls.
- Real backend integration.

# 20. Design Acceptance Criteria

The design is ready for implementation when:

1. The social and professional identity is balanced.
2. Home feed composition is defined.
3. Student discovery is defined.
4. Profiles communicate academic and professional identity.
5. Connections and requests have distinct states.
6. Graph exploration is clearly presented.
7. Approved colour and typography systems are implemented.
8. Responsive layouts are established.
9. Reusable components are specified.
10. Accessibility and visual QA requirements are satisfied.

# 21. Finalized Decisions and Open Items

| Decision | Status |
|---|---|
| Product design direction | Approved |
| Core colour palette | Approved |
| Supporting neutrals | Approved |
| Display font: Newsreader | Approved |
| Interface font: Manrope | Approved |
| Typography hierarchy | Approved |
| Desktop information architecture | Approved as design direction |
| Mobile navigation direction | Approved as design direction |
| Spacing system | Approved |
| Radius system | Approved |
| Icon system | Lucide recommended |
| Animation library | Open |
| Component library | Open |
| Final logo artwork | Open |
| Detailed wireframes | To be produced during implementation |

# 22. Document Governance

This document is governed by PRD.md v1.0.

It does not change the mandatory functional requirements or introduce optional social interactions into the baseline.

Any changes to mandatory scope must be approved through PRD change control.

**END OF DOCUMENT — design.md**

Document ID: CC-DES-002  
Version: 1.1 — Revised Draft  
Status: Awaiting project-owner approval  
Next document: architecture.md
