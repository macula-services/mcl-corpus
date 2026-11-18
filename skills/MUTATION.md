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

## Run it cleanly

### A runner restores what it mutated

A mutation run must hold the original bytes and write them back in a finally. A shell restore with flattened paths leaves source files mutated, and every later run fails for that reason alone.

**Why:** the runner's own artifact is the thing being tested; a runner that does not restore pollutes every run after it.

### Read the exit code, not the markers

A test runner that greps failure markers from its output gives random survivors. Select the one test and read the runner's own exit code.

**Why:** markers repeat and include noise; the exit code is the runner's own verdict on that one test.

### A write-through mutant corrupts the fixture

A harness case that links a test path to a committed fixture lets a write-through mutant overwrite that fixture; every later run, green or mutant, then fails for that reason alone. Link to case-local copies and hash-check fixtures after each mutant run.

**Why:** the fixture becomes the mutation, and no later run is trustworthy.

### Count a kill only on the runner's own failure count

A mutation log that carries colour codes inside its "compiling ... failed" line scores a mutant that fails to compile as killed. Strip the codes, and count a kill only when the runner's failure count is above zero.

**Why:** a mutant that does not compile is not a mutant the test killed.

### Restore compares the artifact to the source

A mutation-check restore can leave the mutant's compiled artifact in the build directory when the timestamp is not strictly newer. Delete the artifact and compare it to the source before an evidence run.

**Why:** a stale mutant artifact answers every later question wrongly.
