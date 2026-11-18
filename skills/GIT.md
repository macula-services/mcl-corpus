---
title: Git
layer: skill
audience: [agent, human]
stage: stable
---

# GIT.md: Git

*A commit is only what you staged, and the checkout is not what shipped.*

---

## What a commit is

### A commit is only what is staged

Verify the staged set against what you meant before committing. After any multi-file `git add` that printed an error, assume nothing was staged. After a `reset --soft` or a `checkout <sha> -- <file>`, stage again before committing: the index keeps what was staged before, so a commit right after carries the old bytes for anything the reset left unstaged. Confirm what landed with `git show HEAD:<file>` or a staged stat, never from the working tree.

**Why:** passing tests prove the working tree is right, not that the commit matches it; a staging bug is never in the working tree to begin with.

### A bad pathspec stages nothing

`git add a b missing` fails the whole invocation and stages none of the valid files, not "the valid ones minus the bad one". Stage by exact path, one or a small group at a time, and verify the pushed branch itself rather than the local tree.

**Why:** the failure mode is silent, and the blast radius is the whole commit, not the bad path.

### Stage by explicit path, never everything

In a repo the owner also works in, `git add -A` or `git add .` sweeps up their untracked drafts and experiments. List the exact paths your task produced, stage them, and check the staged set before and after.

**Why:** the owner keeps work-in-progress files untracked on purpose, and "everything" from a subdirectory still acts on the whole root.

### Never squash by resetting to a moved main

Squashing with `git reset --soft origin/main` after a fetch, when main moved since the branch point, makes the squash commit silently revert every change main gained in between. Squash onto the branch's own merge-base, then rebase.

**Why:** a silent revert of someone else's commit ships under an approved range, and the gate stays green because the reverted change is not code under test.

## What the checkout is

### The shared checkout is not the shipped artifact

When several sessions work in the same checkout, `git status` is the union of everyone's edits and the tree moves under you. For a claim about what is shipped or running, read the tag, the registry or the box, and say which one you read. Never restore, reset or stash in a tree another session may be working in.

**Why:** reading a shared tree as released state draws wrong conclusions, and a broad reset discards someone else's uncommitted work.

### Fetch before a code read becomes a claim

Before a code read becomes an issue, a plan note or a claim, fetch and read the default branch (or the latest tag) and name that sha. Use `git show origin/<branch>:<path>` to describe what a branch holds, never a working-tree file.

**Why:** local checkouts drift far behind, and a finding filed from a stale view needs correction.

### A handover's commit is a claim, not a fact

A landing sha or a green gate named in a handover is often off by one. Re-derive the sha with `git merge-base --is-ancestor`, and re-run every gate it calls green, before the sha goes into a comment, a handoff line or a pull request body.

**Why:** a handover is written from scrollback, and the landing numbers are exactly what gets reconstructed wrong.

### Use git, not the wrapper, for git-able actions

Clone, fetch, ls-remote, push, branches, tags and log are git's. Use the hosting wrapper only for what exists only there: repos, issues, pull requests, secrets, environments, runs.

**Why:** the wrapper hides what actually happened in git terms and trips checks and prompts.

## Resolving a collision

### A collision on a format string is resolved by counting, field by field

When two changes touch one format line — a `printf`, a template, a `format!` — resolve it by writing the merged format and the merged argument list side by side and counting: as many specifiers as arguments, every field at the same ordinal in both, and every name assigned above the line. Keep each change's field where that change put it, and have the merge commit say which field came from where.

**Why:** a specifier and an argument that drift by one position still parse. They print one value under another value's name, which reads plausibly and passes any test that only asks whether the names are present.

### Review a conflict resolution with the remerge diff, row by row

When two changes edit neighbouring rows of one table or list, such as a component table or a diagram's boxes, the conflict hunk shows both rows twice, and the resolution has to take each row from the change that owns it, not one side whole. Review a resolution with `git show --remerge-diff <merge>`: it shows the conflict markers as git produced them and what the merge kept, so a reviewer reads only the resolved lines. For each row, name which side it came from. Then search the merged tree, not either parent, for any name one side retired.

**Why:** taking "ours" or "theirs" whole for a hunk silently reverts the other change's row. The result still compiles and still reads plausibly, so only a row-by-row read catches it.

## Where work lives

### The clone stays on the default branch; work lives in a worktree

One clone per repo, on the default branch, clean and fast-forwarded. Branch work happens in a worktree under a flat, dedicated path, and the worktree and its branch are removed when the package lands.

**Why:** a clone off the default branch misleads every sweep, and stray worktrees look like repos nobody removes.

### Trunk is the default

Commit directly to the default branch; do not propose pull requests or feature branches unless an explicit instruction asks for one.

**Why:** single-committer fast iteration; pull requests add ceremony without review value.

### On an upstream repo the maintainer's convention wins

Follow the maintainer's history and branching convention even when your tooling blocks it. When a tool blocks a required step, stop and hand the blocked step to the owner; never substitute another scheme.

**Why:** picking a different scheme to dodge a tool block goes against the maintainer's stated preference.

### Restoring an old version undoes later decisions

Restoring an older copy of a file also reverts every decision made after it. Undo only the named change with a targeted edit, or diff the current file against the restored one and re-apply every change that is not the one being undone.

**Why:** an old copy carries old state, not just the one thing being undone.

## The shared index and the sweep

### Edit a shared index by identifier, not line number

When restructuring a shared index, key every rewrite on each line's own identifier, pass unknown lines through untouched, and refuse the write if the pointer set shrank. Insert a new ordered row after the anchor it belongs to, never before it.

**Why:** line numbers go stale the instant another session writes, and dropping an entry is a permanent loss for a temporary margin.

### Drop archived repos from sweeps and clones

Before counting a local clone in a sweep, check the repo is live. Archiving a repo includes deleting its local clone and worktrees in the same step, after checking for uncommitted work.

**Why:** stale clones of archived repos look live and mislead greps, inventories and findings.
