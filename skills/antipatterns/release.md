---
title: "ANTIPATTERNS: Release, Testing & Packaging"
layer: skill
audience: [agent, human]
stage: stable
---

# ANTIPATTERNS: Release, Testing & Packaging

*Demons about releases, versioning, hex packaging, testing, and plugin discovery.*

[Back to Index](INDEX.md)

---

## 🔥 Demon 27: Hardcoded User/Submitter IDs

**Date exorcised:** 2026-02-23
**Where it appeared:** a removed app command modules
**Cost:** Every event in the store records the wrong actor — audit trail is useless

### The Lie

"Just use `<<"system">>` or a placeholder for the user ID — we'll fix it later."

### What Happened

Command modules hardcoded the submitter identity:

```erlang
%% WRONG — who actually did this?
Cmd = buy_license_v1:new(#{
    license_id => LicenseId,
    plugin_id => PluginId,
    user_id => <<"system">>   %% Hardcoded placeholder
}),
```

Every event stored in ReckonDB records `<<"system">>` as the actor. The audit trail — "who did what, when" — is destroyed. In an event-sourced system, events are immutable. You cannot retroactively fix the actor identity.

### Why It's Wrong

1. **Audit trail destroyed** — Event sourcing's primary value is a complete, truthful history. Hardcoded actors make the history a lie.
2. **Immutable damage** — Events cannot be amended. Once stored with `<<"system">>`, that event will always say "system did it."
3. **Security blind spot** — No way to trace actions back to actual users for access control, debugging, or compliance.
4. **Multi-user broken** — When two users buy licenses, both events say "system" — indistinguishable.

### The Rule

> **Commands MUST carry the real actor identity. The API handler extracts the user from the request context and passes it through to the command.**

### The Correct Pattern

```erlang
%% API handler extracts identity from request
handle_post(Req0, State) ->
    UserId = extract_user_id(Req0),  %% From auth token, session, etc.
    {ok, Params, Req1} = app_api_utils:read_json_body(Req0),
    Cmd = buy_license_v1:new(#{
        license_id => maps:get(<<"license_id">>, Params),
        plugin_id => maps:get(<<"plugin_id">>, Params),
        user_id => UserId   %% Real actor identity
    }),
    ...
```

For commands triggered by Policies or Listeners (no HTTP request), the actor is the **system process** that initiated the action — record it explicitly:

```erlang
%% Policy — actor is the policy itself
Cmd = remove_plugin_v1:new(#{
    license_id => LicenseId,
    initiated_by => <<"policy:on_license_revoked_v1_maybe_remove_plugin">>
}),
```

### Prevention

- Every command struct MUST have a `submitter_id` or `initiated_by` field
- API handlers MUST extract identity from request context
- Policies/Listeners MUST identify themselves as the actor
- Code review: reject any command with hardcoded `<<"system">>`, `<<"admin">>`, or `<<>>`

### The Lesson

> **Events are immutable history. Hardcoded actor IDs destroy that history permanently.**
> **The identity flows from the entry point (API, Policy, Listener) into the command. No exceptions.**

---

## 🔥 Demon 28: No Tests on Event-Sourced Domains

**Date exorcised:** 2026-02-23
**Where it appeared:** a removed app — 0 tests across 6 CMD desks, 5 projections, 4 query handlers, 4 policies
**Cost:** Bugs found only by dialyzer or at runtime — no safety net for refactoring

### The Lie

"Dialyzer catches type errors, so we don't need tests."

### What Happened

