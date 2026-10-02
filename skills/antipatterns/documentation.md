---
title: "ANTIPATTERNS: Documentation"
layer: skill
audience: [agent, human]
stage: stable
---

# ANTIPATTERNS: Documentation — History Narration in Operational Docs

*One demon so far. It happened three times in one afternoon before it got named.*

[Back to Index](INDEX.md)

---

## 🔥 History Narration in Operational Docs

**Date:** 2026-09-01
**Origin:** the crew roster redesign session — `roles/AGENT_ARCHITECTURE.md`,
`macula-mcp/plans/PLAN_MARTHA_MULTI_AGENT_MCP.md`, and four role files all
picked up the same habit independently, in the same afternoon.

### The Antipattern

A PLAN, guide, or role file narrates its own revision history instead of
stating the current fact:

```markdown
**Corrected 2026-09-01, twice.** First pass: the original design routed
every agent call through `serve_llm` unconditionally — wrong once roles
are exposed to arbitrary MCP harnesses. Second pass, a real mistake
caught the same day: the first correction still described a removed
backend service calling a model directly for "background" work...
```

This reads fine the moment it's written, because the author (human or
agent) just lived through the correction and the story is fresh. It
reads as noise to everyone else: a reader who wants to know "does
any service call a model" has to parse two abandoned positions to
find the one that's still true. And it doesn't even stay accurate on its
own terms — this exact passage needed a **third** correction later the
same day, at which point "corrected... twice" was itself wrong, and nothing
caught that until a human did.

**Why this one is worse than an ordinary stale comment**: this corpus is
the retrieval source for `mcl-rag`. A role querying "how does model
routing work" gets back whatever text is there — it doesn't know to
discount the "first pass said X, that was wrong" clause as scaffolding
around the real answer. Narration written for a human mid-conversation
becomes misinformation the moment it's serving an agent's retrieval.

### The Rule

> **Operational docs (PLANs, guides, role files, philosophy docs) state
> current fact only. History — what changed, when, and why — belongs in
> `CHANGELOG.md` and nowhere else.**

If a past mistake is worth recording because the *lesson* generalizes
(not just "we changed our mind"), it belongs here, as its own demon —
not as a footnote in the document the mistake was made in.

### The Mechanism That Refuses It

Per this index's own rule (see `INDEX.md`, "Before You Add a Demon
Here" and Demon #55): naming the antipattern in prose doesn't stop it.
Run this before committing any PLAN/guide/role-file change — it's a
plain grep, not a new tool, and it catches the exact shape of the
mistake above:

```bash
# From a repo root. Excludes CHANGELOG.md; everything else that matches
# is a document narrating its own history instead of stating fact.
grep -rniE \
  '(corrected|revised|fixed|reworked|added) 20[0-9]{2}-[0-9]{2}-[0-9]{2}|as of 20[0-9]{2}-[0-9]{2}-[0-9]{2}|added 20[0-9]{2}-[0-9]{2}-[0-9]{2} because|later the same (day|week)|this reverses|first pass|second pass|absorbed 20[0-9]{2}|what changed \(20|used to (say|be)|previously (said|read)' \
  --include='*.md' \
  --exclude='CHANGELOG.md' \
  .
```

A non-empty result is a finding, not a judgment call — move the content
to `CHANGELOG.md`, or drop it if it was never more than "we changed our
mind." `PLAN_*.md` files with a `Status:` line tracking phase progress
(e.g. `PLAN_MACULA_MCP.md`'s "Phase 1 + 2 landed; Phase 3 spec'd") are
not a violation — that's current state, not a narrated correction.

### A README's own "Status"/"Changelog" section is the same demon at scale

`macula-mcp/README.md` had a `## Status` section that was, functionally,
a second changelog: version-by-version prose ("v0.5.0 — mesh_hello...,
2026-08-30", "Dropped in this rework, not carried over...") duplicating
`CHANGELOG.md` almost line for line, plus inline instances scattered
through the operational sections above it ("As of 2026-08-31, `mesh_hello`
already starts...", "Added 2026-08-31 because...", "Later the same day:
presence stopped requiring `mesh_hello` at all.", "This reverses
`mesh_watch`'s own earlier design note..."). None of the regex above
caught it — the mistake didn't repeat its exact phrasing, it repeated
the *shape*: a dated claim about when/why something changed, sitting in
a doc a reader consults for current behavior. Grep now covers `reworked
DATE`, `as of DATE`, `added DATE because`, `later the same day/week`,
and `this reverses`, but treat that list as a floor, not a ceiling — a
README `Status` section is worth a manual skim for this shape even when
the automated check is clean, since a `Status`/`Changelog` heading is
exactly where a rewritten history feels most natural to leave in place.
