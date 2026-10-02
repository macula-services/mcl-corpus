---
title: The Task Model
layer: philosophy
audience: [agent, human]
stage: draft
---

# The Task Model — Work as First-Class Citizen

_How Macula surfaces software development as a list of actionable tasks with AI assistance._

Uses `domain`/`domain_id`/`domain_initiated_v1` terminology throughout,
consistent with the Domain/Division/Department/Desk/Dossier model (see
`GLOSSARY.md`). Reconciled against the current 6-role roster
(`roles/AGENT_ARCHITECTURE.md`: Domain Expert, Architect, DevOps, QA,
Reporter, Mentor) and the current 2-process Division ALC
(`alc/README.md`: Planning, Crafting) — see below.
**Status:** Not superseded. This draft's own Insight section already says
it: "The domain model doesn't change... What changes is how the Dev
Studio presents work to the user" — task-centric UX (a task as the
first-class unit, phase as metadata on it) is a still-live idea,
independent of how many phases, processes, or roles exist underneath it.
The Division-Scoped task catalog treats Monitor Division and Rescue
Division as continuous, always-available operational concerns, not
sequential, prerequisite-gated tasks downstream of Deploy Division —
matching `alc/README.md`'s own doctrine that "monitoring, rescue,
debugging, and refactoring are operational concerns, not lifecycle
phases — they happen continuously, not sequentially."
**Origin:** Design conversation on task-centric vs phase-centric UX

---

## The Insight

The Domain Lifecycle (DOMAIN_LIFECYCLE.md) defines the domain-level processes (setup, discovery), and the Division ALC (`alc/README.md`) defines two division-level processes, Planning and Crafting. This is the correct domain model — processes are real, phases are real, divisions are real.

But in the **user experience**, phases are not what the user works with. The user works with **tasks**. A task is a concrete action: "Refine the vision," "Design the Auth Service," "Generate code for the Payment Gateway." The phase is just a property of the task — metadata that determines which AI role assists.

**The shift:**

| Aspect | Phase-Centric (old UX) | Task-Centric (new UX) |
|--------|----------------------|---------------------|
| Navigation | Domain → Phase → Division → act | Domain → Task List → pick a task |
| First-class citizen | The phase | The task |
| Phase role | Container to enter | Tag on a task |
| Division role | Context to switch to | Grouping header in task list |
| AI assistance | Manual role switching | Auto-attached to task type |
| What's blocked | Implicit (user guesses) | Explicit (task shows prerequisites) |

**The domain model doesn't change.** The 10 processes, the domain hierarchy, the CMD/QRY/PRJ departments — all unchanged. What changes is how the Dev Studio presents work to the user.

---

## Task Anatomy

Every task has:

```
┌─────────────────────────────────────────────────┐
│ Task                                            │
├─────────────────────────────────────────────────┤
│ verb        : "design"                          │
│ scope       : domain | division                │
│ subject     : "Auth Service" (division name)    │
│ phase       : division-alc-planning             │
│ ai_role     : Architect                         │
│ state       : pending | active | paused | running | done │
│ blocked_by  : ["submit-vision"]                          │
│ has_chat    : true                                       │
│ has_ui      : true (dedicated task UI)                   │
└──────────────────────────────────────────────────────────┘
```

### Task Lifecycle (Event-Sourced)

Every task follows the same lifecycle protocol. Each transition is an **event** stored in the event stream, giving full audit trail and tracking.

```
                    ┌─────────┐
                    │ pending │
                    └────┬────┘
                         │ start
                         ▼
              ┌──── ┌────────┐ ────┐
              │     │ active │     │
              │     └────┬───┘     │
          resume         │      pause
              │          │         │
              │          │         ▼
              │          │    ┌────────┐
              └──────────┼─── │ paused │
                         │    └────────┘
                         │ complete
                         ▼
                   ┌───────────┐
                   │ completed │
                   └───────────┘
```

**State machine:** `pending → active ⇄ paused → completed`

Each transition emits a versioned event:

