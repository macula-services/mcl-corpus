---
title: Martha Event Storming, How We Open a Storm
layer: philosophy
audience: [agent, human]
stage: stable
---

# MARTHA_EVENT_STORMING.md — How We Open a Storm

*Four named phases that put every expert's own notes on the wall before anyone has heard anyone else, so that the wall the group ends with is one each of them recognises.*

---

## The claim

Event storming is Alberto Brandolini's practice, and [`EVENT_STORMING.md`](EVENT_STORMING.md) says what each note on the wall becomes in the tree. This page is about the hour before that: how a storm is opened.

In the usual opening everyone writes at the same wall and sees every note as it goes up. The first notes set the vocabulary, the confident voices set the pace, and the person who knows the awkward exception often never writes it down. We open differently. Everyone writes alone first, nobody sees a neighbour's notes, and only then are the notes brought together. What each person knew is on the wall before the group starts to agree.

Two things are ours here: the four phases, with their names, and the weight a note carries out of them.

---

## Who stands at which wall

| Wall | What it models | Who stands at it |
|---|---|---|
| **The big picture** | the whole business: the Domain | people from across the business |
| **A Division's wall** | one process inside that business, such as procurement or shipping | the people who know that process best |

Both are business walls. A Division's wall is not handed to the builders: the shipping experts stand at the shipping wall. The big picture comes first, since it decides where one Division ends and the next begins; each Division is then stormed on its own wall, with its own people.

Each of those storms opens with the same four phases.

---

## The four phases

| | Phase | What happens | Ends when |
|---|---|---|---|
| 1 | **High Octane** | Everyone works alone and in silence, and cannot see anyone else's notes. One goal: as many orange notes as possible. | the timer runs out, after ten to fifteen minutes at most |
| 2 | **Merge the Experts** | Everyone's notes come onto the group wall, one row per participant. Notes that name the same event are stacked. | every row is empty |
| 3 | **One Wording** | The group settles one wording for each stack. The surviving note carries its weight. | every stack has its wording, or is a hot spot |
| 4 | **Complete the Wall** | The group adds what is missing, by discussion. | the group has nothing to add |

The facilitator starts and ends each phase and keeps the timer.

### 1. High Octane

An orange note is an event: something that happened, in the past tense, in the words the writer would use at work. `member registered`. `book procured`.

- **Alone.** No talking, and no looking at a neighbour's notes. This is the point of the phase, not a courtesy: a note written after reading someone else's is partly theirs.
- **Fast.** Volume over polish. A badly worded event is welcome; a missing one cannot be fixed later by anyone but its author.
- **Short.** Ten minutes, fifteen at most. The time limit is what keeps people from editing themselves.

### 2. Merge the Experts

Every participant's notes appear on the group wall, in a row that carries the participant's name. Now everyone reads everyone's notes, for the first time.

Notes that name the same event are put on top of each other. Identical wordings are the easy stacks. The others are the conversation the phase exists for: is "order placed" in the sales row the same event as "order received" in the warehouse row?

A row empties as its notes are stacked or moved to the shared wall. When every row is empty, the merge is done.

### 3. One Wording

For each stack the group agrees on one wording, and that note survives.

- **The surviving note carries its weight** in its top left corner: the number of people who named the event.
- **The wordings that lose are kept** behind the surviving note, not thrown away. Everyone can still find their own note there.
- **A stack can be split again.** If two notes turn out to name different events, they are two events.
- **A stack with no agreed wording is a hot spot.** It stays on the wall as a question.

### 4. Complete the Wall

The group now works as a group. It puts the events in order, adds the ones nobody wrote, and from here the storm runs as [`EVENT_STORMING.md`](EVENT_STORMING.md) describes: pivotal events and candidate Divisions on the big picture; commands, policies, read models and hot spots on a Division's wall.

Walk the notes with weight 1 on purpose in this phase. They are the next section's subject.

---

## Reading the weight

The weight says **how many people named the event**. It does not say how much the event matters.

