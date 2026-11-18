---
title: Verifying
layer: skill
audience: [agent, human]
stage: stable
---

# VERIFYING.md — Verifying

*Verify the thing claimed, not the nearest thing that is easy to measure.*

---

## The whole gate, not a part of it

### A green suite is not a green gate

A repository's gate is wider than its tests: it may also compile with warnings as errors, lint, type-check and run static analysis. "The tests pass" is a true statement that does not support "this will pass the gate." Run the whole gate before claiming it passes — from a script that reads the workflow, not from memory of what it contains — and say which steps ran.

**Why:** a true statement about the suite is read as a statement about the gate, and no one catches the substitution by reading it, because every word is accurate.

### A run is proof only if the guard under test was live

A run that succeeded is evidence only if the guard it was testing actually ran. A guard that silently failed to load and a guard that passed are indistinguishable in a log that only shows the run succeeding — the absence of a refusal reads as approval. Before quoting a live run as proof, name the evidence that the guard executed: a refusal you also provoked, a line the guard prints, or the loader's own validation. Ask what would have differed had the guard been off.

**Why:** a check that fails to load passes everything, and the green log carries no mark of it.

### A range check misses drift in a generated file's generator

A check that judges only the ranges touching a generated file (a drawn diagram, a lockfile, a rendered doc) cannot see its generator move. When a change edits the generator, or the sources it reads, and touches nothing it outputs, every range check stays green while the tree no longer matches what the generator would produce. So check the whole tree as well: regenerate and compare at release preflight, before the first outward act of the release, not only per range.

**Why:** in one case the drift was caught before a release, but the release's own check would have refused only after one package was already published, and a published package cannot be taken back. Every range check had passed, because no range had touched the generated file.

### A conflicting pull request gets no runs

A pull request that no longer merges cleanly into its base gets no runs — the test merge cannot be built, so no run is created for it, and a watcher waits out its whole deadline for runs that will never come. Before treating a missing run as an outage or a queue delay, check whether the pull request still merges; a conflict explains it on the spot, and merging the base back in brings the runs.

**Why:** a conflict reads as a stalled pipeline when it is really the test merge failing to build.

## The mechanism, not the label

### Name the mechanism, then check it could produce the result

Name the mechanism, then check it could produce what you are looking at — arithmetic first, investigation second. A cause and an effect that sit close in time are not thereby linked: check the cause's duration before believing the link; when crediting a commit with a fix, read what it actually touched; when reasoning from a periodic event, read what re-arms it.

**Why:** an attribution that matches on a label or a timestamp rather than on a mechanism is locally reasonable and still wrong.

### A secondhand summary drops the scope

A secondhand summary systematically drops the scope qualifiers that decide whether a claim is true as stated. When a relay characterizes a prior finding, treat "X was found to Y" as a hypothesis about what the primary source says, and read that source before accepting or repeating the framing — especially when asked to evaluate the claim independently.

**Why:** a compressed summary propagates an over-generalization, and every relay that does not go back to the source repeats it.

### A definition is not behaviour

Never conclude a system does something from a definition — find the consumer. Search for the name across the tree; if the only hits are the definition, the type and the doc, the field is decorative and the system does not do the thing. Report the definition and the consumer separately.

**Why:** a declared or documented behaviour with no consumer is inert, and two readers of the same definitions reach opposite conclusions until one checks the consumers.

## The control, not the coincidence

### Revert the change before blaming it

When a test starts failing right after a dependency change, the instinct is to blame the change. Before reporting a regression — or shipping around it — revert just that change, rebuild, and rerun the same test enough times for a real failure-rate comparison. Only then decide whether the change is implicated.

**Why:** a failure that coincides with a change is often already present at baseline, and a single run in either direction proves nothing for anything timing- or network-dependent.

### A release passes only when its version is unused

Before passing a release, check that the proposed version is still unused: the tag is absent and the registry does not serve it, with the previous version as the positive control. A version that is already live means the release renumbers a section that already shipped.

**Why:** a "skip duplicates" default or a stale section hides the fact that the version is live, and the pass then ships a version that is not the one the review read.

### A scheduled job is unproven until its first run is observed

A scheduled job that is merged is a definition, not a running job. Count it as working only after its first scheduled run has been seen: the run exists, it ran on the schedule, and it did what it is for. Until then, say "scheduled, not yet run", and put a check on the date the first run is due.

**Why:** a daily sync had been on the default branch for 16 hours without ever running, while everyone counted it as live. Nothing fails when a scheduled job never fires, so only looking for the run shows it.

## The assertion where the behaviour lives

A test of a behaviour owned elsewhere belongs where the behaviour lives. An integration check that goes green about someone else's invariant passes because the call succeeded, while nothing stops the owner from removing the behaviour — both suites stay green and the feature breaks. Assert the invariant in the repository that implements it, and verify the location yourself rather than trusting a relayed claim about where a seam lives.

**Why:** a green test about the adjacent object is a signal from next to the thing that matters, not from the thing.