| Transition | Event | Example |
|-----------|-------|---------|
| start | `{task}_started_v1` | `refine_vision_started_v1` |
| pause | `{task}_paused_v1` | `design_division_paused_v1` |
| resume | `{task}_resumed_v1` | `refine_vision_resumed_v1` |
| complete | `{task}_completed_v1` | `test_division_completed_v1` |

### Task States

| State | Symbol | Meaning |
|-------|--------|---------|
| **blocked** | `○` (dim) | Prerequisites not met |
| **pending** | `○` | Ready to start, prerequisites met |
| **active** | `●` | User is currently working on this |
| **paused** | `◑` | Started but paused (user can resume) |
| **running** | `◐` | AI is working in background |
| **done** | `✓` | Completed |

A task can be **active** (user is interacting) or **running** (AI background work). Multiple tasks can be **running** simultaneously. **Paused** means the user explicitly stepped away — the event stream records when and for how long.

### Desks per Task (Lifecycle)

Each lifecycle transition is its own **desk** (vertical slice). Every task type gets 4 lifecycle desks:

```
refine_vision/
├── start_refine_vision/       → emits refine_vision_started_v1
├── pause_refine_vision/       → emits refine_vision_paused_v1
├── resume_refine_vision/      → emits refine_vision_resumed_v1
├── complete_refine_vision/    → emits refine_vision_completed_v1

design_division/
├── start_design_division/     → emits design_division_started_v1
├── pause_design_division/     → emits design_division_paused_v1
├── resume_design_division/    → emits design_division_resumed_v1
├── complete_design_division/  → emits design_division_completed_v1
```

Task-specific action desks (chat, confirm, etc.) are separate and only valid when the task is **active**.

---

## The Task Catalog

### Domain-Scoped Tasks

These tasks exist once per domain.

| Task | Verb | AI Role | Prerequisites | Ongoing? |
|------|------|---------|---------------|----------|
| **Initiate Domain** | `initiate-domain` | — | None | No |
| **Refine Vision** | `refine-vision` | Domain Expert | Domain initiated | Yes |
| **Submit Vision** | `submit-vision` | — | Vision refined | No |
| **Refine Divisions** | `refine-divisions` | Domain Expert | Vision submitted | Yes |

**Initiate Domain** — Creates the domain. Name, brief description, scaffolding. This is the birth event. No AI needed — it's a form.

**Refine Vision** — The user and Domain Expert collaborate to shape the domain's vision. What are we building? Why? For whom? What are the constraints? Domain Expert researches first — prior art, similar systems, existing patterns via `mcl-rag`/web search — before opining, then the chat is the work: asking questions, challenging assumptions, helping crystallize the vision. This task is **ongoing**: the user can return to refine further.

**Submit Vision** — Locks the vision. An explicit confirmation action (button, not a task UI). After submission, the vision document becomes the foundation for division discovery.

**Refine Divisions** — The user and Domain Expert explore the business domain together. Through conversation, the AI gradually proposes divisions (bounded contexts). Each proposed division appears with a **[Confirm]** action. Confirming a division spawns its sub-tasks. This task is **ongoing**: the user can always come back to discover more divisions or rethink existing ones.

### Division-Scoped Tasks

These tasks are created when a division is **confirmed** during "Refine Divisions." One set per division.

| Task | Verb | AI Role | Prerequisites | Ongoing? |
|------|------|---------|---------------|----------|
| **Design Division** | `design-division` | Architect | Division confirmed | Yes |
| **Plan Division** | `plan-division` | Architect | Design reviewed | Yes |
| **Generate Division** | `generate-division` | DevOps | Plan approved | No (background) |
| **Test Division** | `test-division` | QA | Code generated | No (background) |
| **Deploy Division** | `deploy-division` | DevOps | Tests passing | No |
| **Monitor Division** | `monitor-division` | Mentor | *(none — opens automatically once deployed)* | Yes, always available |
| **Rescue Division** | `rescue-division` | DevOps | *(none — opens on incident, from any state)* | Yes, always available |

