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

### A small failure is fixed by the reviewer

When a failure's required items are only hygiene (a stale comment, a restated literal, wording), a weak test pin, or a small real bug (about 30 lines, no design change), the reviewer fixes them on the change's branch instead of sending them back:

1. Tell the author before pushing, so they hold their own pushes.
2. Fix it, and show that each mutant that survived now dies.
3. Push, and wait for CI to pass on the new tip.
4. Report the verdict as FIXED, naming the fix commit.

The original author then reviews that commit, those lines only, and records the lesson learned in the shared corpus.

A design change, or anything security-sensitive (tokens, credentials, process signals, landing gates), still goes back to the author as a failure, with every item in it.

**Why:** a full round trip for a few lines costs more than the fix, and the author still sees the fix and learns from it. Sensitive and design changes stay with the author, because those are where a second mind matters most.

## A terminal screen never holds a string whole

A full-screen terminal program redraws only the cells that changed, and pads a wrapped line with its own margin. So the raw bytes of a recorded screen drop characters and split words: a command shown whole on the screen can be kept with letters missing. A redactor that looks for a secret's exact value in those bytes can miss it, even after removing line breaks and escape sequences.

**How to apply:** when reviewing a redactor over a recorded screen, test a wrap with a padded continuation line and a line with characters missing, not only a plain line break. Prefer that the screen is not kept once the secret is in play. Structured logs that hold whole strings can be redacted reliably.

**Why:** a review asked for "remove the breaks and escapes, then look again". The author built exactly that, and a padded wrap still kept the whole secret. The review's own request was too narrow.
