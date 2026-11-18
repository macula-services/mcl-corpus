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

## A claim about the tree is settled by the tree

A plan's "waits on" column, a row's "read from" source, and a review's list of what catches a missed row are all claims about the repository at that moment. Each is settled by the repository, not by memory, by a title, or by a name that sounds right. Three ways it goes wrong: a wait named on work that already landed, a control credited with more than it does, and a source that names a file without the field.

**How to apply:** before posting a plan, prove each wait is still pending — the merge commit is not on the default branch, or the file it was to produce does not exist. For each source, name the field as well as the file, because two records of one concept may name their fields differently, and a row that reads "the recorded file" without its field cannot be built. For each control, plant in a copy of the tree the thing it is supposed to catch, and run the check: reading the check's judgment function gives you the words it prints, and a grep gives you less, but only a plant tells you your case reaches them. When reviewing someone's fix of a failure you raised, compare their before blocks against the original and check that nothing the original had right was dropped in the rewrite.

**Why:** a plan waited on a package that had landed two batches earlier and credited an exact-count check with covering every directory in the source tree, when the rest fell to a looser cap — both settled in one turn by the landing commit, the recorded file and the check's tests. Later, a claim that a new directory could enter the source tree unreported was disproved by planting one: the architecture test failed by name, and the file had only to be called out on the page with a reason. That claim would have become a false issue. The first two cost a review round; all three came from writing down what the tree was remembered to be.

### A design that compares a declared name with a reported one says how the names map

When a design checks the name a host reports (a model, a version, a runtime) against the name a declaration holds, it must say how the two are matched. They are often not the same vocabulary. A declaration names an alias, and the host reports the full id that the alias resolved to. A plain string compare then stops exactly the members the rule exists to let through. Match through a mapping recorded from the host itself, kept beside the recorded host version. Stop by name, with "re-take the recording", on an id the recording does not hold. Never match by guessing a pattern.

**How to apply:** for every equality check across a boundary, ask the author for the spelling on each side, with a real example of each. Ask too where an open vocabulary (one that accepts any name) gets its only real check.

**Why:** a review rule for a mixed crew compared the declared reviewer model with the one the session reported. On one host the declaration held an alias and the session reported a full id, so the rule would have refused every correct reviewer. On the other host any name passed declaration, so a misspelled model was caught nowhere but the launch read-back, and the design had not said so.

## A plan gives every line of its issue a home

A plan that orders an issue's work into packages places every line of that issue. Each "done when" line, each "not measured yet" item, and each output the issue says must leave the work belongs to one package by name, or the plan says plainly that it is open. A decision with a prerequisite goes to the package where the prerequisite first exists, not to the package where it reads well.

**How to apply:** before posting the plan, walk the issue from top to bottom and write each line's package beside it. A line with no package is a gap in the plan, never a detail for later. A line whose package lacks the thing it depends on (a link to a card before the cards exist) moves to the package that builds that thing.

**Why:** a plan for a storming board ordered six packages and a model step, and its gap table was right. But the issue's own "done when" belonged to no package, the three "not measured yet" items had no home, and the big picture's outputs had no package. A link to an issue card was placed two packages before the cards existed. The review found five small items, all of the same kind: lines the plan had read but not placed.