| Weight | What it tells you |
|---|---|
| high | Everyone knows this happens. A candidate for a pivotal event. |
| 1 | One person knows this happens. Often the exception, the edge of the process, the thing the workshop was called to find. |

A note with weight 1 is not a weak note. Ask its author to tell the story; it is frequently the most useful five minutes of the session.

**The weight counts people, not notes.** Someone who wrote the same event twice counts once.

**The losing wordings are evidence.** Two groups using different words for one event is the sign [`EVENT_STORMING.md`](EVENT_STORMING.md) gives for a Division boundary: where the vocabulary changes, a Division ends.

---

## The expert agent

Experts are busy, and some never make it to the room. The work still has to progress. An agent may take part in High Octane as an expert after study: it has read what is public about the kind of business, and it writes its orange notes like anyone else.

- **It has its own row, named for what it is**, such as "Expert after study of the internet". Nobody mistakes its notes for a colleague's.
- **Its notes count apart.** A weight is written as people plus agents, `4 + 1 agent`, so the first number still says how many people in the room named the event.
- **It writes in High Octane like everyone else:** alone, without seeing the others' notes.

---

## The Definition of Dossier

A wall of events says what happens and who does it. It does not yet say what is known. The Definition of Dossier fills that in: for each dossier, **the names of what is known about it, and which event makes each known**.

It is not a separate step and not a data model drawn up front. It emerges from a Division's wall. At each orange note the group answers one question: *what do we know now that we did not know before?*

> "At `shipment released`, I need the date it was released by customs."
> "At `part received`, I need to know that part's serial number."

Those two sentences are the definition at work: a name, and the event that makes it known. The sum of those answers, per dossier, is its definition.

Two consequences:

- **An event's payload is a subset of its dossier.** Every field of an event is a field of the dossier ([`DDD.md`](DDD.md), "The Default Read Model and Data Flow").
- **One definition per dossier, not one model for the business.** A book club has four dossiers: the club, a member, a book, a reading. Where one refers to another it holds an id, and nothing more.

Names only. Types, status flags and which slip is allowed when are technical design, and come after the storm (`roles/architect.md`, Stage 2).

---

## The wall belongs to the business

Everything above follows from one principle: **the wall belongs to the business, not to the engineers.**

- **The test.** Before anything goes on the wall, ask: could the people standing here answer this? They can say what a registration makes known. They cannot say in what order lookups run, so a command's pipeline is not drawn at the wall ([`COMMAND_PIPELINES.md`](COMMAND_PIPELINES.md); Demon 75 in [`skills/antipatterns/domain.md`](../skills/antipatterns/domain.md)).
- **Recognition.** People must recognise today what they worked on yesterday. Their notes stay where they put them and look the way they left them. Nobody is shown a tidied diagram in place of their own work: the content may be right, and they will still not see it as theirs.
- **A note that is mine.** Because the storm opens with High Octane, every participant has notes on the wall, and after One Wording can still find them behind the surviving ones.

Business people follow lines and arrows without trouble. What loses them is a wall they did not make.

---

## What this page is not

- **Not the wall-to-tree rule.** What each note becomes in a Division's tree is [`EVENT_STORMING.md`](EVENT_STORMING.md).
- **Not a full facilitation guide.** It covers the opening and the principle behind it. Running the room beyond that is in Brandolini's book and the community cheat sheet.
- **Not a tool.** The phases work with paper, a screen between neighbours and a kitchen timer.

---

## See also

- [`EVENT_STORMING.md`](EVENT_STORMING.md): the notes, the lane form, and what each note becomes.
- [`D5_MODEL.md`](D5_MODEL.md): Domain, Division, Department, Desk and the Dossier that moves through them.
- [`DDD.md`](DDD.md): the Dossier Principle, and what an event carries.
- [`COMMAND_PIPELINES.md`](COMMAND_PIPELINES.md): how a command is prepared, which is the builder's work.
- [`GLOSSARY.md`](../GLOSSARY.md): the storming vocabulary.
- `agents/storm_big_picture/oracle.md`, `agents/storm_design_level/oracle.md`: the agent that plays the expert.