**Design Division** — The user and Architect collaborate on event storming, aggregate design, desk inventory. The task UI shows the emerging domain model alongside the chat. Ongoing — design evolves. (Both Design and Plan sit on Architect's single Planning dossier — kept as two tasks here because the task list is deliberately finer-grained than the underlying process, not because they're separate processes.)

**Plan Division** — The user and Architect break down the design into an implementation plan. Sequencing, priorities, dependencies between desks. Ongoing — plans adapt.

**Generate Division** — DevOps generates skeleton code — retrieving the matching corpus template and antipattern list from `mcl-rag` first, then filling it in, per the "coding should be almost mechanical" principle in `roles/AGENT_ARCHITECTURE.md`. This runs in the **background** — the user can work on other tasks while code is being generated. The task shows progress and generated files.

**Test Division** — QA runs tests and verifies the generated code against the same corpus DevOps retrieved from — the interesting failure mode is "wrong template" or "filled in wrong," which is exactly what this catches. Also background. Shows test results, coverage, issues found.

**Deploy Division** — Ship it. DevOps version-bumps, confirms CI is green, and deploys — same role that generated the code, consistent with "you build it, you run it." The user reviews and confirms. Could show deployment status, canary results.

**Monitor Division** — **Not gated by Deploy Division completing, and never blocks anything.** Per `alc/README.md`: "monitoring... [is an] operational concern, not a lifecycle phase — it happens continuously, not sequentially." This task opens automatically the moment a division is first deployed and simply stays open — Mentor's live-observation mode, extended from watching agent output during Crafting to watching the running system afterward. Shows metrics, logs, alerts.

**Rescue Division** — Something broke. **Not downstream of Monitor Division in any DAG sense** — it can open from any state, triggered by an incident, not by another task completing. DevOps is first responder (it owns deployment — "you get paged"), QA verifies the fix, Domain Expert joins if the root cause is a domain-modeling gap rather than a bug. Can escalate back to Design Division if the fix requires architectural changes.

---

## The Task List

The primary view of the task model is the task list. It's a single, scrollable list with visual grouping.

### Layout

```
Domain: MyProject
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ✓  Initiate Domain
 ✓  Refine Vision                 🤖 Domain Expert
 ✓  Submit Vision
 ●  Refine Divisions              🤖 Domain Expert
─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
 ▸ Auth Service
    ✓  Design                     🤖 Architect
    ✓  Plan                       🤖 Architect
    ◐  Generate                   🤖 DevOps
    ○  Test                       🤖 QA
    ○  Deploy                     🤖 DevOps
    ●  Monitor                    🤖 Mentor      (always open once deployed)
 ▸ Payment Gateway
    ●  Design                     🤖 Architect
    ○  Plan
    ○  Generate
    ○  Test
    ○  Deploy
 ▸ Notification Service
    ○  Design                     (blocked)
    ○  ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ↑/↓ navigate  Enter: open  q: back
```

### Behaviors

- **Collapsible groups**: Division groups can be collapsed/expanded with `Tab` or arrow keys.
- **Status at a glance**: Each task shows its state symbol. Background tasks show progress.
- **Blocked tasks are visible but dimmed**: The user can see what's coming but can't open blocked tasks.
- **Navigate with j/k or arrows**: Standard vim-style navigation in Normal mode.
- **Enter opens the task UI**: Each task type has its own dedicated interface.
- **Division independence**: Tasks in one division don't block tasks in another division.

### Dynamic Growth

The task list grows as the user works:

1. **`domain_initiated_v1`** → "Initiate Domain" completes, "Refine Vision" unlocks
2. **`refine_vision_started_v1`** → task becomes active, Domain Expert greets, research already under way
3. **`vision_submitted_v1`** → "Refine Divisions" unlocks
4. **`refine_divisions_started_v1`** → user and Domain Expert explore the domain
5. **`division_confirmed_v1`** → Division group appears with its sub-tasks, plus Monitor Division (dormant until deploy) and Rescue Division (dormant until an incident)
6. **`design_division_started_v1`** → user opens a division task, Architect assists
7. **`design_division_paused_v1`** → user steps away, timestamp recorded
8. **`design_division_resumed_v1`** → user returns, picks up where they left off
9. **`deploy_division_completed_v1`** → Monitor Division opens automatically, stays open indefinitely

