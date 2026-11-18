---
title: BEAM
layer: skill
audience: [agent, human]
stage: stable
---

# BEAM.md: BEAM

*Let it crash, keep it flat, and name one process per role.*

---

## Write it flat

### Never nest one case inside another

Flatten control flow in every language. Decompose a nested `case` into pattern-matched helper function clauses instead. Closures count as a nesting level too.

**Why:** deep nesting hides the intent and reads as garbage; the flat form names each branch.

### No anonymous spawn

Before writing a `spawn` or `spawn_link` with an anonymous fun, ask whether a supervised `gen_server` or `gen_statem` should hold that work instead.

**Why:** anonymous processes are invisible to OTP, not restartable, and leak on crash.

## The OTP way

### A synchronous call in a connect handler blocks the whole server

A synchronous `gen_statem:call` from a `gen_server`'s connect handler blocks the entire server for the call timeout, per connection. Spawn an async resolver that casts the answer back, and snapshot the target state first.

**Why:** one slow caller serializes every other caller behind it.

### A call across apps can race boot

When a `gen_server` in one application calls a `gen_server` in another at startup, their boot order is not guaranteed; a `:noproc` crash on a tight restart loop can take down the whole release. Do not assume another application is up just because yours is.

**Why:** startup order is an ordering fact, not an invariant the runtime promises.

### A process manager is how policy is expressed

A process manager (an `on_<event>_maybe_<action>` slice) is the place a policy lives, inside one domain too. Never fold one into a command handler to make it atomic.

**Why:** the policy is a sibling concern, not a step of the command.

### A process manager is a sibling slice, not a nested desk

Cross-domain listeners and process managers live as sibling slices in the target application (own directory, own supervisor, own server), never nested inside the desk they trigger.

**Why:** nesting the policy inside the desk it watches couples the two and hides the relationship.

### try/catch has one valid use

try/catch is generally anti-BEAM (prefer let-it-crash and pattern matching), but it has one legitimate use: preserving a distinct failure-mode signal that would otherwise collapse into an opaque supervisor exit. Document it at the call site.

**Why:** the exception is not an escape hatch; it is a named signal that must stay distinct.

### No generic agent modules

Never share a generic agent module. Each agent role gets its own desks, events, commands, handlers and process managers.

**Why:** a generic module becomes a god module and violates screaming architecture; clarity beats DRY.

### Two formats for one concept means unify, not parallel

When two existing formats, types or modules represent the same domain concept, unify them. Do not maintain a parallel implementation labelled "for now".

**Why:** a second copy is technical debt that only grows, and the label hides it.

## The runtime

### Build, test and document against the declared runtime version

Target the team's declared runtime version, and treat a repo on another major as drift to fix, never a constraint to keep. A version that silently differs is the worst kind.

**Why:** a passing suite on the wrong runtime proves nothing about the one that ships.

### Status is bit-flag integers, not strings

Aggregate status fields are bit-flag integers, not string labels. A string that reads "uploaded" or "published" violates the convention and is the tell of a status field that should be flags.

**Why:** bit flags compose, compare and project; strings do not.

### A release eval is not the running process

`bin/<release> eval` boots a fresh, throwaway instance; it is not the running production process. Use `rpc` for live diagnostics against an already-running release.

**Why:** a fresh instance has none of the state the live one holds, so its answers read like the live one's and are not.

### Never type `q().` into a remote console

`q().` typed or piped into a release's remote console (a `-remsh` session) calls `erlang:halt()` on the remote node, not locally. Never include it in a probe script.

**Why:** the halt lands on the node you are attached to, and a probe that kills the target is the worst outcome.
