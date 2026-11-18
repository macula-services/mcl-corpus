---
title: GitHub
layer: skill
audience: [agent, human]
stage: stable
---

# GITHUB.md: GitHub

*A tool aims where you point it, and a token does what its scopes say.*

---

## Aiming the tool

### A bare command can aim at the wrong repo

In a clone that keeps more than one remote, a bare command such as a run or pull-request listing can resolve to the wrong remote and print a plausible result for the wrong repo, saying nothing about which it chose. Pass the owner and repo explicitly on every call. If a history looks implausibly stale, check the remotes before believing it.

**Why:** a fork that shares history makes the wrong repo's list look like yours, just older, and a real current head reads as "nothing has run here in days".

### Two API paths rate-limit independently

The REST endpoints and the GraphQL path can rate-limit or refuse at different times, and the reverse also happens. When one path answers with a refusal, try the other before reporting a blocker.

**Why:** a shared token can be refused on one path while the other still answers, so a blocker report is premature until both have been tried.

## Credentials

### The CLI reads a token from the environment before any stored login

A command-line client takes a token from the environment ahead of any login stored in a config directory. A private config with a narrow token does not keep a script off the ambient credentials unless the script also runs under a clean environment.

**Why:** the narrow token you meant to use is silently bypassed by the broader one in the environment, and the script acts with more power than intended.

### A token does what its scopes say, and a push should use SSH

A token missing a scope is refused on that action, and the error often names the object, not the missing scope, so it reads like a permissions problem. A token without the workflow scope cannot create or update workflow files. Use SSH remotes for pushing; key auth is not subject to that restriction.

**Why:** the refusal names the file, so the real cause, a scope the token lacks, is invisible, and reaching for a broader token is the wrong fix.

## Pull requests and settings

### A fast-forwarded pull request leaves no merge commit

A pull request whose head is pushed straight onto the base leaves no merge commit, so a first-parent log shows its commits as if pushed directly. Before calling a commit unreviewed, ask the platform's API whether a pull request covers it.

**Why:** an approved, reviewed change looks like a direct push in the log, and a release note then mislabels reviewed work as unreviewed.

### Enabling workflows is a repo-settings change that arms the publishers

Turning on a repo's workflows, or its actions permissions, is a settings change, and it does not only enable your own job: it also registers the publishing workflows, so a later push can publish things nobody meant to. Ask before making it, even on a fork, and name exactly which workflows become live.

**Why:** a fork whose actions had never run, once enabled, quietly armed every upstream publisher in the same name.

## Features and visibility

### A config file is not the whole feature

A feature driven by a config file may also need a per-repo switch that defaults to off, and the listing command does not expose it. Turn the switch on after creating the file, and treat the mutation as idempotent rather than trying to pre-filter.

**Why:** the file resolves for every repo while the button still does not render, and the listing gives no way to see the switch.

### Package visibility inherits from the org, not the repo

On a forge, container packages inherit visibility from the owning org, not from the repo, and a per-repo visibility flip does not propagate to them. If a package must be publicly pullable, the org must be public, and an API call that changes the org flag may be silently ignored, so do it through the platform's own settings.

**Why:** the repo flag flips and nothing changes for the package, because the package has no access list of its own.

### A stored mirror credential goes stale with no update endpoint

A push mirror stores a credential at creation time, exposes no update endpoint, and goes stale when that credential loses access. The fix is delete and recreate, and a sync call that returns success is not proof: read the mirror's recorded state or compare heads.

**Why:** the sync returns success even when there is nothing to sync, so a green answer hides a dead mirror.
