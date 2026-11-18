---
title: Build
layer: skill
audience: [agent, human]
stage: stable
---

# BUILD.md: Build

*A green build proves only what the runner actually ran, on the version it actually resolved.*

---

## The stale beam

### A deleted test module still runs from the build directory

The test runner executes the test build directory, not the repository. A test module deleted from source keeps running from its stale compiled artifact: it fails if its subject is gone, and passes silently, inflating the count, if the subject is also a stale artifact.

**Why:** the runner never looks at the source tree, so deletion in source changes nothing until the artifact is rebuilt.

### A restored source still runs the old beam

The runner reuses a compiled artifact when the restored source is not strictly newer, and its timestamp granularity is one second, so a touch is not enough. Delete the artifact and compare the artifact to the source before trusting a red or green flip.

**Why:** an mtime that is not strictly newer skips the recompile, and the runner then reports on the old code.

### A passing suite can be green on the wrong dependency

A local, ignored lock file keeps resolving the old dependency version after a constraint bump, and the suite goes green on the version you did not mean to test. The manifest is the source of truth; never reason from, or hand-edit, a lock file.

**Why:** the resolved version silently differs from the declared one, and the green proves nothing about the new version.

## What the runner counts

### eunit hides cancelled tests

"Failed: 0. Passed: N." hides cancelled tests, such as a failed fixture setup or a timeout. Report passed, failed and cancelled separately, and look for the fixture-setup failure line.

**Why:** a cancelled test is not a passed test, and the summary does not say so.

### eunit setup runs in a different process

A fixture's setup runs in a different process from the test body, so a logger handler, a network listener or a trap made in setup never reaches the test.

**Why:** process-local state made in one process is invisible in another, and the test then fails for a reason unrelated to its subject.

### eunit runs a module's tests in one long-lived process

A module's tests share one process, so a process a test starts and streams it owns outlives the test and shows up in later modules.

**Why:** leaked processes make later tests fail for reasons the later tests did not cause.

### The app-scoped runner skips standalone tests

Running the suite scoped to an application skips standalone test modules that live outside that application. Use the directory scope or the full gate.

**Why:** a scoped run passes by not running the tests you needed it to run.

### A cancelled test exits one, a skipped test exits zero

The runner exits nonzero on a cancelled test, but a user skip can exit zero. Read the exit code against the right kind of skip.

**Why:** treating every zero exit as "all passed" turns a skipped test into a green one.

## Dependencies

### A two-part tilde floats to the next major

A `~> 0.34` constraint means at least 0.34.0 and below 1.0.0, so it floats onto 0.35. Only a three-part `~> 0.34.0` stops at 0.35.0. With no committed lock, every build takes the newest inside the constraint.

**Why:** the two-part form is wider than it looks, and "newest" silently drifts every build.

### An umbrella override wins silently

When a dependency is declared at the umbrella root with an override flag, a child's own bump is silently ignored; the override wins at resolve time.

**Why:** the child's change looks applied and is not.

### Exact pins break diamond coordination

Do not pin dependencies to exact versions; use a two-part or three-part tilde. Exact pins break diamond-dependency coordination across the tree.

**Why:** two consumers pinning different exact versions of one library cannot both resolve.

### Lock files follow the ecosystem's convention

Whether a lock file is committed follows the ecosystem convention, never a guess: some stacks commit the lock, others never do. Do not hand-edit a lock; change the constraint and let the resolver write it.

**Why:** a lock committed where it should not be, or missing where it should be, both drift silently.