---

## Task UIs

Each task type has a dedicated UI. Most AI-assisted tasks share a common layout:

### AI-Assisted Task Layout

```
┌─────────────────────────────────────────────────┐
│ Design Division: Auth Service     🤖 Architect  │
├─────────────────────────────────────────────────┤
│                                                 │
│  [Task-specific content panel]                  │
│  (domain model, file tree, test results, etc.)  │
│                                                 │
├─────────────────────────────────────────────────┤
│  AI: What authentication patterns are you       │
│  considering? OAuth2, session-based, or JWT?    │
│                                                 │
│  You: We need OAuth2 for external clients and   │
│  session-based for the web dashboard.           │
│                                                 │
│  AI: Good split. I'd suggest two desks:         │
│  - authenticate_oauth_client (external)         │
│  - authenticate_web_session (internal)          │
│  Each with their own aggregate...               │
│                                                 │
├─────────────────────────────────────────────────┤
│ > Type here...                                  │
└─────────────────────────────────────────────────┘
```

The chat component is embedded in the task UI. It's both the AI interaction surface AND the primary text input. The AI role is auto-selected based on the task type.

### Task-Specific Content Panels

| Task | Content Panel |
|------|--------------|
| Refine Vision | Vision document (evolving markdown) |
| Refine Divisions | Proposed divisions list with [Confirm] / [Reject] actions |
| Design Division | Domain model: aggregates, events, commands |
| Plan Division | Task breakdown, sequencing, dependency graph |
| Generate Division | File tree, generation progress, generated code preview |
| Test Division | Test results, coverage, failing tests |
| Deploy Division | Deployment status, rollout progress |
| Monitor Division | Metrics dashboard, recent logs, alerts |
| Rescue Division | Incident timeline, diagnosis, suggested fixes |

### Non-AI Tasks

Some tasks don't need AI assistance:

- **Initiate Domain** — A form (name, brief, path). Completes immediately.
- **Submit Vision** — A confirmation button within the Refine Vision task.
- **Deploy Division** — May be a confirmation + status view (the deployment itself is automated).

---

## The DAG (Prerequisites)

Tasks form a directed acyclic graph. The task engine enforces prerequisites.

### Domain-Level DAG

```
initiate-domain
       │
       ▼
 refine-vision
       │
       ▼
 submit-vision
       │
       ▼
refine-divisions ──────┐
       │               │
       ▼               ▼
  [confirm div A]  [confirm div B]  ...
       │               │
       ▼               ▼
  design-div-A    design-div-B
       │               │
       ...             ...
```

### Division-Level DAG

```
design-division
       │
       ▼
 plan-division
       │
       ▼
generate-division
       │
       ▼
 test-division
       │
       ▼
deploy-division
       │
       ▼
  (deployed) ────────────────────▶ monitor-division
       .                           (opens automatically,
       .                            stays open, blocks nothing,
       .                            not blocked by anything)
       .
       └──── (incident, any time) ─▶ rescue-division
                                            │
                                            ▼
                                    (may escalate to design-division)
```

Monitor and Rescue are deliberately **not** drawn as sequential nodes
downstream of Deploy. They're triggered (by a deploy event, or by an
incident) rather than unlocked by a prerequisite, and neither blocks
anything else — matching `alc/README.md`'s doctrine that monitoring and
rescue are continuous operational concerns, not lifecycle phases. The
dotted line is deliberate: it's a trigger, not a DAG edge.

### Cross-Division Independence

Division-level DAGs are completely independent. Auth Service can be deploying while Payment Gateway is still being designed. The only shared prerequisite is that a division must be confirmed before any of its tasks unlock.

---

## Verb-Based API

The task API is organized around verbs — each endpoint IS a workflow action. Every task has lifecycle endpoints (start, pause, resume, complete) and task-specific action endpoints.

### API Pattern

Every task follows the same lifecycle pattern:

