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

### Read while CI runs, send the verdict on green

Start reading the change as soon as it is handed over, while its CI runs. Send the verdict only once every run on the exact tip has passed. A verdict with a run still pending is not sent, and a run that fails turns a PASS into a FAIL.

**Why:** reading after CI finishes adds the whole CI time to every round, and a verdict sent before the runs finish passes a tip nobody has seen pass.

## When a review keeps failing

### Two failed rounds means a scope question

When a change fails review twice and each fix opens new findings, stop relaying rounds and bring a scope menu: cut scope for one last round, park now, or keep going.

**Why:** when the new findings are in machinery the previous round added, the question itself is malformed, and more rounds will not settle it.

### The reviewer says when its own request was too narrow

A first-round request can be too narrow: the author builds exactly what was asked, and the threat is still open. When the second round finds this, the reviewer says so plainly in the verdict: the fix meets the request, the request missed the threat, and here is the wider one. That failure counts as the second, so the next step is the scope menu above, not a third round.

**Why:** an author who did exactly what was asked and fails again reads the second failure as moved goalposts. Naming the reviewer's own narrow request keeps the record honest and sends the scope question to the owner instead of into more rounds. See the redaction case under "A terminal screen never holds a string whole" below.

### A small failure is fixed by the reviewer

When a failure's required items are only hygiene (a stale comment, a restated literal, wording), a weak test pin, or a small real bug (about 30 lines, no design change), the reviewer fixes them on the change's branch instead of sending them back:

1. Tell the author before pushing, so they hold their own pushes.
2. Fix it, and show that each mutant that survived now dies.
3. Push, and wait for CI to pass on the new tip.
4. Report the verdict as FIXED, naming the fix commit.

The original author then reviews that commit, those lines only, and records the lesson learned in the shared corpus.

The branch has one owner per round: the reviewer from the moment it says it holds the branch until it reports FIXED, the author before and after. Only the owner pushes.

**How to apply:** an author who is told the reviewer holds the branch stops pushing at once. A push it cannot avoid is announced first, with the new tip, so the reviewer fixes on the right base.

A design change, or anything security-sensitive (tokens, credentials, process signals, landing gates), still goes back to the author as a failure, with every item in it.

**Why:** a full round trip for a few lines costs more than the fix, and the author still sees the fix and learns from it. Sensitive and design changes stay with the author, because those are where a second mind matters most.

## A terminal screen never holds a string whole

A full-screen terminal program redraws only the cells that changed, and pads a wrapped line with its own margin. So the raw bytes of a recorded screen drop characters and split words: a command shown whole on the screen can be kept with letters missing. A redactor that looks for a secret's exact value in those bytes can miss it, even after removing line breaks and escape sequences.

**How to apply:** when reviewing a redactor over a recorded screen, test a wrap with a padded continuation line and a line with characters missing, not only a plain line break. Better: keep no screen at all once a secret is live, only transcripts. A screen cannot be redacted by value, so the only safe screen is one never written. Structured logs and transcripts that hold whole strings can be redacted reliably.

**Why:** a review asked for "remove the breaks and escapes, then look again". The author built exactly that, and a padded wrap still kept the whole secret. The review's own request was too narrow.

## A stand-in that prints the checked line pins nothing

When a test's stand-in (a fake host, member or server) prints the very line a guard reads, the real code that prints it in production never runs under the test. Disable the real producer and every case still passes.

**How to apply:** for each line or value a guard reads, ask what produces it in production, and mutate that producer, not the guard. If a stand-in produces it in the test, add one check that runs the real producer over the smallest stub below it, with a value of the stub's own (an exit status, say), and require the line with that value.

**Why:** a run's terminal script was changed to print its own "<name> ended, status N" line, which a screen check reads. The test's stand-in members printed that same line themselves. With the real script's print turned off, every case held. One check running the real script over a stub that exits with a named status closed it.

## Read the issue's "done when", line by line

A review checks every "done when" line of the issue against the diff before the verdict, and names the change or test that meets each one. Mutants and the author's claims cover what the author thought of; they do not cover a requirement the change quietly dropped.

**How to apply:** open the issue first and list its "done when" lines. A fix that takes text out of a message (to stop a leak, say) gets a check on what the message must still say, not only on what it must no longer say.

**Why:** a fix stopped a refusal from quoting a value that could carry a secret. The review killed every leak mutant and drafted a pass. The issue also said the refusal must still tell the reader what to do, and the fix had dropped that. Nobody had aimed a check at it, so only a second reader caught it.
