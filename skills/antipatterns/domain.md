---
title: "ANTIPATTERNS: Domain"
layer: skill
audience: [agent, human]
stage: stable
---

# ANTIPATTERNS: Domain — Domain Modeling Mistakes

*Demons about domain modeling. Process-centric, not data-centric.*

[Back to Index](INDEX.md)

---

## 🔥 Parallel Domain Infrastructure

**Date:** 2026-02-04
**Origin:** the removed daemon apprentice

### The Antipattern

Creating duplicate command/event/emitter infrastructure in a new domain when an existing domain already handles that concept.

**Example:** `serve_llm` created:
- `announce_llm_capability_v1` command
- `llm_capability_announced_v1` event
- `llm_capability_announced_v1_to_mesh` emitter
- `mcl.llm.announced` mesh topic

But `manage_capabilities` already has:
- `announce_capability_v1` command
- `capability_announced_v1` event
- `capability_announced_v1_to_mesh` emitter
- `mcl.capability.announced` mesh topic

LLM capabilities ARE just capabilities with `type = <<"llm">>`.

### The Rule

> **Don't duplicate domain concepts. Extend existing domains or use Process Managers to integrate.**

### The Solution: Process Managers

When Domain A needs to trigger behavior in Domain B:

```
Domain A (serve_llm)
    ↓ emits internal event (llm_model_detected_v1)

Process Manager (on_llm_model_detected_announce_capability)
    ↓ subscribes to Domain A events
    ↓ dispatches command to Domain B

Domain B (manage_capabilities)
    ↓ handles command normally
    ↓ existing infrastructure does the rest
```

**Loose coupling. Single source of truth. No duplication.**

---

## 🔥 Missing or Wrong "Birth" Event

**Date:** 2026-02-08
**Origin:** Domain/Division architecture discussion

### The Antipattern

Process/domain aggregates that don't have a clear "birth" event, or use wrong verbs:

| ❌ Wrong | Why |
|----------|-----|
| `project_created_v1` | CRUD — "created" says nothing about business intent |
| `division_started_v1` | Ambiguous — "started" could mean resumed, begun, etc. |
| `order_made_v1` | Weak — doesn't convey the initiation of a process |
| No birth event at all | Aggregate appears from nowhere |

### The Rule

> **Every process/domain aggregate MUST begin with `{aggregate_singular}_initiated_v{N}`**

This event is the "birth" of the aggregate — it marks the moment the process began.

| ✅ Correct | Aggregate |
|-----------|-----------|
| `venture_initiated_v1` | Domain |
| `division_initiated_v1` | Division |
| `order_initiated_v1` | Order |
| `claim_initiated_v1` | Insurance Claim |
| `project_initiated_v1` | Project |

### Why "Initiated"?

- **Business verb** — "We initiated a new project" is natural language
- **Process-oriented** — signals the START of a lifecycle, not just creation of data
- **Consistent** — one word for all aggregates, easy to search/grep
- **Not CRUD** — avoids the banned "created/updated/deleted" vocabulary

### The Pattern

```erlang
%% First event in any aggregate stream
#{
    event_type => <<"venture_initiated_v1">>,
    stream_id => <<"domain-abc123">>,
    data => #{
        venture_id => <<"abc123">>,
        name => <<"macula-geo">>,
        brief => <<"Geo-restriction for compliance">>,
        initiated_by => <<"human:rl">>,
        initiated_at => 1707350400000
    }
}
```

### Checklist

When creating a new aggregate:
- [ ] First event is `{aggregate}_initiated_v1`
- [ ] Event includes `initiated_by` (who/what started it)
- [ ] Event includes `initiated_at` (timestamp)
- [ ] Handler validates "not already initiated" before accepting

---

## 🔥 Auto-Creating Child Aggregates on Parent Initiation

**Date:** 2026-02-08
**Origin:** Domain → Division architecture discussion

### The Antipattern

Assuming that when a parent aggregate is initiated, child aggregates should be automatically created.

**Example (WRONG):**
```
venture_initiated_v1
    → listener subscribes
    → automatically creates division
```

This assumes:
- Every domain needs exactly one division
- The relationship is 1:1 and automatic
- No human/agent decision is needed

**Reality:** A domain might need 0, 1, 5, or 10 divisions. This is a deliberate decision, not an automatic consequence.

### The Rule

> **Parent aggregates DISCOVER children. Child aggregates INITIATE themselves.**

The parent owns the "what exists" decision. The child owns its lifecycle.

### The Correct Flow

```
1. venture_initiated_v1          # Domain exists
2. division_discovered_v1        # Domain decides "I need a division called X"
   → emitted to mesh
3. division_initiated_v1         # Division service starts X's lifecycle
```

