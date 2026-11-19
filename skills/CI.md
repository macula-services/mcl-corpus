---
title: CI
layer: skill
audience: [agent, human]
stage: stable
---

# CI.md: CI

*A green conclusion proves only what that run actually ran.*

---

## Is CI actually green?

### A local green run is not a CI green run

After pushing to a repo with CI, check the actual CI status before calling the push verified. Local build, lint and test passing is not proof: CI commonly runs extra checks that a normal local workflow never triggers, such as a docs job with deny-level link lints. Read the workflow file once per repo so you know what CI actually runs, and check the run list after every push, not only when something seems off.

**Why:** the checks you skip locally are exactly the ones that catch a broken reference, so "verified, zero regressions" can be red in CI for hours while you keep reporting clean.

### A listing tool can report a false absence

A run-listing command can return a stale set and report it as if complete, with no error and no warning. Before recording "CI has not run" as fact, confirm the list against the REST endpoint, and prefer the artefact the run produces, such as the registry's own timestamps, over any listing.

**Why:** an absence reported by one tool is not an absence, and nothing looks different when you are wrong, so a stale list becomes a false "no CI for days".

## Reading a run

### Verify each run by workflow, conclusion and head sha

When a run id is cited, check its workflow name, conclusion and head sha before trusting it, and pick runs by commit and workflow, never by recency. A workflow the platform rejects appears as a push-event failure with no jobs, so "the newest run on the branch" can be a rejected workflow.

**Why:** a rejected workflow never shows in the pull request checks, only in the run list, so recency hands you the one run that proves nothing.

### Count the jobs from the run, never from memory

A green conclusion proves nothing if the run ran fewer jobs than the workflow declares, which happens during an outage. Read the job list from the run itself and compare it against the workflow's declared jobs; a subset gets re-run, never accepted.

**Why:** the declared job count drifts across releases, so no remembered number is safe, and a run missing a job still reports success.

### The run must be on the exact tip, and be the right workflow

A handoff that cites a green gate names a run on the exact tip, triggered on the branch, never a local run. A repo with several workflows can hand you a green docs run on the exact tip; confirm the run is the gate workflow, not just the right sha.

**Why:** a local run never exercises the pushed tree, and the wrong workflow on the right sha is the same as no gate at all.

### A conflicting pull request gets no runs

A pull request whose branch no longer merges with its base stops every pull-request workflow: the platform cannot build the merge ref, so no run is ever created, and a watcher waits out its whole deadline. Before treating a missing run as an outage, check whether the pull request merges cleanly.

**Why:** the gap looks like a platform outage when it is only the merge ref failing, and reopening the pull request does not help.

### A wait can answer before the run exists

A CI-wait helper called seconds after a push can answer "no run on this sha" with a clean exit, which reads like "no CI on this tip" when the run had not been created yet. Wait until the run list shows the run for the full sha, then wait; a short sha answers empty.

**Why:** the early answer is a clean exit, so "not yet" is easy to mistake for "never".

## Waiting on CI

### A re-run hides its first attempt

A run that failed and was re-run to green is stored as one run whose conclusion is success and whose attempt number is two. Its first attempt's failures appear in no list, no run view and no "failed runs" filter.

**Why:** a census of failures built from the run list therefore drops exactly the runs somebody re-ran because they were flaky, which is the evidence most worth having. A census that reads 22 failures may be missing the two that mattered.

**How to apply:** after listing runs, take every row whose attempt number is above one and read that run's first attempt's jobs and their logs. Report how many runs were re-run, and treat each re-run as a flake claim you have read rather than inferred. A job log whose text holds terminal escape sequences is refused by the CLI unless its escape allowance is passed; that refusal exits non-zero and leaves an empty file, which reads as "no log at all" if only the file size is checked.

### Do not poll in a loop

Wait with a single watch command at a slow interval, or check once at about the run's expected length; never a sub-minute loop over several run ids.

**Why:** the request limit is shared across every session, so one member's polling stalls everyone.

## Runners