```
POST /api/start-{task}/:id         → {task}_started_v1
POST /api/pause-{task}/:id         → {task}_paused_v1
POST /api/resume-{task}/:id        → {task}_resumed_v1
POST /api/complete-{task}/:id      → {task}_completed_v1
```

Task-specific actions only work when the task is **active**:

```
POST /api/{task}/:id/{action}      → (task-specific event)
```

### Domain Lifecycle

```
# Initiate (no lifecycle — it's the birth event)
POST   /api/initiate-domain
  Body: { name, brief, path }
  Returns: { domain_id, tasks: [...] }
  Event: domain_initiated_v1

# Refine Vision
POST   /api/start-refine-vision/:domain_id      → refine_vision_started_v1
POST   /api/pause-refine-vision/:domain_id       → refine_vision_paused_v1
POST   /api/resume-refine-vision/:domain_id      → refine_vision_resumed_v1
POST   /api/complete-refine-vision/:domain_id    → refine_vision_completed_v1

# Refine Vision actions (only when active):
POST   /api/refine-vision/:domain_id/chat
  Body: { message }
  Returns: { response, vision_snapshot }

# Submit Vision (confirmation action, not a lifecycle task)
POST   /api/submit-vision/:domain_id
  Returns: { ok, tasks_unlocked: ["refine-divisions"] }
  Event: vision_submitted_v1

# Refine Divisions
POST   /api/start-refine-divisions/:domain_id    → refine_divisions_started_v1
POST   /api/pause-refine-divisions/:domain_id     → refine_divisions_paused_v1
POST   /api/resume-refine-divisions/:domain_id    → refine_divisions_resumed_v1
POST   /api/complete-refine-divisions/:domain_id  → refine_divisions_completed_v1

# Refine Divisions actions (only when active):
POST   /api/refine-divisions/:domain_id/chat
  Body: { message }
  Returns: { response, proposed_divisions: [...] }

POST   /api/refine-divisions/:domain_id/confirm
  Body: { division_name, division_brief }
  Returns: { division_id, tasks_created: [...] }
  Event: division_confirmed_v1
```

### Division Lifecycle

Each division task follows the same lifecycle pattern. `:id` is the division ID.

```
# Design
POST   /api/start-design-division/:id             → design_division_started_v1
POST   /api/pause-design-division/:id              → design_division_paused_v1
POST   /api/resume-design-division/:id             → design_division_resumed_v1
POST   /api/complete-design-division/:id           → design_division_completed_v1

POST   /api/design-division/:id/chat               (only when active)
  Body: { message }
  Returns: { response, model_snapshot }

# Plan
POST   /api/start-plan-division/:id               → plan_division_started_v1
POST   /api/pause-plan-division/:id                → plan_division_paused_v1
POST   /api/resume-plan-division/:id               → plan_division_resumed_v1
POST   /api/complete-plan-division/:id             → plan_division_completed_v1

POST   /api/plan-division/:id/chat                 (only when active)

# Generate (background — starts AI work)
POST   /api/start-generate-division/:id            → generate_division_started_v1
POST   /api/pause-generate-division/:id            → generate_division_paused_v1
POST   /api/resume-generate-division/:id           → generate_division_resumed_v1
POST   /api/complete-generate-division/:id         → generate_division_completed_v1

GET    /api/generate-division/:id/status
  Returns: { progress, files_generated }

# Test (background)
POST   /api/start-test-division/:id               → test_division_started_v1
POST   /api/complete-test-division/:id             → test_division_completed_v1

GET    /api/test-division/:id/status
  Returns: { results, coverage, failures }

# Deploy
POST   /api/start-deploy-division/:id             → deploy_division_started_v1
POST   /api/complete-deploy-division/:id           → deploy_division_completed_v1

POST   /api/deploy-division/:id/confirm
  Body: { target_env }
  Event: deployment_confirmed_v1

# Monitor (ongoing)
POST   /api/start-monitor-division/:id            → monitor_division_started_v1
POST   /api/pause-monitor-division/:id             → monitor_division_paused_v1
POST   /api/resume-monitor-division/:id            → monitor_division_resumed_v1

GET    /api/monitor-division/:id/status
  Returns: { metrics, alerts, health }

# Rescue (opens on incident)
POST   /api/start-rescue-division/:id             → rescue_division_started_v1
POST   /api/complete-rescue-division/:id           → rescue_division_completed_v1

POST   /api/rescue-division/:id/chat               (only when active)
```

