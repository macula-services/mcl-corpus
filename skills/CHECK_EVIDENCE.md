---
title: Check Evidence
layer: skill
audience: [agent, human]
stage: stable
---

# CHECK_EVIDENCE.md — Check Evidence

*A green check is evidence only for what it actually ran, and only for what was actually read back.*

---

## A test proves what it pins, not what it restates

### A test that reads the default back to itself proves nothing

A test that compares a value against the very constant the value is defined from passes whatever that constant is set to, so a change to the definition never fails it. Pin the value against a *different* source — a second constant, or the literal — so the test fails the day the definition moves. When a value has both an "off" meaning and a "default" meaning, keep them as two constants and have comparisons read the off one.

**Why:** the test's job is to pin the decision, not to restate the implementation.

### A claim test compares exactly, in both directions, and reads the page

When a page or a diagram makes a factual claim about the code, the test that pins it must compare the sets exactly — not only "everything declared appears" — and must read the page's words, not only the code. Before offering the test as proof, plant the changes a reviewer will try (drop an entry, restore the old sentence) and run each; if any stays green, the test is not exact.

**Why:** a one-way check passes the change that drops an entry, and a test that never reads the page passes the change that puts the false sentence back.

### A search is not proof; plant the failure first

A search proves only that the strings you thought of are absent, and a presence check proves only that a token exists somewhere. Neither proves anything about the class of claim. Before offering a check as proof, plant a known violation in a copy and confirm the check fails on it — a zero-hit result from a check that cannot hit is meaningless. Say which places were scanned and which were excluded, and why.

**Why:** a reader cannot tell a real check from a grep unless the check is handed over with its blind spots named.

## A green exit is not a green result

### Count from the run's summary, not the failure markers

The number of failing cases is the runner's own summary line, never a count of the failure markers in the output — a runner prints each failure once as it happens and again in its summary, so counting markers over-counts. For any "N cases failed" claim, quote the summary's totals; call a per-marker count "failure lines", never "tests". Every runner has one summary line that is the count.

**Why:** an inflated count reads as carelessness about every other number beside it.

### A run is green only when its summary is present

A suite run is evidence only when its output ends with the runner's own summary block, and the exit code and the commit it ran. A run cut off early can exit 0 with a partial list and no summary, which reads exactly like green. Run a long suite to completion; if the summary is missing, the run is evidence for nothing — rerun it.

**Why:** a truncated count backs a claim that is false.

### A proof harness proves its own matcher first

When a proof asserts by pattern, run one case whose pattern is known not to match and require it to be reported red before any real case runs. Read a pattern list with a trailing newline, or its last entry is dropped unread; never let a loop that iterated zero times read as a pass. The harness's own landed-mutation check belongs with it: compare the mutated bytes against the held ones, or a mutation that never applied looks like a surviving mutant.

**Why:** a harness fails by silence, and silence looks exactly like every case holding.

### A check that exits 0 with hits is red

A check that prints hits and still exits 0 is text to read, never a gate the shell enforces. Run it on its own, read the hit count, and only then act — or make the next step depend on a zero-hit reading, so a hit stops the chain.

**Why:** an exit status of 0 makes a guard that did not guard look like it did its job.

### Measure the exit code unpiped

A pipeline reports the last command's exit status, never the first's. When an exit code decides something — a gate, a pass/fail claim — collect it unpiped first: redirect to a file, then read the code. The same trap hides behind `tee`, `grep -q` and `head`.

**Why:** a measurement that cannot show the opposite is not evidence.

## CI evidence

### A subset of jobs still reads success

A run that carries only some of the workflow's jobs, each reporting success, proves nothing — a green conclusion on a partial run is not a green run. Read the job tally from the run itself, grouped by outcome, never from a number in front of you or from memory; the declared count drifts across releases.

**Why:** the workflow and the commit can both be right while half the jobs never ran.

### A run is cited only after its workflow, conclusion and head sha are checked

Cite a run as evidence only after reading its workflow name, its conclusion and the commit it ran, and list every run on that commit to see none failed. Pick runs by commit and workflow name, never by recency. After a landing, the push runs on the landed commit are the evidence, not the pull-request runs that carried the review.

**Why:** a rejected or unrelated run can be the newest run on the branch while proving nothing, and a landing fires a fresh set of runs.

## A test leaves nothing behind

Every test removes what it creates — temp directories, files, processes. A test that leaks scratch fills the machine's scratch space and fails every other test that runs after it, and a review flags the leak as a required change. Back the rule with a check that fails such a test by name.

**Why:** what one test leaves behind is paid for by every other test that runs after it.
