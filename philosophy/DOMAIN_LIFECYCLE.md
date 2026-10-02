---
title: The Domain Lifecycle
layer: philosophy
audience: [agent, human]
stage: stable
---

# The Domain Lifecycle — Process-Centric Architecture

_How Macula models software development as a set of first-class processes._

**Development-process tracking (Domain Lifecycle, Division ALC) is not
event sourced.** Software development is chaotic and non-linear — a plan
gets reopened after being concluded, a design gets revisited mid-build —
which doesn't fit a single-current-state aggregate. Each process's output
is instead a git-tracked artifact, and the human-approval gates that
matter are git commits (or merged PRs): genuinely append-only,
audit-worthy facts, with git log supplying the history for free. This is
scoped to *tracking the building of a domain*; a domain's own production
business logic, once built, stays event sourced by default. **Node
Continuous** (below) was never part of this — a node has no development
process to track, it's just alive.

---

## The Insight

Traditional software tools model development as **data management**: you create projects, update records, delete tasks. The verbs are CRUD, the nouns are passive containers.

Macula models development as a **set of processes**: each phase of building software is its own first-class citizen with its own current state and its own artifact. The verbs are business actions, the nouns are active processes.

**The test:** imagine a human sitting at a desk. What lands on their desk? What do they do with it? What do they pass to the next desk?

If the answer is "they manage a database record" — the model is wrong.
If the answer is "they investigate, decide, produce, and hand off" — the model is right.

---

## Terminology

### Hierarchy

```
Domain (1)
  └── Division (N)        — one per bounded context
       └── Department (3)  — CMD, PRJ, QRY
            └── Desk (N)   — individual capability
```

### Domain Concepts

| Term | What It Is | Old Term |
|------|-----------|----------|
| **Domain** | The overall business endeavor — a conglomerate of divisions | Venture, Torch |
| **Division** | A specialist firm within the domain, responsible for one bounded context | Cartwheel / Company |
| **Department** | CMD, PRJ, or QRY within a division's own production codebase | Department |
| **Desk** | A single capability within a department (where work gets done) | Spoke |
| **Dossier** | The aggregate — the folder of event slips passing through desks. Applies to a division's own production business logic once built, not to tracking the build itself. | Dossier |

### Divisions Are Virtual

A division is a **virtual umbrella** — a logical grouping of apps that share a business context. In practice, it maps to either:

1. **Multiple apps within a shared umbrella**
2. **A separate repo** within the organization

Each division produces N apps following the department pattern:

| Department | Naming | Nature |
|------------|--------|--------|
| CMD | The **process name** itself | Process-centric (verbs) |
| PRJ | `project_{read_model}` | Data-centric (projections) |
| QRY | `query_{read_model}` | Data-centric (queries) |

---

## Three Lifecycle Types

Macula manages three fundamentally different lifecycle types.

### 1. Domain Lifecycle

**Scope:** Per domain. **Duration:** Short inception, long-lived discovery.

A domain's birth and division discovery are tracked as a git-tracked
document — `plans/PLAN_{DOMAIN}_VISION.md`, following this workspace's
established `plans/PLAN_*.md` convention — not as CMD/PRJ/QRY apps:

- **Vision** — Domain Expert drafts, refines, and finalizes a domain
  brief in the plan document. The Vision Gate is the commit (or merged
  PR) that marks it approved.
- **Division Discovery** — Domain Expert identifies bounded contexts and
  records them, with boundary rationale, in the same document. The
  Boundary Gate is the commit that marks the division list approved.

Once divisions are discovered, each follows its own ALC independently
(see `alc/README.md`).

### 2. Division ALC — 2 Processes

**Scope:** Per division. **Duration:** Long-lived, sequential.

Full model in `alc/README.md`. In short: **Planning** produces a plan
document (`plans/PLAN_{DIVISION}.md` in the division's own repo) covering
aggregate design, event list, and desk inventory; **Crafting** produces
the division's own codebase plus its `CHANGELOG.md`. Neither is an
aggregate — each gate (Design, Review, Release) is a git commit or merged
PR, and git log is the audit trail.

### 3. Node Continuous (`guide_node_lifecycle`)

**Scope:** Per node. **Duration:** Indefinite, always-on.

The node lifecycle has no phases and no sub-processes. A node registers, operates forever, and may unpair/re-pair. All desks are independent operations on a living entity:

- `register_identity` — join the mesh
- `configure_node` — set preferences
- `serve_llm` — provide LLM capabilities
- `manage_capabilities` — announce what this node can do
- ...

There is no lifecycle protocol — the node is simply alive and responding to commands. This is the one lifecycle type that was never a candidate for event sourcing in the first place: it isn't tracking a development process, it's a running service.

---

## Coordination

A gate crossing is announced, not orchestrated. Whichever harness makes
the gate-approving commit is responsible for publishing a mesh fact
(e.g. `macula.gate_passed`, with the domain/division id and which gate in
the payload, never the topic). Interested harnesses `mesh_watch` for it
and self-select to pick up the next stage. If two harnesses both act on
the same document, resolution is git's own: whichever pushes or merges
first wins, and the second hits a conflict and backs off. No aggregate,
no process manager, no lock service — the mesh carries the "something
changed, go look" signal, and git carries the state.

See `macula-mcp/plans/PLAN_MARTHA_MULTI_AGENT_MCP.md` for the full
multi-agent design this feeds — there is no backend service that owns
domain/division lifecycle tracking; it's a git-and-mesh convention.

---

## The Guided Conversation Method

### The Protocol

1. **Frame a decision** — Ask a clear, bounded question with no ambiguity
2. **Present options** — Show tradeoffs as a table, not opinions. Include pros AND cons.
3. **User decides** — They own the choice. Never decide for them.
4. **Record the decision** — Write it into the plan document. It becomes a constraint on all future decisions.
5. **Build forward** — Each decision narrows the next decision's option space.
6. **Produce an artifact** — The conversation output is a commit to the plan document, not prose left only in the chat transcript.

### Phase-Specific Conversations

| Phase | Guided Conversation Produces |
|-------|------------------------------|
| Vision | Domain name + brief, written into `plans/PLAN_{DOMAIN}_VISION.md` |
| Division Discovery | Division list with names, descriptions, boundary rationale, in the same document |
| Planning | Aggregates, events, desk inventory, dependencies, in `plans/PLAN_{DIVISION}.md` |
| Crafting | Module generation, test strategy, release manifest — reflected in the codebase and `CHANGELOG.md` |

### The Decision Cascade

Decisions made in earlier phases constrain later phases:

```
vision: name = "my-saas-app"
  └─ constrains discovery scope

discover: divisions = [auth, billing, notify]
  └─ constrains planning: 3 divisions to plan

planning(auth): aggregates = [user, session, credential]
                desks = [register_user, authenticate_user, ...]
  └─ constrains crafting: exactly these desks to implement

crafting(auth): modules generated, tests passed, release delivered
```

Each phase's output is the next phase's input, written into the plan document — not held only in an agent's context window. The conversation at each phase only needs to cover that phase's decisions — everything else is already settled and already written down.

---

*Process-centric architecture. Each phase is a first-class citizen, tracked in git, not event sourced.*
