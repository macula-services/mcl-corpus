# PLAN: Retire the "hecate" and "martha" terminology

Status: **Q1 answered 2026-10-02: Hecate → Macula. P3 executed the same
day (file renames + mechanical pass + contextual fixes); P4 (internal
links) folded into P3. P5 external references done the same day
(macula-mcp plans, the mcl-chess plan, the retrieval skill description),
and the corpus's relative links, indexes and leftover names swept.
Remaining: re-seed the RAG index — the local hecate-rag stack is not
running on this machine.** The inventory and mapping below stay as the
migration record.

This exists so the corpus names what the workspace actually contains. The
services have physically moved to `macula-services` as `mcl-*`, the
daemon/plugin layers were deleted, and the corpus's own newest entries
(the antipatterns) already cite `macula-services/mcl-*` — while its older
pages still name the platform "Hecate" and the crew "Martha". The
GLOSSARY's own doctrine — *"Old names noted once, never repeated
inline"* — is the mechanism: one authoritative "formerly known as" note,
then the new names everywhere.

## Inventory (what is actually there)

| Kind | Where | Scale |
|---|---|---|
| Platform name "Hecate" | `SOUL.md`, `PERSONALITY.md`, `INDEX.md` ("Hecate Corpus"), `GLOSSARY.md`, and most `philosophy/` bodies (the tier model alone carries ~50) | corpus-wide |
| `HECATE_*` filenames | `philosophy/HECATE_AUTH_MODEL.md`, `HECATE_DOMAIN_LIFECYCLE.md`, `HECATE_TASK_MODEL.md`, `HECATE_TIER_MODEL.md`, `HECATE_WALKING_SKELETON.md`; the heading "HECATE ALC" in `philosophy/alc/README.md`; the `templates/hecate-app-template/` directory | 5 files + 2 names |
| Service names `hecate-*` | the tier model's naming row (`hecate-realm`, `hecate-rag`, `hecate-llm`, …), `hecate-citizens/mail/search/git/graph/stations/testkit/turn-credentials/victron/whiteboard/news` in guides and plans, `hecate-daemon/web/gitops` (already documented deleted) | ~20 names |
| "Martha" | `roles/AGENT_ARCHITECTURE.md` (title "Martha Agent Architecture"), `roles/NOTATION.md` (title "Martha Notation"), `hecate-martha`/`hecate-marthad`/`hecate-app-martha` in the tier model, codegen skill, mesh-tiering guide, PM FAQ, `antipatterns/documentation.md`; `macula-mcp/plans/PLAN_MARTHA_MULTI_AGENT_MCP.md` references | ~10 files + 1 external plan |

## Mapping (proposed — Q1 gates the first row only)

| Old | New | Verified against |
|---|---|---|
| "Hecate" (the platform) | **"Macula"** — Q1 | `macula-io`, `macula-services`, `mcl-*`, the Macula mesh; the corpus's own newest entries |
| `hecate-realm` | `macula-realm` | repo exists |
| `hecate-{citizens, mail, search, git, graph, stations, testkit, turn-credentials, victron, whiteboard, news}` | `mcl-{…}` | all verified in `macula-services/` |
| `hecate-rag` | `mcl-rag` | verified |
| `hecate-om` | `mcl-om` | verified |
| `hecate-daemon`, `hecate-web`, `hecate-gitops` | stay deleted — "removed 2026-09-05, historical only" (already documented) | tier model |
| `hecate-llm` | unmapped — no `mcl-llm` exists; keep the name until one does | `macula-services/` listing |
| `hecate-passport` | unmapped — no twin seen | `macula-services/` listing |
| "Martha" (the six-role crew) | **"the crew"** | PLAN_MARTHA already treats it as retired |
| `hecate-martha`/`-marthad`/`hecate-app-martha` | removed — historical | tier model |
| `roles/AGENT_ARCHITECTURE.md` title | "Agent Role Architecture" | — |
| `roles/NOTATION.md` title | "Role Notation" | — |
| `HECATE_AUTH_MODEL.md` | `AUTH_MODEL.md` | — |
| `HECATE_DOMAIN_LIFECYCLE.md` | `DOMAIN_LIFECYCLE.md` | — |
| `HECATE_TASK_MODEL.md` | `TASK_MODEL.md` | — |
| `HECATE_TIER_MODEL.md` | `TIER_MODEL.md` | — |
| `HECATE_WALKING_SKELETON.md` | `WALKING_SKELETON.md` | — |
| "HECATE ALC" heading | "The ALC — Division Application Lifecycle" | alc/README title already reads that |
| `templates/hecate-app-template/` | `templates/app-template/` | — |
| `GLOSSARY.md` header | "Canonical vocabulary — formerly known as the Hecate terms" — the one allowed mention | glossary's own doctrine |

## Phases

- **P1 — landed with this plan.** `philosophy/AGGREGATE_LIFECYCLE_SLICES.md`
  and `skills/EVOQ_BIT_FLAGS.md`, both written neutral from day one, plus
  the cross-links in `STATUS_LABELS_IN_PROJECTIONS.md` and the `INDEX.md`
  reading path.
- **P2 — the gate.** Operator answers Q1 (platform name). Nothing renames
  before it.
- **P3 — the mechanical pass.** File renames + front-matter titles + body
  replacements per the mapping table, one commit per document (or per
  tight group), each diff reviewed — never a blind `sed`. The GLOSSARY
  gains the single "formerly known as" note.
- **P4 — internal links.** Cross-references inside the corpus, the INDEX
  reading paths, the FAQ index.
- **P5 — external references and indexing.** `macula-mcp` plans cite
  corpus paths by filename (`PLAN_AGENT_CONVERSATIONS.md` names
  `hecate-services/hecate-citizens`; the Martha plan is referenced by
  name); fix or note them. Re-seed the RAG index after P3, and update the
  retrieval skill's description.

## Out of scope (heavier, separate steps)

- Renaming the GitHub orgs/repos (`hecate-services`, `hecate-social`,
  `hecate-corpus`) — git/GitHub operations, not a doc pass.
- Renaming `macula-mcp/plans/PLAN_MARTHA_MULTI_AGENT_MCP.md` — a pass in
  that repo.
- Rewriting the tier model's deleted-layer history beyond its existing
  "REMOVED" notes — history stays history.

## Risks

- **Broken external links** — other repos cite corpus files by name; P5 is
  not optional, it is what keeps the mesh of links true.
- **Blind mechanical edits** — the mapping table is the guard; every
  replaced occurrence is reviewed in context.
- **RAG staleness** — the retrieval index must be re-seeded or it answers
  with dead names for weeks.
- **Skill staleness** — the hecate retrieval skill names itself after the
  old term; updated in P5.

## Q1 — the one decision that gates execution

**What replaces "Hecate" as the platform name?**

Recommendation: **"Macula"** — it matches the workspace reality
(`macula-io`, `macula-services`, `mcl-*`, the Macula mesh), keeps one
proper noun for the whole stack, and the corpus's newest entries already
speak that way. The alternative is retiring to neutral terms only ("the
division architecture", "the corpus", "the crew"), which reads cleanly but
loses the one name that binds the stack together.
