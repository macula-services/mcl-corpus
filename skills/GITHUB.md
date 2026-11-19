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

## Text that is stored

### A posted body is read back, and corrected where it stands

A comment, an issue or a pull-request body is stored text on someone else's server: what you sent is a request, and the stored body is what every reader sees. Fetch it back and compare it with your source before you believe it landed as written. A control character written as an escape sequence can be transformed on the way and arrive as something else, so name characters in words instead of escaping them. A small error is corrected by updating that same comment — the update keeps its id and its link — not by posting a second comment below it.

**Why:** the stored body is the artefact the work is held to, so a mangled citation is simply a wrong citation to everyone downstream, and nobody reports it. A correction posted underneath leaves two versions of one text, and the older one is the one an existing link opens.

**How to apply:** after posting, fetch the body through the API, compare it trimmed against the file you sent — a trailing newline is not a difference, and a difference anywhere else is — and report that comparison rather than that the post succeeded. Correct with the comment's update call; post a fresh comment only for a fresh take, such as a verdict or an amendment.

## Credentials

### The CLI reads a token from the environment before any stored login

A command-line client takes a token from the environment ahead of any login stored in a config directory. A private config with a narrow token does not keep a script off the ambient credentials unless the script also runs under a clean environment.

**Why:** the narrow token you meant to use is silently bypassed by the broader one in the environment, and the script acts with more power than intended.

### A token does what its scopes say, and a push should use SSH

A token missing a scope is refused on that action, and the error often names the object, not the missing scope, so it reads like a permissions problem. A token without the workflow scope cannot create or update workflow files. Use SSH remotes for pushing; key auth is not subject to that restriction.

**Why:** the refusal names the file, so the real cause, a scope the token lacks, is invisible, and reaching for a broader token is the wrong fix.

### A value piped from the API is checked for its shape, never its length

When a token or an identifier is piped from the API into a script, check the shape of what arrives, not how long it is. A call that fails for a missing scope answers with an error body, and that body travels down the same pipe: a "longer than N characters" test accepts it and hands it to the next step. A registration token, for one, is a single word of uppercase letters and digits; braces, quotes, spaces or lowercase letters mean an error body, and the script refuses it by name before it touches anything. Where the value has to come down a pipe, its shape is the only evidence there is.

**Why:** the wrong input is accepted silently, and it surfaces three steps later as a credential rejection far from the line that let it in.

## Pull requests and settings

### A fast-forwarded pull request leaves no merge commit

A pull request whose head is pushed straight onto the base leaves no merge commit, so a first-parent log shows its commits as if pushed directly. Before calling a commit unreviewed, ask the platform's API whether a pull request covers it.

**Why:** an approved, reviewed change looks like a direct push in the log, and a release note then mislabels reviewed work as unreviewed.

### Enabling workflows is a repo-settings change that arms the publishers

Turning on a repo's workflows, or its actions permissions, is a settings change, and it does not only enable your own job: it also registers the publishing workflows, so a later push can publish things nobody meant to. Ask before making it, even on a fork, and name exactly which workflows become live.

**Why:** a fork whose actions had never run, once enabled, quietly armed every upstream publisher in the same name.

### A pull request opened by the workflow's own token starts no CI

A workflow that opens or pushes to a pull request with the token the platform hands each run does not trigger any workflow on it, so the pull request sits with no CI. Letting a bot open the pull request therefore does not remove the human step: a person still has to push, close and reopen it, or start the runs by hand. To make it hands-off, the workflow needs a separate credential, an app or a scoped token, which is then a credential to guard.

**Why:** the platform does this on purpose, so that a workflow cannot start itself in a loop. A plan of "the bot opens the pull request and CI checks it" breaks on the first run, and the fix is a new secret, which needs its own decision.

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
