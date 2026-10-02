---
title: Agent Role Architecture
layer: role
audience: [agent]
stage: stable
---

# Agent Role Architecture

*How AI agents collaborate to guide the domain lifecycle.*

**Status:** Active

---

## Principles

1. **Minimize cost/token consumption** — use the cheapest tier that can do the job, and prefer a harness's own already-open model over a separate call entirely (see "Model Routing")
2. **Human-in-the-loop at defined gates** — the human can always intervene, but 5 mandatory gates require explicit approval
3. **Multi-provider, advisory not enforced, always** — a role names a capability tier as *guidance* for whichever harness picks it up; no service in this architecture calls a model on an agent's behalf, so there's no context where the tier is anything but advisory (see "Model Routing")
4. **Self-hosted, when a harness's own choice** — Ollama/local models are a fine, cheap option for a harness to reach for on trivial tasks; not a routing decision this architecture makes for it
5. **Retrieve before reasoning** — Domain Expert researches via `mcl-rag`/web before opining; DevOps retrieves the matching corpus template/antipattern list before generating. Coding especially is close to mechanical once the corpus is in `mcl-rag` — the interesting failure mode shifts to "wrong template retrieved," which is exactly what QA checks for

---

## Model Tiers

A tier is a *request*, not a guarantee — see "Model Routing" for who actually honors it.

| Tier | Capability | Example Models | Cost |
|------|-----------|---------------|------|
| **T1 — Reasoning** | Deep analysis, DDD, boundary decisions, review | Claude Opus, GPT-4o, Qwen-72B | $$$ |
| **T2 — Competent** | Good code gen, solid reasoning, follows patterns | Claude Sonnet, Qwen-32B, Llama-70B, DeepSeek-V3 | $$ |
| **T3 — Fast** | Template following, simple transforms, coordination | Claude Haiku, Qwen-7B, Llama-8B, Groq-hosted small models | $ |
| **T0 — Local** | Trivial tasks, formatting, JSON extraction | Self-hosted via Ollama | Free |

**Cost optimization rule:** Start at the lowest tier that can do the job. Escalate only on failure or insufficient output quality.

---

## Agent Roster

| # | Role | Lifecycle Stage | Tier | HITL Gate | File |
|---|------|-----------------|------|-----------|------|
| 1 | **Domain Expert** | Domain Lifecycle (setup, discovery) | T1 | Vision Gate, Boundary Gate | `domain_expert.md` |
| 2 | **Architect** | Division ALC / Planning | T1→T2 | Design Gate | `architect.md` |
| 3 | **DevOps** | Division ALC / Crafting, through deploy; first responder on incidents | T2 (generation) / T3–T0 (release, deploy mechanics) | Release Gate | `devops.md` |
| 4 | **QA** | Division ALC / Crafting (verification side) | T2 (test execution) / T1 (review, release-readiness) | Review Gate | `qa.md` |
| 5 | **Reporter** | Continuous, cross-cutting — documentation | T2/T3 | — | `reporter.md` |
| 6 | **Mentor** | Continuous, cross-cutting — quality observation | T3 (live) / T1 (gate coaching, post-mortem) | — | `mentor.md` |

Two things are deliberately not roles: pipeline routing/kanban tracking
is process-manager logic — a DAG lookup against
task state, not reasoning work — and system monitoring is ordinary
health-endpoint/metrics infrastructure, not an agent. An incident
re-engages the roster reactively: DevOps first (it owns deployment), QA
verifies the fix, Domain Expert if the root cause is a domain-modeling
gap rather than a bug. See `philosophy/alc/README.md`: "Monitoring,
rescue, debugging, and refactoring are operational concerns, not
lifecycle phases."

---

## Model Routing

There is exactly one execution context: **an agent (a harness, channel
(b) of `AUTH_MODEL.md`) does the reasoning, always, on its own
already-configured model.** No service in this architecture calls a
model on an agent's behalf — full design in
`macula-mcp/plans/PLAN_MARTHA_MULTI_AGENT_MCP.md`.

