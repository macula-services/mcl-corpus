---
title: Role Notation
layer: role
audience: [agent]
stage: stable
---

# Role Notation

*Compact inter-agent protocol for the domain pipeline.*

**Date:** 2026-03-11
**Status:** Active

---

## Purpose

Agents communicate using a line-oriented structured notation instead of verbose prose. This:
1. **Saves tokens** — ~50% smaller than markdown descriptions
2. **Eliminates ambiguity** — one construct per line, keyword first
3. **Enables parsing** — any consumer extracts structure without LLM calls (zero tokens), whether that's a harness's own tooling or a human skimming it
4. **Is human-readable** — technical humans read it directly at HITL gates

---

## Rules

- One construct per line. No multi-line values.
- Keyword first, UPPERCASE. Content follows.
- Indentation = nesting (2 spaces per level).
- Field lists in square brackets: `[field1 field2 field3]`
- Strings with spaces in double quotes: `"Invoice processing"`
- Agents produce notation for inter-agent output. Prose only for human-facing interaction (Domain Expert ↔ human, Mentor gate briefings).

---

## Division Spec (Domain Expert → Architect)

```
DIV {context_name} "{description}"
  OWNS {concept1} {concept2} ...
  PUBLISHES {fact_name}
  CONSUMES {fact_name} FROM {division}
```

Example:
```
DIV billing "Invoice and payment processing"
  OWNS invoice payment account_receivable
  PUBLISHES invoice_paid_fact payment_received_fact
  CONSUMES customer_registered_fact FROM auth
```

---

## EventStorm Output (Architect Stage 1 → Architect Stage 2)

```
AGG {name} {stream_pattern}
  FLAGS {NAME=value} ...
  WALK {initiate_desk} {archive_desk}
  DESK {verb_subject} -> {event_v1} [{field1} {field2} ...]
  PM {pm_name} -> {target_division}
```

Example:
```
AGG invoice invoice-{invoice_id}
  FLAGS INITIATED=1 ARCHIVED=2 ISSUED=4 PAID=8 VOIDED=16
  WALK initiate_invoice archive_invoice
  DESK issue_invoice -> invoice_issued_v1 [invoice_id domain_id division_id amount currency issued_by issued_at]
  DESK pay_invoice -> invoice_paid_v1 [invoice_id paid_by paid_at amount method]
  DESK void_invoice -> invoice_voided_v1 [invoice_id voided_by reason]
  DESK archive_invoice -> invoice_archived_v1 [invoice_id]
  PM on_invoice_paid_notify_customer -> notifications
```

---

## Technical Spec (Architect → DevOps)

```
APP {app_name} {CMD|PRJ|QRY}
  SUP {sup_name} {strategy}
    EMIT {event}_v1_to_mesh
    PM {pm_name}
  STORE {store_name}
    TABLE {table} [{col:type} ...]
  PROJ {event_v1} -> {table} {INSERT|UPDATE} [{col} ...]
  QUERY {name} {METHOD} {path}
```

Example:
```
APP guide_billing CMD
  SUP guide_billing_sup one_for_one
    EMIT invoice_issued_v1_to_mesh
    EMIT invoice_paid_v1_to_mesh
    EMIT invoice_voided_v1_to_mesh
    EMIT invoice_archived_v1_to_mesh
    PM on_invoice_paid_notify_customer

APP project_billings PRJ
  STORE project_billings_store
    TABLE billings [division_id:pk domain_id:text status:int status_label:text available_actions:text]
    TABLE invoices [invoice_id:pk division_id:text amount:int status:int status_label:text]
  PROJ invoice_issued_v1 -> invoices INSERT
  PROJ invoice_paid_v1 -> invoices UPDATE [status status_label available_actions]

APP query_billings QRY
  QUERY get_billing_by_id GET /api/billings/:division_id
  QUERY get_invoices_page GET /api/billings/:division_id/invoices
  QUERY get_invoice_by_id GET /api/billings/:division_id/invoices/:invoice_id
```

