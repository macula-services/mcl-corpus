---
title: The D5 model
layer: philosophy
audience: [agent, human]
stage: draft
---

# The D5 model

*One name for the way a Macula code base is laid out, so that it can be taught, cited and templated.*

The D5 model is five levels, each named with a word that starts with D. Four of them are nested places: a Domain holds Divisions, a Division holds three Departments, a Department holds Desks. The fifth is not a place. The Dossier is the thing that moves through the Desks and grows as it goes.

The name is a nod to Simon Brown's [C4 model](https://c4model.com), which gives architects four zoom levels for drawing a system. C4 says where the boxes are. D5 adds what moves through them, and that fifth level is the point.

Until this page existed the corpus called the same thing "the 5D hierarchy". The two names mean the same five levels. Write **D5 model**, with the letter first, the way C4 is written. "5D" is already taken by the building industry, where it means geometry plus time plus cost.

---

## The five levels

| Level | What it is | How many | Where it shows in code | Nearest term elsewhere |
|---|---|---|---|---|
| **Domain** | The whole business endeavour, the problem space | 1 | A GitHub organisation, or a set of repositories | DDD: the domain. C4: the system landscape |
| **Division** | One cohesive piece of software: a bounded context, with its own ubiquitous language | N per Domain | One repository | DDD: the bounded context. C4: a software system |
| **Department** | One of three roles inside a Division: CMD decides, PRJ records, QRY answers | exactly 3 per Division | One OTP application each: `host_bookclub`, `project_bookclub`, `query_bookclub` | CQRS: the write side, the projections, the read side. C4: a container |
| **Desk** | One capability. The atomic unit of work, of review and of estimate | N per Department | One folder: `register_member/` | Vertical slicing: one slice. C4: a component |
| **Dossier** | The aggregate: the folder of event slips that passes from desk to desk and grows as it goes | N per Division, one per process instance | An event stream; the stream id is the Dossier id | DDD: the aggregate. C4: nothing |

The first two levels carry a warning. **Domain** here is the senior DDD usage, the whole problem space. The thing DDD readers reflexively call a domain, the bounded context, is a **Division** in Macula and never a Domain. The full override notice is in [`GLOSSARY.md`](../GLOSSARY.md).

## What a Desk holds

A Desk in the command Department is four files, and a stranger can read it without a guide:

```
apps/host_bookclub/src/register_member/
    register_member_v1.erl       the command
    member_registered_v1.erl     the event, the Slip this desk adds to the Dossier
    maybe_register_member.erl    the business rule
    register_member_api.erl      the door the outside world knocks on
```

A Desk in the projection Department is one event to one table: `member_registered_v1_to_members`. A Desk in the query Department is one question with one answer: `get_member_by_id`. Where one Desk reacts to another's event, the reaction is its own Desk named after the policy it carries: `on_member_registered_v1_maybe_plan_party`.

Because every Desk has one of three shapes, a Desk can be produced from a template or by a language model and checked by a machine. That is what makes the Desk the unit of a work package, of a review, and of a price.

## How the Dossier moves

A Dossier enters at an `initiate_*` Desk, passes through other Desks, each adding its Slip, and leaves at a `conclude_*` or `archive_*` Desk. At any moment its state is fully determined by the Slips it carries. It is not a row that gets overwritten and it is not a directory; it is the event stream identified by its id. Rebuilding its state means reading the stream front to back. Validating a command means asking whether this Slip may be added to this Dossier.

The Dossier is the fifth D and not a sixth container on purpose. The four containers are places in the code base. The Dossier is what moves through them. Said aloud: five Ds, four nested, one flowing.

## What is not a sixth D

- **The Slip** is one event inside a Dossier: immutable, ordered, named `{subject}_{verb_past}_v{N}`. It is what a Desk adds, not a level.
- **The Decision** is a sibling write-side construct for the cross-cutting case that has no natural identity: uniqueness, allocation, idempotency keys, rate limits. It locks on the absence of matching events rather than on a stream version, and it has no identity, no lifetime and no folder. The rule for choosing between a Dossier and a Decision is in [`CONSISTENCY_BOUNDARIES.md`](CONSISTENCY_BOUNDARIES.md).

## What is borrowed and what is ours

Most of the D5 model is older than Macula, and the page says so.

- **Domain** and **Division** are DDD's domain and bounded context under names that keep the two scales apart.
- **Department** is CQRS: a write side, the projections that build read models from events, and a read side that only answers.
- **Event storming**, the practice that fills the levels from a wall of orange notes, is Alberto Brandolini's. [`EVENT_STORMING.md`](EVENT_STORMING.md) says what each note becomes in the D5 tree.
- **C4** is Simon Brown's, and we draw with it. A Division's `architecture/README.md` carries its C4 pictures.

What is ours is the fixed shape of the Desk as the unit of work, the Dossier as the thing that flows, and the rule that the five levels never grow a sixth. A one-person Domain with one Division and six Desks and a fifty-person Domain with fifteen Divisions and four hundred Desks have the same structure. You learn it once.

## Why a name

A convention without a name lives in the heads of the people who use it. A name lets a work package say "add one Desk", a review say "this Desk is five files, which one does not belong", an estimate say "eleven Desks", and a newcomer, human or agent, find any feature by reading folder names. It also lets a stranger cite it. That is the whole reason this page exists.

## Read also

- [`GLOSSARY.md`](../GLOSSARY.md), the canonical vocabulary and the Domain override notice
- [`DDD.md`](DDD.md), the Dossier principle: process over data
- [`VERTICAL_SLICING.md`](VERTICAL_SLICING.md), why a Desk holds everything it needs
- [`SCREAMING_ARCHITECTURE.md`](SCREAMING_ARCHITECTURE.md), why the names are verbs and facts
- [`CARTWHEEL.md`](CARTWHEEL.md), the three Departments in detail
- [`DOMAIN_LIFECYCLE.md`](DOMAIN_LIFECYCLE.md), how a Domain and its Divisions are built
- [`EVENT_STORMING.md`](EVENT_STORMING.md), from the wall to the tree
- [`../CODEX.md`](../CODEX.md), chapter 4, the long-form telling
- The book club, [mcl-bookclub](https://github.com/macula-services/mcl-bookclub), the worked example every path above comes from
