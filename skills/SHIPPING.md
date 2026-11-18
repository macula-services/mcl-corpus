---
title: Shipping
layer: skill
audience: [agent, human]
stage: stable
---

# SHIPPING.md: Shipping

*A push, a tag and a release are three different acts; each has a silent way to look done while nothing moved.*

---

## What "done" means

### A push is not a deploy

On a repo whose CI builds and ships the deploy image only after its tests pass, a successful push is not evidence that the running system got the new code. The push can land while the test job fails and the image is never built, and the system keeps running the old image with no visible error on the pushing side. After a push, read the run's conclusion and wait for success before treating a fix as live.

**Why:** the leg from the registry to the running system is automatic, but the leg from the push to the registry goes through the whole test gate, and an unrelated flaky test can stop it every time.

### Run the product live from the first days, and again every night

Schedule a live end-to-end run of the finished install in the first days of a product, and repeat it every night. A suite that runs over a recording sees only what the recording holds: the first-run screens, the host's own update and its trust prompts appear in a live run and nowhere else. Pick the one milestone path before opening parallel fronts, and keep generated artifacts out of the changes when many changes touch them.

**Why:** a product that took weeks where a plugin of the same size took days had no live run for its first two weeks, ran several fronts against no milestone, and rebuilt one generated file in every change until landings serialized. Each of those is a cost that the first live run, or one ordered path, would have surfaced in the first days.

### A tag never lands ahead of its main

Push the commit, re-fetch and confirm the remote default branch equals the tip, and only then create and push the tag. Never pipe a push, or any step whose exit code decides the next step, through a filter, which eats the exit code. Refuse to tag unless the remote branch already equals the approved base.

**Why:** a refused push masked by a pipe lets the loop continue and push the tag ahead of the branch it names, so the tag points at a commit the branch never carried.

### Verify the publish on the exact sha that will be tagged

Run the release workflow's own verify steps, in its own order, on the exact commit that will be tagged, after the last review-driven edit. A lint-and-test gate is not a substitute: it does not run the docs build or the format check, and a deletion or an insertion can break one of those on a commit the tests still pass. A list of checks you assembled yourself is not the gate.

**Why:** verifying an earlier commit and then moving the tag to a later one ships, or fails to ship, on a commit nobody verified, and the version number or the tag is the thing that cannot be taken back.

## The ref that goes out

### Push the ref the approval names, not the stale default branch

In a worktree on a feature branch, `git push origin main` pushes the repository's own, stale main ref, not the branch you are on, and answers "everything up-to-date" while nothing has moved. Read both refs first, then push the branch to the ref the approval named, and confirm the remote moved afterwards.

**Why:** the push looks successful and the failure is silent, and the shape is exactly the one this way of working produces: the checkout sits on the default branch while the work sits in a worktree.

### Commit on a fresh origin, not the stale local default

Make every change on a branch cut from the remote default right after a fetch, never on a shared checkout's local default branch. A commit made on a local default that has drifted behind origin makes the range's tip not descend from its base, so the range silently reverts the newer work, or is refused as non-fast-forward.

**Why:** an approval is given on a base and a tip; if the tip does not descend from the base, pushing it undoes someone else's landing.

### Rebase after the approval only when the paths do not touch

When the remote default moves between the approval and the push, the rebased commit may go out without a new approval only if both hold: every new commit touches none of the change's paths, and the rebased files are byte-identical to the approved ones. Anything else goes back for a fresh approval.

**Why:** a pure rebase over unrelated commits is the same change; a rebase over a commit that edits the same files is not, and the byte check is what tells the two apart.

## Landing a batch

### The lander merges the default branch into passed heads

When several passed changes land together, whoever lands the batch merges the moved default branch into each passed head. The authors are not called back for it. A merge that only takes the default branch's side, or regenerates a generated file, is the lander's to make and the lander's to check.

**Why:** calling each author back to merge in turn makes a batch wait on the slowest session, and the author holds no knowledge the merge needs.

### A reviewed, green batch lands without a per-batch question

When every change in a batch has passed review, the combined tip is green in the project's own checks, and the landing base is the current default tip, the batch lands on the coordinator's go and is reported afterwards with the range that would revert it. Do not open a landing question per batch: review plus a green tip is the safety, and a question per batch makes the owner the bottleneck of every shipment.

**Why:** a team that had already settled this drifted back to one landing question per batch within days, and the owner's answer was that the team should be able to do far more without the owner's continuous intervention. Still asked, and batched into one question: version and release tags, changes to repository settings or secrets, infrastructure rolls, realm and credential changes, deletions, and spending. A landing is an infrastructure roll when the default branch publishes an image that a running machine follows: check for that before treating a batch as one that needs no question.

### A freed member takes its next work from an ordered queue

When a member's change passes or lands, its next package is already waiting in one ordered queue, and it takes the top one in the same step. It does not ask what to do next, and the coordinator does not pick on the spot.

**Why:** a coordinator who chooses the next package only when asked leaves members idle, and the choice made under pressure skips the order that was agreed.

### A change lands alone only when it changes the landing path

Land a passed change on its own only when it changes how changes land: the merge, the batch, the checks before a push. Everything else waits for the next batch.

**Why:** a change to the landing path must be on the default branch before it lands anything else, so that what it fixes applies to the very next batch. Any other change gains nothing from landing alone and costs the owner one more act.

## Where the work lives

### Approved-but-unpushed commits do not sit on a shared default branch

Commits that are approved but not yet pushed must not sit on the default branch of a checkout other sessions also commit in. The next session to commit there builds on top of them, and its push ships them unverified and out of order. Park multi-step work on a branch or in a worktree, and push each approved commit from there.

**Why:** where several sessions commit as one author, the history does not reveal whose unpushed work got swept into someone else's push.

### Untracked is the only truly unrecoverable state

Before calling work single-copy, check both directions. A branch with no upstream configured still reads as "never pushed" and may be on the remote at the identical sha, and a diff that says two trees are identical cannot see an untracked file that exists in no object anywhere. Only a file present in no local or remote ref is genuinely unrecoverable.

**Why:** a diff proves nothing about untracked files, and the one item that is really lost is exactly the one a backup-by-copy misses.

## Who fires the release

### A tag push is the release gate

Where a pushed version tag triggers the publish, the approval point is the push of the tag, not a human reviewer after it. Do not propose adding a required reviewer to a release environment: a tag push that already goes through the approval gate is the whole gate, and a second one duplicates it. And a workflow comment that claims a reviewer gate exists when nothing enforces it is false and gets corrected: fix the comment, not the environment.

**Why:** the missing reviewer is the design; the tag push is where the human already says yes, so the safety is not a gap but a duplicate.

### Never fire the publish yourself

Never run a publish command by hand, for a package, the docs, or anything else, no exceptions, and never offer "I'll publish it" as an option. Prepare the release (bump the version, changelog, tag, and confirm the docs build clean) and push the tag, approved like any push: the tag push fires the publish, and there is no manual publish step after it.

**Why:** a publish is one-way and externally visible, and the person who owns the package fires it; an offered option treats a forbidden act as available, and two publish paths for one version is how a version gets burned twice.