---

## Lifecycle State

```
PHASE {code} STATUS={int} LABEL="{string}" ACTIONS=[{action1} {action2}]
```

Example:
```
PHASE planning STATUS=5 LABEL="Open" ACTIONS=[shelve conclude]
PHASE crafting STATUS=1 LABEL="Initiated" ACTIONS=[open]
```

---

## Kanban Items

```
ITEM {id} TYPE={cmd_desk|prj_desk|qry_desk|ui_slice|sql_schema|test_suite|review|release} STATUS={ready|picked|done} "{title}"
```

Example:
```
ITEM i-001 TYPE=cmd_desk STATUS=ready "issue_invoice"
ITEM i-002 TYPE=cmd_desk STATUS=picked "pay_invoice"
ITEM i-003 TYPE=prj_desk STATUS=done "invoice_issued_v1 -> invoices"
```

---

## Mentor Flags

```
FLAG {agent} {CRITICAL|MAJOR|MINOR} "{message}"
AMEND {file} +"{rule to add}"
AMEND {file} -"{rule to remove}"
```

Example:
```
FLAG architect MAJOR "invoice_created is CRUD — rename to invoice_issued"
FLAG devops MINOR "missing @doc on maybe_issue_invoice"
AMEND roles/architect.md +"Financial events: issued/voided/settled, never created/updated"
```

---

## Gate Verdicts

```
GATE {gate_name} {PASS|FAIL} "{reason}"
```

Example:
```
GATE boundary_gate PASS "5 divisions, clean boundaries"
GATE review_gate FAIL "3 critical findings"
```

---

## Cost Tracking

```
COST {agent} {tokens}K ${amount}
TOTAL {tokens}K ${amount}
```

Example:
```
COST architect 4.2K $0.03
COST devops 12.1K $0.02
COST qa 8.5K $0.12
TOTAL 38.2K $0.24
```

---

## Status Updates

Self-reported by whichever agent completes a unit of work. There is no
backend service that tracks pipeline state — see `philosophy/alc/README.md`
"Coordination": a gate crossing is a git commit, announced over mesh by
the agent that made it, not dispatched by a process manager.

```
STATUS {division} {agent} {message}
```

Example:
```
STATUS billing architect COMPLETE
STATUS billing devops STARTED
STATUS auth devops 3/5
```

---

## Quick Reference

| Keyword | Producer | Consumer | Purpose |
|---------|----------|----------|---------|
| `DIV` | Domain Expert | Architect | Division boundary |
| `AGG` | Architect (Stage 1) | Architect (Stage 2) | Aggregate definition |
| `DESK` | Architect (Stage 1) | Architect (Stage 2) | Desk → event mapping |
| `FLAGS` | Architect | DevOps | Bit flag definitions |
| `WALK` | Architect (Stage 1) | Architect (Stage 2), QA | Walking skeleton check |
| `PM` | Architect (Stage 1) | Architect (Stage 2), DevOps | Process manager |
| `APP` | Architect (Stage 2) | DevOps | App scaffold |
| `SUP` | Architect (Stage 2) | DevOps | Supervision tree |
| `STORE` | Architect (Stage 2) | DevOps | Store + tables |
| `TABLE` | Architect (Stage 2) | DevOps | Schema definition |
| `PROJ` | Architect (Stage 2) | DevOps | Projection mapping |
| `QUERY` | Architect (Stage 2) | DevOps | API endpoint |
| `PHASE` | Whichever agent reports it | All | Current lifecycle state |
| `ITEM` | Whichever agent reports it | DevOps, QA | Kanban item |
| `FLAG` | Mentor | Target agent | Live correction |
| `AMEND` | Mentor | (role files) | Post-mortem improvement |
| `GATE` | The agent making the gate commit | Human, Mentor | HITL checkpoint |
| `COST` | Each agent, self-reported | Mentor | Token spend tracking |
| `STATUS` | Whichever agent completes the work | All | Pipeline progress |
