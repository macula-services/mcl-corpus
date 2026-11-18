---
title: Mutation
layer: skill
audience: [agent, human]
stage: stable
---

# MUTATION.md: Mutation

*A test proves a guard only when the guard actually runs and the mutant actually hits it.*

---

## Aim the mutant

### A survivor means re-aim at the pinned check, not a missing test

A mutant that survives means the mutation did not hit the check the test pins; re-aim it at that check. It does not mean the test has a gap.

**Why:** the mutant missed the seam, and the fix is aim, not a new test.

### The seam must sit below the mutant

A test-supplied step that sits above the mutant's anchor lets the mutant survive, because the test fakes the very code it claims to cover. Put the seam below the mutation point.

**Why:** a fake above the anchor replaces the code the mutant would break, so the mutant never fires.

### A probe proves the gate ran, not just that it passed

A live probe proves nothing unless it proves the gate under test actually ran. A guard that failed to load and a guard that passed are indistinguishable in a log that only shows success.

**Why:** the absence of a refusal reads as approval, and a green log carries no mark of a guard that never loaded.

### Two independent guards hide each other

Two independent guards each make a failure unreachable, so each survives its own mutation and looks unnecessary; only removing both shows the damage.

**Why:** mutation testing cannot see redundancy, and a comment crediting the wrong guard is then unfalsifiable.

### A pin with a margin wider than the difference pins nothing

A check written to allow a margin can pass the very behaviour it exists to forbid, when the cases it runs are closer together than the margin. A clock pinned as "somewhere near now" passes a clock that prints now, because the run's real wait is seconds. Widen the difference in the case — run it with a long window — rather than the assertion, and say why the margin is there.

**Why:** a band is a statement about what is allowed, and one wide enough for the bug states nothing.

### A behaviour promised on several paths is pinned on each

A line promised "whenever X happens" is unpinned if only one of X's paths is asserted. A mutant that prints it on the success path alone then survives: the test only ever reached that path.

**Why:** the promise is about every path it names, so the test has to reach every one of them.

## Run it cleanly

### A runner restores what it mutated

A mutation run must hold the original bytes and write them back in a finally. A shell restore with flattened paths leaves source files mutated, and every later run fails for that reason alone.

**Why:** the runner's own artifact is the thing being tested; a runner that does not restore pollutes every run after it.

### Read the exit code, not the markers

A test runner that greps failure markers from its output gives random survivors. Select the one test and read the runner's own exit code.

**Why:** markers repeat and include noise; the exit code is the runner's own verdict on that one test.

### An exit code is a kill only when the test spoke

The exit code alone is not enough either: a run that never happened also fails. A runner that rewrites the source through a new file drops its execute bit, so every case dies at "cannot execute" (126); a syntax error (2) or a missing command (127) reads the same way, and a set of apparent kills is a set of runs that never reached the test. Require the test's own voice in the log — a line only it writes once it is running its cases — before counting a failure as a kill, and refuse the rest by name. Never grep for the one error string that happened last time.

**Why:** the exit code says the process failed, not that the test failed, and every mutant looking immortal costs a round.

### A write-through mutant corrupts the fixture

A harness case that links a test path to a committed fixture lets a write-through mutant overwrite that fixture; every later run, green or mutant, then fails for that reason alone. Link to case-local copies and hash-check fixtures after each mutant run.

**Why:** the fixture becomes the mutation, and no later run is trustworthy.

### Count a kill only on the runner's own failure count

A mutation log that carries colour codes inside its "compiling ... failed" line scores a mutant that fails to compile as killed. Strip the codes, and count a kill only when the runner's failure count is above zero.

**Why:** a mutant that does not compile is not a mutant the test killed.

### Restore compares the artifact to the source

A mutation-check restore can leave the mutant's compiled artifact in the build directory when the timestamp is not strictly newer. Delete the artifact and compare it to the source before an evidence run.

**Why:** a stale mutant artifact answers every later question wrongly.