### Task List

```
GET    /api/domain/:domain_id/tasks
  Returns: {
    domain: { id, name, vision_status },
    tasks: [
      {
        verb, scope, subject, phase, ai_role,
        state,         -- pending | active | paused | running | completed
        started_at,    -- from *_started_v1 event
        paused_at,     -- from *_paused_v1 event (null if active)
        completed_at,  -- from *_completed_v1 event
        blocked_by     -- task verbs that must complete first
      },
      ...
    ],
    divisions: [
      { id, name, confirmed_at, tasks: [...] },
      ...
    ]
  }
```

This single endpoint powers a task list view. The frontend polls it (or subscribes via WebSocket in the future) for updates. Timestamps from lifecycle events enable tracking ("Design paused 2 days ago", "Generation took 45 minutes").

---

## AI Role Auto-Selection

Each task type knows which AI role it needs. The task model doesn't ask the user to switch roles — it's automatic.

| Task Type | AI Role | Personality Aspect |
|-----------|---------|-------------------|
| Refine Vision | Domain Expert | Curious, research-first, probing |
| Refine Divisions | Domain Expert | Boundary finder, grounded in prior art |
| Design Division | Architect | Pattern matcher, systems thinker |
| Plan Division | Architect | Sequencer, prioritizer |
| Generate Division | DevOps | Mechanical by design — retrieve the template, fill it in |
| Test Division | QA | Skeptical, meticulous, checks against the same corpus DevOps retrieved from |
| Deploy Division | DevOps | Ships what it built — same role, same ownership |
| Monitor Division | Mentor | Continuous, low-cost, watching |
| Rescue Division | DevOps | First responder — "you built it, you run it" |

Cutting across every row above: **Reporter** documents continuously
(not tied to any one task type), and **Mentor** also observes live
during every task, not just Monitor Division — the table above names
which role a task is *for*, not the only role ever present.

The system prompt for each AI interaction is:

```
[PERSONALITY.md]   — Macula's core personality
---
[role file]        — roles/{domain_expert,architect,devops,qa,reporter,mentor}.md
---
[task context]     — Domain name, division name, current state, history
---
[task prompt]      — Task-specific instructions (what the AI should focus on)
```

---

## Ongoing vs Completable Tasks

Not all tasks "finish" the same way.

### Completable Tasks

These have a clear end state:

- **Initiate Domain** — Done when domain exists
- **Submit Vision** — Done when confirmed
- **Generate Division** — Done when code is generated
- **Test Division** — Done when tests pass
- **Deploy Division** — Done when deployed

### Ongoing Tasks

These can be revisited indefinitely:

- **Refine Vision** — Vision can always be refined (but must be submitted to proceed)
- **Refine Divisions** — New divisions can always be discovered
- **Design Division** — Design evolves as understanding deepens
- **Plan Division** — Plans adapt to reality
- **Monitor Division** — Always watching
- **Rescue Division** — Opens on incidents, closes when resolved, can reopen

Ongoing tasks show as `✓` when their minimum criteria are met, but the user can always reopen them. They might show a secondary indicator: `✓↻` (done but revisitable).

---

## Service Shape

### What Changes

1. **New: Task Engine** — A service that tracks task states, prerequisites, and transitions. The task engine reads lifecycle events to derive current state and enforces the DAG (e.g., rejects `start-design-division` if vision is not submitted).

2. **New: Verb-based API routes** — Each workflow action gets its own endpoint. Replaces noun-based CRUD endpoints. Each endpoint maps to a desk.

3. **New: Background job tracking** — Generation and testing run as background jobs with progress reporting via SSE.

