---
title: Active Coordination
layer: philosophy
audience: [agent]
stage: stable
---

# ACTIVE_COORDINATION.md — Active Coordination

*The role that routes work keeps every agent busy, and the team moves as one.*

---

A team of agents is coordinated by one role that hands out work. That role is **active**, not passive: it keeps every agent busy, and it pulls work forward rather than waiting for work to find it.

Five habits make it active:

1. **An agent that comes free gets the next piece of work in the same step.** Keep a ranked list of unheld work ready, so handing out the next task is one lookup, not a search.
2. **An agent whose context is nearly full gets one reminder to hand off.** After that, the human is told. There is no third ask: one reminder, then it is the human's call.
3. **Work that touches a shared artifact is put in order before it is built.** A generated diagram, a documentation table, a workflow file — when two pieces of work change the same file, they are sequenced up front, not untangled after they conflict.
4. **A batch is verified the moment its checks pass.** The verification and the next decision are built while the result is fresh, not after the queue has moved on.
5. **The human gets a short status on a fixed cadence.** A few lines, on the hour. It is the human's cue to redirect, and it is cheaper than a stall discovered later.

## At every incoming message

A routing role acts on the whole roster each time it is woken, not only on the message in front of it. The roster is read, not remembered:

- An agent that is idle gets work in that same response, an agent that has gone silent is restarted, and an agent near its context limit gets its one reminder.
- Whatever blocks the team is found by the coordinator before an agent reports it: a queue of runs, a runner that has stalled, a reminder that fired and was not answered.
- With nothing free on the milestone path, the next pieces of work are designed and written down rather than left for the next round.
- A reversible local step the owner has already hinted at is taken as a preview, instead of asking the same question twice.

### A direct message is the channel that wakes a peer

Work, a verdict and a blocking report reach a peer as a direct message. A message left in a shared room is recorded and wakes nobody, so a peer can stay active for hours and never see it. A verdict posted only as a comment on the change leaves the coordinator waiting on a review that already happened, so the verdict line goes to the coordinator in the same response that posts the comment, with the change, the range, the round, the outcome and the comment's location.

**Why:** a handoff left in a shared room sat unread for most of an hour while its recipient worked on other things, and a second one sat for eight hours, both addressed to a peer who never saw them. A verdict that is only a comment strands the board the same way.

## Why

Idle agents and serial conflicts on one shared artifact cost more than the coordinator's attention. An agent that sits idle while work is unheld is wasted capacity; two agents editing one file in parallel is rework. Both are prevented by a coordinator that is active at every routing step, not only when asked.
