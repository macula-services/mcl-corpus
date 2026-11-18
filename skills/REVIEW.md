---
title: Review
layer: skill
audience: [agent, human]
stage: stable
---

# REVIEW.md: Review

*Read the change yourself, treat every finding as required, and stop at the second failed round.*

---

## The review itself

### Read the change yourself

Before anything goes upstream, read the diff yourself. Never trust a summary, a secondhand account, or a grep. A shortcut a maintainer has to point out costs the author's reputation, not just a redo.

**Why:** the change carries the author's name, and the reviewer is the last person who can catch the shortcut before it is public.

### Every finding is required

Every bug a review finds is a required change. No cap on the count, no downgrading a bug to an observation, no "fold it into your next change". Observations are only for non-bugs, such as style or wording.

**Why:** real defects get parked as optional observations and never fixed.

### One review per change

One review per change. No second reviewer, and no diff-only re-review after a small fix: the author fixes it and a green run on the exact tip is the check.

**Why:** review rounds are the dominant cost, and the second round rarely finds what the first could not.

## When a review keeps failing

### Two failed rounds means a scope question

When a change fails review twice and each fix opens new findings, stop relaying rounds and bring a scope menu: cut scope for one last round, park now, or keep going.

**Why:** when the new findings are in machinery the previous round added, the question itself is malformed, and more rounds will not settle it.

### A hygiene-only failure folds in

A failure whose required items are all hygiene, such as a stale comment, a restated literal, wording, or a doc line, is folded in by the author. The reviewer then checks only those lines, with no new round. A behaviour or security bug still gets a full round.

**Why:** hygiene does not deserve another full round, and the reviewer names the exact fix so it can be checked in isolation.