4. **Evolves: CMD apps** — The existing process-centric CMD apps (`design_division`, etc.) gain lifecycle desks. Each CMD app has 4 lifecycle desks + N action desks:

```
apps/design_division/src/
├── start_design_division/
│   ├── start_design_division_v1.erl        (command)
│   ├── design_division_started_v1.erl      (event)
│   └── maybe_start_design_division.erl     (handler)
├── pause_design_division/
│   ├── pause_design_division_v1.erl
│   ├── design_division_paused_v1.erl
│   └── maybe_pause_design_division.erl
├── resume_design_division/
│   └── ...
├── complete_design_division/
│   └── ...
├── chat_design_division/                    (task-specific action)
│   ├── chat_design_division_v1.erl
│   ├── design_division_chatted_v1.erl
│   └── maybe_chat_design_division.erl
└── design_division_aggregate.erl            (enforces lifecycle state machine)
```

5. **Evolves: Fact stream** — Lifecycle events emit facts on the mesh so a task view updates in real-time. "Design Division started", "Generation paused", etc.

### What Doesn't Change

- **Event sourcing** — Still the foundation. Lifecycle transitions ARE events.
- **CMD/QRY/PRJ departments** — Still the internal architecture.
- **Vertical slicing** — Each desk owns its command, event, and handler.
- **The domain/division process model** — Still the foundation (domain-level setup + discovery; division-level Planning + Crafting). Tasks are now deliberately *finer-grained* than processes, not 1:1 with them — e.g. Design Division and Plan Division are two tasks on Architect's one Planning dossier, and Generate/Test/Deploy Division are three tasks on DevOps/QA's one Crafting dossier.
- **Aggregate pattern** — The aggregate enforces the state machine (can't pause a pending task, can't chat on a paused task).

---

## The Task View

### Structure

The task view is a task-driven workspace:

1. **Task List View** (default) — Shows all tasks, grouped by division, with state indicators.
2. **Task UI View** (on Enter) — Opens the dedicated UI for the selected task.
3. **Back to list** (Escape/q) — Returns to the task list.

The task view does NOT share a single chat. Each AI-assisted task has its own embedded chat component with the appropriate AI role.

### Key Components

- **TaskList** — The scrollable, collapsible task list with vim navigation
- **TaskChat** — Embedded chat component (reusable across task UIs)
- **VisionEditor** — Refine Vision task UI
- **DivisionExplorer** — Refine Divisions task UI (chat + proposed list)
- **DomainModeler** — Design Division task UI (chat + model view)
- **PlanBuilder** — Plan Division task UI (chat + task breakdown)
- **GenerationMonitor** — Generate Division task UI (progress + file preview)
- **TestRunner** — Test Division task UI (results + coverage)
- **DeployDashboard** — Deploy Division task UI (status + rollout)
- **MonitorDashboard** — Monitor Division task UI (metrics + alerts)
- **RescueConsole** — Rescue Division task UI (diagnosis + chat)

---

## Relationship to Existing Documents

| Document | Relationship |
|----------|-------------|
| `DOMAIN_LIFECYCLE.md` | **Foundation** — The domain hierarchy and domain-level processes are unchanged. This document adds the UX layer on top. |
| `alc/README.md` | **Foundation** — the two Division ALC processes (Planning, Crafting) are the basis for the division-scoped task catalog above; its doctrine that monitoring/rescue/debugging/refactoring are continuous, not sequential operational concerns, is why they appear as always-available branches in the DAG above, not gated phases. |
| `roles/AGENT_ARCHITECTURE.md` | **Foundation** — the `ai_role` column above names roles from its current 6-role roster (Domain Expert, Architect, DevOps, QA, Reporter, Mentor), not the retired DnA/AnP/TnI/DnO scheme. |
| `DDD.md` | **Unchanged** — The Dossier Principle still applies. Each task works on a dossier. |
| `CARTWHEEL.md` | **Unchanged** — CMD/QRY/PRJ departments are internal architecture, not user-facing. |

---

_Tasks are the work. Phases are the weather. The goddess guides both._ 🔥🗝️🔥
