---
title: The Division Application Lifecycle
layer: philosophy
audience: [agent, human]
stage: stable
---

# The ALC — Division Application Lifecycle

*Two processes. One chain. Planning feeds crafting. Tracked in git, not event sourced.*

---

## Overview

The ALC governs how a **division** (bounded context, cohesive piece of software) evolves from design to delivery, through **two processes**: Planning and Crafting.

Development itself is chaotic and non-linear — a design gets revisited after Crafting starts, a plan gets reopened after Discovery reveals something new. That doesn't fit a single-current-state aggregate, so neither process is event sourced. Instead, each process's output is a git-tracked artifact, and the human-approval gates that matter are git commits or merged PRs -- genuinely append-only, audit-worthy facts, with git log supplying the history for free.

The ALC applies to **divisions specifically**. Domains have their own lifecycle (`DOMAIN_LIFECYCLE.md`). Nodes run continuously. The division is where craft happens.

---

## The Two Processes

| # | Process | Artifact | Purpose |
|---|---------|----------|---------|
| 1 | **Planning** | `plans/PLAN_{DIVISION}.md`, in the division's own repo | Event storming, aggregate design, desk inventory, dependencies |
| 2 | **Crafting** | The division's own codebase + `CHANGELOG.md` | Code generation, testing, release delivery |

Planning produces a document. Crafting produces the thing the document describes -- there's no separate crafting document; the code and its `CHANGELOG.md` entries are the artifact.

---

## Planning

**Where it lives:** `plans/PLAN_{DIVISION}.md`, following this workspace's established `plans/PLAN_*.md` convention -- read at session start, edited as work proceeds, never narrated with its own revision history (see `skills/antipatterns/documentation.md` Demon #58: state the current design, let git log carry how it got there).

**What it must contain before the Design Gate:**
- Aggregate boundaries -- what the division's aggregate(s) are, and why
- The domain event list
- A desk inventory -- what capabilities the division needs
- Desk dependencies -- what has to exist before what

**The Design Gate is a commit, not a command.** A human reviews the plan document and either edits it directly or merges the PR that finalizes it -- that commit *is* the approval; git log is the audit trail. No separate approval record is needed.

---

## Crafting

**Where it lives:** the division's own codebase. There's no separate crafting document -- the code, its tests, and `CHANGELOG.md` entries are the artifact, and git log is the record of how it got built.

**What a complete Crafting pass produces:**
- Generated modules and their tests, matching the plan document's desk inventory
- A green test suite run
- A `CHANGELOG.md` entry
- A tagged, released version

**The Review Gate and Release Gate are commits too.** QA's sign-off is a commit (or PR approval) against the code or `CHANGELOG.md`; the Release Gate is the human approving the release PR or tag. Same mechanism as the Design Gate -- a git action is the fact, git log is the history.

---

## Coordination

Concluding Planning doesn't dispatch a command to start Crafting -- there's no process manager, because there's no event stream to subscribe to. Whichever harness makes the Design Gate commit is responsible for publishing a mesh fact announcing it (e.g. `macula.gate_passed`, with the division id and `gate: "design"` in the payload, never the topic). A DevOps-role harness `mesh_watch`-ing for it picks up Crafting.

If two harnesses both act on the same document, resolution is git's own: whichever pushes or merges first wins, and the second hits a conflict and backs off. No aggregate, no lock service -- the same thing that already happens whenever more than one contributor touches a shared file.

There is no crew backend service; this is a git-and-mesh convention, not infrastructure to build.

---

## Three Lifecycles

The ALC is one of three lifecycle types in the Macula ecosystem:

| Lifecycle | Scope | Nature |
|-----------|-------|--------|
| **Domain Lifecycle** | The overall business endeavor | Setup, discovery, orchestration -- see `DOMAIN_LIFECYCLE.md` |
| **Division ALC** | A single bounded context | The two-process chain described here |
| **Node Lifecycle** | Infrastructure | Continuous operation, no phases -- never a candidate for event sourcing; it's a running service, not a development process |

---

## Related Doctrines

| Doctrine | Relevance | Description |
|----------|-----------|--------------|
| [Walking Skeleton](../WALKING_SKELETON.md) | Crafting | Fully operational system from day one |
| [Dossier Principle](../DDD.md) | Planning | Process-centric domain modeling -- applies to a division's own production business logic, not to tracking the build |
| [Vertical Slicing](../VERTICAL_SLICING.md) | Planning, Crafting | Features live together, no horizontal layers |
| [Screaming Architecture](../SCREAMING_ARCHITECTURE.md) | Planning, Crafting | Names reveal intent |
| [Division Model](../../guides/CARTWHEEL_COMPANY_MODEL.md) | All | CMD/PRJ/QRY department structure -- for a division's own production business logic, which stays event sourced by default |

---

## For Agents

When working on a division:

1. **Know which process is active.** Planning produces the design; Crafting builds it. Don't generate code before the plan document has cleared the Design Gate.
2. **The plan document is the source of truth**, not a chat transcript or a memory of the conversation. If a decision isn't written down in `plans/PLAN_{DIVISION}.md`, it hasn't been decided yet.
3. **A gate is a commit.** Don't wait for a service to tell you a gate passed -- watch for the `mesh_publish` fact, or just read the document.
4. **Conclude fast.** Small iterations. A thin plan that clears the Design Gate quickly beats an exhaustive one that never ships.

---

## Terminology

| Term | Meaning | Old Term |
|------|---------|----------|
| **Domain** | The overall business endeavor | Venture, Torch |
| **Division** | A bounded context, cohesive software unit | Cartwheel / Company |
| **Department** | CMD, PRJ, or QRY within a division's own production codebase | Department |
| **Desk** | A single capability within a department | Spoke |
| **Dossier** | The aggregate -- folder of event slips. Applies to a division's own production business logic, not to Planning/Crafting tracking. | Dossier |

---

*Two processes. Planning feeds crafting. Tracked in git, not event sourced.*