"Interactive" and "background" are a scheduling distinction — is a human
watching this particular session right now — not an architectural one.
A background task (e.g. "Generate Division," per `TASK_MODEL.md`)
still runs inside some harness's own agent session; it's just not the
one session a human happens to be watching turn-by-turn. Task-state
tracking and unlock publication are process-manager mechanics (see
`PLAN_MARTHA_MULTI_AGENT_MCP.md`'s "Multi-agent coordination"); nothing
picks up the work itself, and nothing calls a model.

The T0–T1 tier vocabulary is advisory in every case, without exception —
a role names a tier as guidance for whichever harness picks it up.
`macula-mcp` cannot see or control what model a harness
has configured, so there is no context where the tier is anything but
advisory. See `AUTH_MODEL.md` and the plan doc above for the full
reasoning, including the honest tradeoff (no enforced quality floor for
interactive roles).

---

## Human-in-the-Loop Gates

Five mandatory checkpoints where the human must approve before the pipeline advances.

```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  Domain Expert ──► [VISION GATE] ──► Domain Expert ──► [BOUNDARY GATE]│
│  (research + brief)                  (division discovery)             │
│                                                 │                      │
│                                             Architect                 │
│                                                 │                      │
│                                          [DESIGN GATE]                │
│                                                 │                      │
│                                    ┌────────────┴────────────┐        │
│                                    │                         │        │
│                                 DevOps ◄──────────────────► QA        │
│                            (generate, RAG-           (test, review)   │
│                             template-driven)                          │
│                                    │                         │        │
│                                    └────────────┬────────────┘        │
│                                                 │                      │
│                                          [REVIEW GATE]                │
│                                                 │                      │
│                                             DevOps                    │
│                                     (version, CI, publish, deploy)    │
│                                                 │                      │
│                                         [RELEASE GATE]                │
│                                                 │                      │
│                                            (deployed)                 │
│                                                 │                      │
│              incident? ──────────────────► DevOps (first responder), │
│                                             QA verifies, Domain       │
│                                             Expert if root-cause is   │
│                                             domain-modeling           │
│                                                                        │
│         Mentor: continuous observation + gate coaching + post-mortem  │
│         Reporter: continuous documentation                            │
│         (both run alongside every stage above, not gated by any)     │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

| Gate | After | Before | Human Approves |
|------|-------|--------|----------------|
| **Vision Gate** | Domain Expert produces a research-backed domain brief | Domain Expert begins division discovery | Domain name, vision, brief |
| **Boundary Gate** | Domain Expert identifies divisions | Architect begins per-division design | Division names, boundaries, rationale |
| **Design Gate** | Architect produces EventStorm + desk inventory | DevOps/QA begin building | Aggregates, events, desk inventory, dependencies |
| **Review Gate** | QA has tested and reviewed generated code | DevOps prepares the release | Code quality, test results, anti-pattern compliance |
| **Release Gate** | DevOps has version-bumped and CI is green | Publish / deploy | Final go/no-go for shipping |

Between gates, agents work autonomously. Gate escalation is
process-manager logic, not an agent's judgment
call.

---

## Role File Structure

Each role file (`roles/{role}.md`) contains:

```markdown
---
id: role_id
name: Display Name
tier: T2
context:
  - philosophy/DDD.md
  - skills/NAMING_CONVENTIONS.md
---

{system prompt: identity + task + behavioral rules + output format}
```

### Context Loading

The `context:` frontmatter lists shared knowledge files the agent needs. The runtime:
1. Loads the role file → system prompt (always small, cheap)
2. Reads `context:` manifest → loads listed files as reference material
3. Context files are loaded ONCE per agent session, not per turn

### Context Budget

| Role | Context Files | Est. Input Tokens |
|------|--------------|-------------------|
| Domain Expert | 6 files | ~7K (rough — not measured) |
| Architect | 7 files | ~8K (rough — not measured) |
| DevOps | 8 files | ~10K (rough — not measured) |
| QA | 13 files | ~14K (rough — not measured) |
| Reporter | 3 files | ~3K (rough — not measured) |
| Mentor | 4 files | ~6K |

---

## Learning Loop

The Mentor operates continuously in three modes:

```
┌─────────────────────────────────────────────────────────┐
│                    LIVE (T3 — cheap)                     │
│  Watches every agent's output as it's produced.         │
│  Flags issues BEFORE downstream agents consume them.    │
│  One-line corrections. Pattern matching, not reasoning. │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                 GATE COACHING (T1 — per gate)            │
│  At each HITL gate, briefs the human:                   │
│  "Here's what looks good, here are my concerns."        │
│  Helps the human make better gate decisions.            │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│               POST-MORTEM (T1 — per run)                │
│  After RELEASE GATE: full retrospective.                │
│  Amends role files, antipattern docs, tier assignments. │
│  Encodes lessons permanently for the next run.          │
└─────────────────────────────────────────────────────────┘
```

**Why three modes:** A correction after the Architect costs 1 message. After QA it costs rework across every desk in the division. Catch early, fix cheap.

Every domain the team builds makes the next domain cheaper, faster, and higher quality. The role files are living documents that encode accumulated wisdom.
