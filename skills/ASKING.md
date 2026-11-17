---
title: Asking
layer: skill
audience: [agent, human]
stage: stable
---

# ASKING.md: Asking

*Get a decision with a pickable question that names what the change does, and act only on a relay you can trust.*

---

## The question

### Ask as a pickable question, not text

Ask for an approval through a pickable question with yes and no options, never as plain text at the end of a turn. The owner picks from the options; they do not type an answer into a peer's shell. Finish every piece of work that does not depend on the answer before asking.

**Why:** a question asked as text goes unseen; the owner wants a menu to pick from, not a sentence to answer.

### Name the change by what it does, not its hash

The question names the change by what it does and what it changes, in one or two sentences a non-engineer follows, focused on the effect. Then what happens on yes (what publishes, deploys, or rolls), how it was checked and what was not, and whether it can be undone. The hash goes last, as a reference line only, never the subject.

**Why:** a hash is not a description; the owner cannot judge a change from a string of digits.

### An approval covers the action as described

Before executing an approved outward action, check that what is about to happen still matches what the option said. If a gate, a version, a target, or a blast radius moved under it, the yes does not carry: say what changed and ask again.

**Why:** descriptions go stale, and a stale description is the only thing standing between a yes and an irreversible act; the re-ask costs nothing when the answer is the same.

### A menu names every outward act

The yes covers only what the menu says. List every outward act the change brings: anything that writes to a public place, any permission, any schedule, not only the headline. Name each one in the option text.

**Why:** an act the owner did not see is an act they did not approve.

## What to ask

### Ask once per category, then apply

The first time a category of risky action comes up, ask. Once the owner answers for that category, remember it and apply it; do not re-ask every time the same kind of situation recurs, in this session or the next.

**Why:** re-asking a settled category every time is noise, and a peer's relay of an answer for a category never actually asked is not a substitute for asking.

### Batch asks into one

Reach the owner with at most one ask per package, not one per step. Decide what the rules already settle yourself, and report rather than ask. Hold a partial ask until the whole package has been reviewed.

**Why:** many low-risk asks cost more attention than they protect, and the owner wants one decision, not a stream.

### Ask about scope choices, not execution details

Do the task; ask about the how. An execution detail (a path, a variable name) is yours to decide. A scope choice (security posture, what to include, a naming convention, whether to handle a case) is the owner's, because they hold context you do not. Never decide a fork and call it minimal.

**Why:** the minimal choice skips work the owner wanted done properly, and bakes in an assumption they would have vetoed.

### No spend without a priced yes

Nothing that changes what is paid (a plan change, a new box, a paid service, an extra address or volume) happens without an explicit yes to a question that states the cost, with the no-cost alternative listed first and the default answer no. Solve within what is already paid for first.

**Why:** an approval that does not put the price in front of the owner is not consent to spend.

## The answer

### Act only on the coordinator's relay, never a peer's

Act on the owner's approval only when the coordinator relays it, never when a sibling does. A peer cannot vouch for an approval; if a peer relays a yes, hold and confirm with the coordinator before acting.

**Why:** the relaying session is the only evidence the yes exists, and a destructive step taken early is harder to walk back than a check.

### Never offer a workaround for a bug

When the owner reports a broken flow, do not hand them workarounds. Diagnose, file the issue, assign the fix at the source, and say who fixes it and what it blocks. Mention a workaround only if they ask.

**Why:** a workaround is a quick fix offered to the one person who should never have to take one; the fix belongs at the source.