The app shipped with zero tests. Dialyzer caught the `row_to_map` tuple/list bug (Demon #19), but only because it was a type mismatch. Business logic bugs — wrong aggregate guards, incorrect projection SQL, broken policy chains — are invisible to dialyzer.

### What Dialyzer Cannot Catch

| Bug Type | Dialyzer? | Unit Test? |
|----------|-----------|------------|
| Wrong function argument types | Yes | Yes |
| Dead code branches | Yes | Yes |
| Wrong aggregate business rule (rejects valid command) | **No** | Yes |
| Projection writes wrong column value | **No** | Yes |
| Policy dispatches wrong command | **No** | Yes |
| Command validation too permissive | **No** | Yes |
| Event missing required field | **No** | Yes |
| Bit flag combination produces wrong status_label | **No** | Yes |

Dialyzer proves types align. Tests prove behavior is correct. Both are needed.

### Minimum Test Coverage for Event-Sourced Domains

| Component | What to Test | Priority |
|-----------|-------------|----------|
| **Aggregate** | Every command + every business rule guard | Critical |
| **Projection** | Each event type with real `#event{}` record input (Demon #23) | Critical |
| **Command struct** | `new/1` produces valid command, required fields enforced | High |
| **Event struct** | `new/N` produces valid event, `to_map/1` round-trips | High |
| **Policy** | Receives event, dispatches correct command | High |
| **Query API** | `row_to_map` works with actual esqlite3 output format | Medium |

### The Rule

> **Tests must be written BEFORE the code file (preferred) or IMMEDIATELY AFTER it. Never deferred to "before it ships" or attached to a CI/workflow gate.**

The "ship" framing is the lie. By the time something is "shipping" the code has been merged, the author has moved on, and the gap is now a backlog item that never closes. The test belongs alongside the code as a unit of work — not as a downstream chore.

### When to Write Tests

Two acceptable moments:

1. **Before** writing the `.erl` file — TDD style. Write a failing test that describes the slice's behaviour, then write the code that makes it pass. Best when the behaviour is well-understood (e.g. an aggregate guard rejecting an already-archived command).
2. **Immediately after** writing the `.erl` file — same commit, same task, same session. Acceptable when the behaviour took some exploration to land. The bar: the test file lands before the next desk/slice is started.

**Unacceptable:**

- "I'll add tests later" — later never arrives
- "Tests can come in a follow-up PR" — the PR rots in review
- "CI will run them when they exist" — a green CI on zero tests is a lie
- "Pre-commit hook blocks unverified commits" — hooks are local and bypassable, and they don't write tests for you

### Tests Are Not a Workflow Action

> **Test creation MUST NOT depend on any workflow gate — CI, pre-commit hooks, PR templates, release checklists, or any other downstream automation.**

Workflow gates check *whether tests passed*, not *whether tests exist*. A workflow can fail a build for a regression in an existing test. It cannot fail a build for a slice that ships with no test at all — because there's nothing to run, and "no tests" is indistinguishable from "all tests passed" to most green/red signals.

The discipline lives in the author's hands, in the same commit as the code. If the author skips the test, no later automation can recover the missed opportunity to verify behaviour at the moment the design decision was fresh.

### Minimum Viable Test Suite

For an aggregate with N commands:

```erlang
%% 1. Each command produces the right event
initiate_test() ->
    {ok, State} = my_aggregate:init(<<"agg-1">>),
    Cmd = #{command_type => <<"initiate_thing_v1">>, id => <<"t-1">>},
    {ok, [Event]} = my_aggregate:execute(State, Cmd),
    ?assertEqual(<<"thing_initiated_v1">>, maps:get(event_type, Event)).

%% 2. Business rules reject invalid commands
cannot_archive_already_archived_test() ->
    State = state_with_flags(?ARCHIVED),
    Cmd = #{command_type => <<"archive_thing_v1">>, id => <<"t-1">>},
    ?assertMatch({error, already_archived}, my_aggregate:execute(State, Cmd)).

%% 3. Projection handles real #event{} records
projection_with_record_test() ->
    Event = #event{
        event_type = <<"thing_initiated_v1">>,
        data = #{id => <<"t-1">>, name => <<"Test">>},
        stream_id = <<"thing-t-1">>, version = 0,
        event_id = <<"evt-1">>, metadata = #{},
        timestamp = 1000, epoch_us = 1000000
    },
    FlatMap = projection_event:to_map(Event),
    ok = thing_initiated_v1_to_sqlite_things:project(FlatMap).
```

### The Lesson

> **Dialyzer catches type bugs. Tests catch logic bugs. An event-sourced domain without tests is a domain you can't safely refactor.**
> **The appstore's tuple/list bug (Demon #19) was found by dialyzer. The next bug won't be.**
>
> **Write the test in the same session as the code, in the same commit if possible. Never push the responsibility onto CI, hooks, or "later".**

---

## 🔥 Demon 30: Forgetting to Bump `.app.src` Versions Before Tagging

**Date exorcised:** 2026-02-24
**Where it appeared:** a removed app — 4 `.app.src` files stuck at `"0.1.0"` while tagging `v0.2.0`
**Cost:** Had to delete the remote tag, bump versions, re-commit, and re-tag

### The Lie

"Just commit, tag, and push. The version takes care of itself."

### What Happened

A significant feature was implemented (schema extension, new endpoints, bug fixes), committed, tagged as `v0.2.0`, and pushed — but all 4 `.app.src` files still contained `{vsn, "0.1.0"}`. The OCI image built by CI would ship with the old version baked into the BEAM release, causing version mismatches between the git tag and the running application.

### Why It's Wrong

1. **BEAM release version comes from `.app.src`** — `application:get_key(App, vsn)` returns what's in the `.app.src`, not the git tag
2. **OCI images carry the wrong version** — Logs, health endpoints, and manifest responses report the old version
3. **Impossible to debug version mismatches** — "I deployed v0.2.0 but the running service says 0.1.0"
4. **Tag deletion is destructive** — If CI already built on the tag, you have a phantom image with wrong metadata

### The Rule

> **When tagging a release, ALWAYS bump `{vsn, "X.Y.Z"}` in ALL `.app.src` files BEFORE committing and tagging.**

### Pre-Tag Checklist

Before running `git tag vX.Y.Z`:

1. [ ] **Root `.app.src`** — `src/{app_name}.app.src` bumped
2. [ ] **All umbrella app `.app.src` files** — `apps/*/src/*.app.src` bumped
3. [ ] **`rebar3 compile`** — still compiles clean
4. [ ] **Commit the version bump** — version change is IN the tagged commit
5. [ ] **Then tag and push**

### Where to Find `.app.src` Files

```bash
# Erlang umbrella — find all version files
grep -r '{vsn,' src/*.app.src apps/*/src/*.app.src
```

### For Other Ecosystems

| Ecosystem | Version File(s) | Same Rule |
|-----------|----------------|-----------|
| Erlang/OTP | `src/*.app.src`, `apps/*/src/*.app.src` | Yes |
| Tauri | `src-tauri/Cargo.toml` AND `src-tauri/tauri.conf.json` | Yes |
| Elixir | `mix.exs` | Yes |
| Node.js | `package.json` | Yes |

### The Lesson

> **The git tag is a label. The `.app.src` version is the truth. They must match.**
> **Bump versions FIRST, commit, THEN tag. Never the other way around.**

---

## 🔥 Hex Packages Without debug_info

**Date:** 2026-03-05
**Origin:** Dialyzer couldn't analyze reckon_gater beams from hex

### The Antipattern

Publishing a hex package with `no_debug_info` in the build profile:

```erlang
%% rebar.config
{profiles, [
    {prod, [
        {erl_opts, [
            no_debug_info,    %% Strips debug info from beams
            deterministic
        ]}
    ]}
]}.
```

### Why It's Wrong

Consumers need `debug_info` in beam files to run dialyzer. Without it, dialyzer reports "Could not get Core Erlang code" and silently skips the dependency, potentially missing type errors at the boundary.

### The Correct Pattern

```erlang
{prod, [
    {erl_opts, [
        debug_info,       %% KEEP for library packages
        deterministic
    ]}
]}
```

`no_debug_info` is appropriate for **release binaries** (final deployment artifacts), never for **library packages** published to hex.

**Rule:** Libraries on hex.pm MUST include `debug_info`. Only strip it from end-user release tarballs.

---

## 🔥 Containerized reckon_db With a Dynamic BEAM Node Name

**Date:** 2026-05-21
**Origin:** reckon-portal blog Division on reckon-db.org — brief 502 outage on the second redeploy

### The Antipattern

Running a containerized app that embeds **reckon_db** (Ra/Khepri) with the default release node name, `<app>@<container-id>`.

### Why It's Wrong

Ra persists the node name into its on-disk cluster state under the store's `data_dir`. The container hostname (hence the node name) changes on **every** `docker run`/recreate. So on the first boot everything works; on the next redeploy Ra reads its persisted state, sees a "leader" on a node that no longer exists, and waits for it forever:

```
[warning] Retry attempt 1 for store :blog_store after 106ms: :timeout
[warning] Retry attempt 2 ... :timeout      %% backs off to 30s, never recovers
```

The store never serves → the app hangs **unhealthy** → 502. With a persistent volume this bites on the *second* deploy (or the next watchtower auto-update), not the first.

### The Fix

Pin a stable node name in the container env:

```yaml
# docker-compose.yml — on the app service
RELEASE_DISTRIBUTION: name
RELEASE_NODE: reckon_portal@127.0.0.1   # any fixed name; IP avoids DNS
```

Persisted Ra state then stays valid across recreates: `1 record(s) recovered`, leader re-elected on the same node, healthy in ~10s.

### Why a Fresh-Volume Smoke Misses It

A container smoke that uses a **fresh** volume each run boots clean every time — there is no persisted node name to mismatch. **You must test the restart path:** `docker compose up -d --force-recreate` against an *existing* volume, and confirm it stays healthy. First-boot green is not enough for stateful stores.

### Recovery If Already Broken

The dead node name is baked into the volume. Pin the node name AND wipe the stale volume once: `docker compose rm -sf <svc>` (frees the volume), `docker volume rm <project>_<vol>`, then recreate. Safe only if there's no real data yet.

### The Rule

> **Stateful BEAM stores need a stable node identity.** If Ra/Khepri (or Mnesia) data outlives the container, the node name must too.

---

## 🔥🔥 Demon 52: Duplicate `{profiles, ...}` Tuple in rebar.config

**Date:** 2026-05-31
**Origin:** a since-removed service — adding an evoq-testkit `test` profile crash-looped every beam node (exec 127).

### The Mistake

To wire a new test-only dependency I added a **second** top-level
`{profiles, ...}` tuple to `rebar.config` instead of merging into the
existing one:

```erlang
%% WRONG — two top-level profiles tuples
{profiles, [
    {prod, [{relx, [{include_erts, true}, {dev_mode, false}]}]}
]}.

%% ...later in the same file...
{profiles, [
    {test, [{deps, [{evoq_testkit, "~> 0.1"}]}]}
]}.
```

### Why It Bit Hard

**rebar3 keeps only the LAST top-level `{profiles, ...}` tuple.** The
second one shadowed the first entirely, so the `prod` profile vanished.
CI built `:latest` without `prod`'s `include_erts` → an **ERTS-less
release**. The alpine runtime has no system Erlang → the entrypoint
`exec`'d a non-existent VM → **exit 127 crash-loop on every beam**. The
fleet froze: dead store, frozen read model, trips/revenue stuck.

The symptom is maximally misleading: zero BEAM logs (the VM never
starts), just a container restarting forever. It looks like a bad
entrypoint or a missing binary, not a build-config typo.

### The Fix

One `{profiles, ...}` tuple, all profiles inside it:

```erlang
{profiles, [
    {prod, [{relx, [{include_erts, true}, {dev_mode, false}]}]},
    {test, [{deps, [{evoq_testkit, "~> 0.1"}]}]}
]}.
```

(Fixed in parksim `c329b6d`.)

### The Tell

> **exit 127 + zero BEAM logs + alpine runtime = ERTS-less release.**
> Check the image for `/app/erts-*` and confirm `include_erts` survived.
> If a release config seems to have "lost" a profile or term, grep for a
> **duplicate top-level key** — rebar3 silently keeps the last.

### The Rule

> **Never add a second top-level `{profiles, ...}` (or any duplicate
> top-level key) to rebar.config — merge into the existing tuple.**
> rebar3 does not combine them; the last one wins and the rest vanish
> with no warning.

---

## 🔥 Demon 63: Existence Mistaken for Freshness in a Build Cache

**Date exorcised:** 2026-09-05
**Where it appeared:** `macula-io/macula` and `reckon-db-org/reckon-db`, both
`priv/build-nifs.sh` (reckon-db's own header even says "modeled on macula's");
also `macula_quic`'s `fetch-nif.sh`
**Cost:** every "clean `rebar3 eunit`" claim against the affected NIF that day
was silently exercising a compiled binary that predated the fix by hours,
including once for a real security patch

### The Lie

"The `.so` is already there, so it's built."

### What Happened

`build_nif()` skipped compilation whenever the target `priv/*.so` already
existed — an existence check, nothing else. Editing `deterministic.rs` and
running `rebar3 compile && rebar3 eunit` produced a fully green suite that had
tested the SAME artifact as before the edit, because nothing in the script ever
compared the `.so`'s age against the source tree's. A second, related bug rode
along in `fetch-nif.sh`: `MACULA_FORCE_SOURCE_BUILD=1` was meant to force a
rebuild regardless, but the bare existence check ran *before* that flag was
ever consulted, so the one lever built to defeat a stale cache did nothing
whenever the cache had anything cached at all.

### The Signature

**A build script whose cache check is "does the output exist," not "is the
output newer than its inputs," reports success on stale work indefinitely.**
It costs nothing to write and nothing to notice, because the failure mode is
not an error — it's a correct-looking green run against the wrong code. Found
here only because a parallel scratch build, done out of habit rather than
suspicion, disagreed with the "clean" result.

### The Rule

**A build-skip decision must compare source mtime against artifact mtime, not
just check the artifact exists.**

```sh
# WRONG — existence only
[ -f "$SO_PATH" ] && return 0

# RIGHT — rebuild if any source file is newer than the artifact
if [ -f "$SO_PATH" ] && [ -z "$(find "$CRATE_DIR" -newer "$SO_PATH" \
    \( -name '*.rs' -o -name 'Cargo.toml' -o -name 'Cargo.lock' \))" ]; then
  return 0
fi
```

Verified RED (an aged `.so` plus a newer source file → old logic says skip,
reproducing the exact incident in miniature) then GREEN (same fixture, new
logic rebuilds) against an isolated fixture — not just read the diff and
agreed it looked right. And where a force-rebuild escape hatch exists, order
matters: check it **before** any cache-hit path can return early, or the
escape hatch is dead code the day a cache entry exists.

---

## 🔥 Demon 64: A Split Name Doesn't Mean a Split Namespace

**Date exorcised:** 2026-09-05
**Where it appeared:** `macula-io/macula-py`, at its first-ever PyPI publish
**Cost:** a first release plan built on a design that would have collided
with an unrelated package's real import namespace, caught only because the
user asked a sharp question, not because anyone reviewing it checked

### The Lie

"Renaming the distribution name is enough — pip and import are independent,
like beautifulsoup4/bs4."

### What Happened

`macula-py`'s intended PyPI name, `macula`, was already registered — a real,
unrelated project ("Library for creative software design and development",
different author, confirmed live on PyPI). The proposed fix: publish under
`macula-py` while leaving the actual Python import unchanged (`import
macula`), citing `beautifulsoup4`/`bs4` as precedent for distribution and
import names legitimately differing.

That precedent doesn't transfer here, and an assistant reviewing the plan
said so with confidence before checking. `bs4` is not just a *different*
import name from `beautifulsoup4` — it's a name **nothing else uses**. This
case is the opposite: `macula` isn't merely a name the plan wanted to keep,
it is the actual, already-occupied import namespace of the unrelated PyPI
project. Keeping `import macula` while renaming only the distribution name
would mean any environment with both packages installed has two different
projects racing to write into the same top-level `macula/` directory —
whichever installs second silently overwrites or shadows the other. The user
asked one question — "will it not collide when someone imports the original
macula?" — and the answer was yes, immediately, on inspection.

### The Signature

**A real split-name precedent (distro name ≠ import name) was pattern-matched
onto a new case without checking the one fact that actually decides whether
it applies: is the shared string already claimed as an import namespace by
someone else, or just unclaimed as a distribution name?** Those are different
questions. The first makes the precedent irrelevant; the second is exactly
what the precedent solves. Confident, correctly-worded, wrong: the AI
reviewing the plan explained the bs4 pattern accurately and still misapplied
it, because "matches a known-good pattern" was checked and "the specific
premise that pattern depends on holds here" was not.

### The Rule

**When a rename is driven by a namespace collision, verify the fix removes
the collision — don't just verify the rename happened.** The mechanical
check that actually proves it: build the real artifact, install it into a
fresh environment, and confirm the OLD, colliding name is now genuinely
unreachable.

```bash
python -m build
pip install --no-deps dist/macula_py-*.whl   # fresh venv, no local override
python -c "import macula"                     # MUST raise ModuleNotFoundError
python -c "import macula_py; macula_py.identity.KeyPair()"  # and the new name must actually work
```

If the old name still imports successfully after your "fix," the rename
solved nothing — it just moved the string, not the namespace.

---

*We burned these demons so you don't have to. Keep the fire going.* 🔥🗝️🔥
