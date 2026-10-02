---
title: Macula Corpus
layer: index
audience: [agent, human]
stage: stable
---

# Macula Corpus

*Shaping material for Macula agent runtimes — philosophy, skills, guides, guardrails.*

This repository is the corpus that shapes how Macula agents think and work. It contains no runtime code. It contains the doctrine that runtime agents (the crew roles, Apprentices, Codegen) load to align their behavior with Macula's principles.

---

## Start here

| You are | Read |
|---------|------|
| Human, first contact | [`INDEX.md`](INDEX.md) → follow Reading Path 1 (Apprentice) |
| Agent runtime (the crew) | [`INDEX.md`](INDEX.md) → Reading Path 2 (Agent runtime) |
| Tier-3 codegen LLM | [`INDEX.md`](INDEX.md) → Reading Path 3 (Codegen) |
| Looking for a term | [`GLOSSARY.md`](GLOSSARY.md) |
| Reviewing code | [`skills/antipatterns/INDEX.md`](skills/antipatterns/INDEX.md) |
| "How do I actually run/build X?" (practical, not architectural) | [`guides/FAQ.md`](guides/FAQ.md) |
| Want a narrative book version | [`CODEX.md`](CODEX.md) → The Macula Codex (draft) |

---

## Layout

| Layer | Where | Purpose |
|-------|-------|---------|
| **Soul** | `SOUL.md`, `PERSONALITY.md` | Identity, voice, values |
| **Philosophy** | `philosophy/`, `philosophy/alc/` | Mental models — the WHY |
| **Guides** | `guides/` | Walkthroughs — the HOW |
| **Skills** | `skills/`, `skills/antipatterns/`, `skills/codegen/` | Executable knowledge, guardrails, codegen |
| **Examples** | `examples/` | Concrete patterns |
| **Roles** | `roles/`, `agents/` | Personas |
| **Templates** | `templates/` | Parameterized codegen |

Full layout and reading paths in [`INDEX.md`](INDEX.md).

---

## The 5D Hierarchy

The structural backbone Macula uses everywhere:

```
Domain (problem space)
  └── Division (bounded context)
       └── Department (CMD | PRJ | QRY)
            └── Desk (single capability)

       Dossier flows through Desks, accumulating Slips
```

See [`GLOSSARY.md`](GLOSSARY.md) for full definitions. Note the explicit override notice on `Domain` — Macula Domain ≠ DDD bounded-context-domain.

---

## Contributing

Changes to this corpus shape how every Macula agent thinks. They are not casual edits.

- **Philosophy** changes affect mental models across all agents
- **Skills** changes affect generated code
- **Guardrails** (`skills/antipatterns/`) changes affect what fails review
- **Templates** changes affect what generated code looks like

Read [`INDEX.md`](INDEX.md) before opening a PR.

---

*The goddess shapes her servants.*