### Public repos run hosted, private repos run self-hosted

A public repo uses hosted runners; a private repo uses self-hosted runners. A pull request from a fork must never run on your own box.

**Why:** hosted runners are free and safe for public repos, a fork's code is untrusted, and a runner group that refuses public repositories will queue a public job forever.

### A self-hosted runner wipes its temp directory every job

A self-hosted runner clears the contents of its temp directory when a job tears down, so anything cached there is empty at the next run. Cache in a host-owned directory chosen by an environment variable instead.

**Why:** the shape, directory tree intact with the files gone, looks like an unexplained cleanup pass, but it is the runner, and the run that filled the cache never gets it back.

### A change from a fork inherits the base repository's jobs

A change proposed from a fork runs the base repository's workflow files, so it carries jobs the fork's own settings never asked for. A job the base's runner policy cannot supply then runs no step at all, or reports that no runner was acquired: that is a property of the base repository's policy, not evidence about the change. Read the full job list before calling a run red, because a job that never started proves nothing either way.

**Why:** a change sat red on a job that had not run one step, while every job that did run was green. Re-running once is the repair when the cause is a queued runner; landing past such a job is a decision the owner makes, and the verdict then names the job and says it never started.

## Environment drift

### A native dependency can outrun the pinned runtime

A native dependency can silently require a newer runtime than CI pins: the package manager warns on the mismatch but does not fail, so every local check is green and the crash happens only when the compiled binding loads in CI. Before trusting a local green run with a new native dependency, check its declared minimum against the runtime CI actually pins, and reproduce under CI's exact pinned version when it surfaces.

**Why:** the failure is a hard crash inside a compiled binary, invisible on a machine that happens to run a newer runtime than CI, so it never reproduces locally.

### Windows CI differs in small, loud ways

A Windows CI job's bash is a different toolset: a common comparison command is missing, and a checkout rewrites line endings unless the file is marked binary. A committed file compared byte-for-byte against a release artifact then matches everywhere except Windows. Mark files compared or parsed byte-for-byte as binary in the attributes file and use a portable comparator.

**Why:** the failure message reads like a content mismatch when the real cause is a missing tool plus line endings.

## Run the gate the way CI runs it

### The gate runs in CI's image, as CI's user, on the exact sha

Run the gate inside the same container image CI uses, as the same user CI runs as, on an archive of the exact sha, not on the host. Never inject a failure with permission bits; use a shape that binds for any user, such as a regular file where a directory must go.

**Why:** CI runs as a privileged user, and a permission-bit injection the privileged user ignores passes locally and fails in CI.

## What CI cannot see

### CI cannot catch what it does not run

A change that touches paths CI skips gets a short by-eye read even on a green tip, without an extra round for the owner.

**Why:** CI is green precisely because it skipped the jobs that would have caught the defect.

### A branch with no pull request gets no runs at all

Read the workflows' triggers before promising CI on a tip. A workflow whose `on:` is `push: branches: [main]` plus `pull_request:` runs nothing for an intermediate branch that has no pull request: the run list for that sha is empty and the waiter answers "no workflow run", which is not a slow or queued run. Either wait for the pull request the landing will open, or say plainly that the tip has no CI, and never substitute runs from another sha.

**Why:** a green on a neighbouring tip says nothing about this tree, and an empty run list read as "still starting" turns a missing run into a cited one.

### A check goes in a workflow that runs for the files it guards

Before placing a new check in an existing workflow, read that workflow's path filters and its runner image. A check that guards generated files (a diagram, a lock file, a rendered page) cannot live in a workflow whose `paths-ignore` lists those files. A pull request that changes only them never starts that workflow, so the check never runs on the very change it is for. Put it in a workflow with no path filter, as its own job, on an image that has the check's interpreter. Name the mutant that changes only a guarded file, and run it.

**Why:** a drift check in the wrong workflow is green by never running. A design passed review with its drift check in a build workflow that ignored the diagram directory and whose image had no python. Only reading the filter and running the tool in the image showed it.