### Semantic Distinction

| Action | Owner | Meaning |
|--------|-------|---------|
| **Discover** | Parent (domain) | "This parent will have a child called X" |
| **Initiate** | Child (division) | "Start the lifecycle of X" |

### Why It Matters

- **Flexibility** — Parent can have 0..N children
- **Explicit decisions** — Humans/agents choose what children exist
- **Proper DDD** — Parent aggregate owns its children's identities
- **Separation of concerns** — Identity vs lifecycle are different responsibilities

### The Lesson

> **Skip DnA phase → Make wrong assumptions → Build wrong architecture → Waste time fixing**

This mistake happened because we jumped to implementation without understanding the domain.

---

## 🔥 Direct Creation Endpoints for Child Aggregates

**Date:** 2026-02-09
**Origin:** Division API architecture review

### The Antipattern

Exposing a direct "create" or "initiate" API endpoint for child aggregates that should only exist through their parent.

**Example (WRONG):**
```
POST /api/divisions/initiate
{
  "name": "My Division",
  "description": "..."
}
```

This bypasses the domain flow:
- Divisions should only exist because a domain discovered them
- Direct creation allows orphan divisions (no parent domain)
- Violates the parent-child aggregate pattern

### The Rule

> **Child aggregates should NOT have direct creation endpoints. They're created through parent discovery.**

### The Correct Flow

1. **Parent discovers child**: `POST /api/domains/:venture_id/divisions/discover`
2. **Event emitted**: `division_discovered_v1` to pg (internal) + mesh (external)
3. **PM sibling slice in target domain receives**: `on_division_discovered_initiate_division/` in `design_division` (gen_server `pg:join`s source scope in `init/1`)
4. **PM dispatches command**: `initiate_division_v1`
5. **Child initiated**: `division_initiated_v1` event created

### When to Use Which

| Aggregate Type | Creation Endpoint? | Why |
|----------------|-------------------|-----|
| **Root aggregate** | Yes | Domain, Order, User — top-level entities |
| **Child aggregate** | No | Division, OrderLine — created via parent |

### API Design Pattern

```erlang
%% GOOD: Parent creates children through relationship
POST /api/domains/:venture_id/divisions/discover

%% BAD: Direct creation of child
POST /api/divisions/initiate    % REMOVE THIS
```

### Testing Implications

When testing the walking skeleton:
- **Respect the domain flow** — Don't bypass event-driven creation with direct APIs
- **Test the full path** — Parent → Event → Listener → Child
- **If it doesn't work** — Fix the event flow, don't add a shortcut API

### The Lesson

> **API endpoints should reflect domain operations, not CRUD convenience.**

If you need to create test data, use the proper flow or seed the event store directly.

---

## 🔥 Implementation on the Storming Wall

**Demon 75. Date:** 2026-11-14
**Origin:** shaping a storming board for the method

### The Antipattern

At a Division's wall, the group (or the engineer who facilitates) starts to model how a command is prepared and decided:

- its pipeline: which lookups run before the decision, and in which order
- the types of the fields
- the status flags, and which slip is allowed when

Every one of these is a fair question, and none of them is for this room. The people at the wall are there because they know the process. They cannot say in what order lookups run, so they fall silent, and what gets drawn is the engineer's design, made before any code. The wall no longer belongs to the business.

### The Rule

> **The wall belongs to the business. Ask of anything about to go on it: could the people standing here answer this?**

They can say what a registration makes known: "the date it was released by customs", "the part's serial number". That is the Definition of Dossier, and it emerges from the wall as names, each with the event that makes it known. They can say what someone needs to see in order to decide, and that is a read model in the actor's lane.

### Where the Rest Goes

| Question | Who answers it | Where it lives |
|----------|----------------|----------------|
| What happens, who does it, what does it make known | the people at the wall | the wall ([EVENT_STORMING.md](../../philosophy/EVENT_STORMING.md)) |
| How a command is enriched and decided | whoever builds the desk | the desk's pipeline ([COMMAND_PIPELINES.md](../../philosophy/COMMAND_PIPELINES.md)) |
| Field types, status flags, which slip when | the architect, after the storm | technical design (`roles/architect.md`, Stage 2) |

### What Refuses It

The wall file of a Division holds names only: notes, lanes, wiring, and per dossier the names of what is known. It has no place for a pipeline, a type or a flag, and its check fails a file that carries one (macula-services/mcl-whiteboard#14).

### The Lesson

> **A wall the experts cannot read is upfront design with sticky notes on it.**

---

*Add more demons as we exorcise them.* 🔥🗝️🔥
