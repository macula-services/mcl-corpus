---
title: "ANTIPATTERNS: Structure"
layer: skill
audience: [agent, human]
stage: stable
---

# ANTIPATTERNS: Structure — Code Organization Violations

*Demons about code structure. Vertical slicing, not horizontal layers.*

[Back to Index](INDEX.md)

---

## 🔥 Incomplete Desks / Flat Workers

**Date:** 2026-02-04
**Origin:** the removed daemon architecture review

### The Antipattern

CMD slices that are missing components or have workers directly supervised by the domain supervisor.

**Symptoms:**
```erlang
%% BAD: Domain sup directly supervises workers
manage_capabilities_sup
├── capability_announced_v1_to_mesh   % Worker — WRONG LEVEL
├── remote_capabilities_listener      % Worker — WRONG LEVEL
└── ...
```

**Missing pieces:**
- No desk supervisor (`*_desk_sup.erl`)
- No responder (`*_responder_v1.erl`) — can't receive HOPEs from mesh
- Emitters exist but float orphaned at domain level

### The Rule

> **Domain supervisors ONLY start desk supervisors + shared infra.**
> **Desk supervisors start all workers for that desk.**

```erlang
%% GOOD: Domain sup → Desk sups → Workers
manage_capabilities_sup
├── manage_capabilities_store         % Shared infra (OK at domain level)
├── announce_capability_desk_sup      % Supervisor
│   ├── announce_capability_responder_v1    % Worker
│   └── capability_announced_v1_to_mesh     % Worker
├── update_capability_desk_sup        % Supervisor
│   └── ...
└── retract_capability_desk_sup       % Supervisor
    └── ...
```

### Complete Desk Checklist

Every CMD desk MUST have:
- [ ] `*_desk_sup.erl` — Desk supervisor
- [ ] `*_v1.erl` — Command record
- [ ] `*_v1.erl` — Event record
- [ ] `maybe_*.erl` — Handler
- [ ] `*_responder_v1.erl` — HOPE → Command (mesh inbound)
- [ ] `*_to_mesh.erl` — Event → FACT emitter (mesh outbound)

Optional:
- [ ] `on_{event}_maybe_*.erl` — Policy/PM for cross-domain

### Why It Matters

Without responders, your domain can emit but not receive. You have a mouth but no ears.

Without desk supervisors, your supervision tree is flat and you lose fault isolation per feature.

See [CARTWHEEL.md](../../philosophy/CARTWHEEL.md) for the complete canonical structure.

---

## ⚠️ Listeners as Separate Desks (REVERSED 2026-05-24)

**Date:** 2026-02-08
**Reversed:** 2026-05-24
**Origin:** Division listener architecture discussion

### Status: REVERSED

This demon was reversed. The current rule (see [Demon 18 below](#-demon-18-process-managers-inside-desks)) is the opposite: **PMs and cross-domain listeners ARE their own slices**, sibling to desks, named `on_{source_event}_{action}_{target}/`. The discoverability of `on_*` directories at the filesystem level was judged more valuable than co-locating the trigger with the desk it serves.

The 2026-02-08 framing — "listener belongs IN desk X" — is no longer canonical. It applied a vertical-slice heuristic to the wrong axis: PMs cut *across* slices, so they get their own slice rather than being nested in one. A listener that does nothing but `pg:join` and forward to a single desk is still legitimate — it just lives in its own `on_*/` slice.

The single remaining caution: don't create an `on_*` slice that wraps a trivial in-process callback the desk could just do itself. Cross-domain integration via pg / mesh = sibling slice. Internal handler chaining within the same domain = stays in the desk.

---

## 🔥 Centralized Listener Supervisors

**Date:** 2026-02-08
**Origin:** the removed daemon architecture refinement

### The Antipattern

Creating a central supervisor for all listeners across domains.

**Example (WRONG):**
```
apps/{service}_listeners/src/
├── {service}_listeners_sup.erl          # Central supervisor
├── venture_initiated_listener.erl
├── division_discovered_listener.erl
└── capability_announced_listener.erl
```

Or within a domain:
```
apps/design_division/src/
├── design_division_listeners_sup.erl     # Still wrong!
├── listeners/                             # Horizontal directory
│   ├── division_discovered_listener.erl
│   └── ...
```

### The Rule

> **Each PM / cross-domain listener owns its own slice supervisor.** No central listener supervisor, no `listeners/` directory.

### The Correct Structure

PMs are sibling slices to desks under the domain supervisor. Each PM slice owns a single-worker supervisor.

```
apps/design_division/src/
├── initiate_division/                                          # desk
│   ├── initiate_division_desk_sup.erl
│   └── ...
│
├── on_division_discovered_initiate_division/                   # PM sibling slice
│   ├── on_division_discovered_initiate_division_sup.erl
│   └── on_division_discovered_initiate_division.erl
│
└── on_all_desks_implemented_complete_division/                 # another PM sibling slice
    ├── on_all_desks_implemented_complete_division_sup.erl
    └── on_all_desks_implemented_complete_division.erl
```

The domain supervisor starts each PM slice's supervisor alongside the desk supervisors.

### Why It Matters

- **Fault isolation** — PM crash only affects its own slice.
- **Discoverability** — `on_*` directories scream which external events the domain reacts to.
- **No orphans** — Every PM has a clear owner (its slice sup).
- **Vertical slicing** — No horizontal grouping by technical concern.

See [PROCESS_MANAGERS.md](../../philosophy/PROCESS_MANAGERS.md) and [INTEGRATION_TRANSPORTS.md](../../philosophy/INTEGRATION_TRANSPORTS.md) for slice structures.

---

## Demon 14: God Module API Handlers

**Date exorcised:** 2026-02-10
**Where it appeared:** `apps/mcl_api/src/mcl_api_*.erl`
**Cost:** 137-file refactoring to fix

### The Demon

Putting all API endpoints for a domain in a single file with multiple `init/2` clauses:

```erlang
❌ WRONG: God module with 16 init/2 clauses
-module(mcl_api_mentors).
-export([init/2]).

init(Req0, [submit]) -> handle_submit(Req0);
init(Req0, [list_learnings]) -> handle_list_learnings(Req0);
init(Req0, [get_learning]) -> handle_get_learning(Req0);
init(Req0, [validate]) -> handle_validate(Req0);
init(Req0, [reject]) -> handle_reject(Req0);
init(Req0, [endorse]) -> handle_endorse(Req0);
%% ... 10 more clauses, 289 lines total
```

### Why It's Wrong

- **Horizontal grouping** — groups by "all mentors HTTP stuff" instead of by business operation
- **Violates vertical slicing** — the API handler is separated from the command/event/handler it serves
- **Growing forever** — every new endpoint adds to the same file
- **Hard to find** — `handle_validate` could be anything; you must read the whole file
- **Duplicated helpers** — each god module reinvents `dispatch_result/3`, `error_response/3`

### The Correct Pattern

Each desk owns its API handler:

```erlang
✅ CORRECT: Handler lives in its desk
apps/mentor_agents/src/validate_learning/
├── validate_learning_v1.erl
├── learning_validated_v1.erl
├── maybe_validate_learning.erl
└── validate_learning_api.erl    # ~30 lines, single-purpose
```

### The Lesson

> **API handlers are part of the desk, not part of the API app.**
> One endpoint = one `*_api.erl` file in the desk directory.
> Each handler exports `routes/0` — the central aggregator discovers them automatically.
> See Demon #25 for why centralized route files are wrong.

### How This Was Fixed

Replaced 11 god modules (1,700+ lines) with 50 desk-based handlers (~30-50 lines each).
All handlers use `mcl_api_utils` from the `shared` app for response helpers.
Routes standardized under `/api/` prefix.

Reference: `../skills/codegen/erlang/CODEGEN_ERLANG_TEMPLATES.md` → API Handler Templates

---

## 🔥 Demon 18: Process Managers Inside Desks

**Date exorcised:** 2026-02-12 (original direction)
**Reversed:** 2026-03-12 (rationale recorded); reinforced 2026-05-24
**Where it appeared:** Various scaffolds that nested `on_{event}_{action}_{target}.erl` inside the target desk directory.
**Cost:** Cross-domain integration points became invisible at the filesystem level — you couldn't tell which external events a domain reacted to without grepping inside every desk.

### The Lie

"A PM is a policy of the desk it triggers. It belongs inside that desk's directory."

This was the original (2026-02-12) framing. **It was wrong.** Production experience showed PMs are not subordinate to a single desk — they are cross-cutting integration points that belong at the same architectural level as desks themselves.

### Why It's Actually Wrong

1. **PMs are cross-slice.** A PM is an integration point between two domains, not a sub-feature of a single desk. Nesting it hides the cross-cutting nature.
2. **Business process flow becomes invisible.** When you `ls src/`, you cannot tell which external events the domain reacts to. You must grep inside every desk directory to find `on_*` files.
3. **One PM can dispatch to multiple desks.** A cancellation cascade, an evacuation force-settle, a fan-out reprice — these don't map 1:1 to any single desk. Nesting in one desk arbitrarily privileges that desk.
4. **The desk-completeness argument cuts both ways.** Yes, hiding the PM inside the desk makes "the desk owns everything." But that's exactly the cost: you lose visibility into integration points.

### The Rule (Current)

> **A PM is a first-class sibling slice in the target CMD app.** Own directory. Own supervisor. Own gen_server. Named `on_{source_event}_{action}_{target}/`.

```
apps/manage_capabilities/src/
├── announce_capability/                                # desk
│   ├── announce_capability_v1.erl
│   ├── capability_announced_v1.erl
│   ├── maybe_announce_capability.erl
│   └── announce_capability_api.erl
│
└── on_llm_detected_announce_capability/                # PM sibling slice
    ├── on_llm_detected_announce_capability_sup.erl
    └── on_llm_detected_announce_capability.erl
```

### Why Sibling, Not Nested

| Concern | Nested-in-desk | Sibling slice |
|---------|----------------|---------------|
| "What external events does this domain react to?" | Hidden — grep needed | Visible — `ls src/` |
| One PM → multiple desks | Awkward (which desk owns it?) | Natural |
| Supervision granularity | PM crash takes down desk infra | PM crash isolated |
| Cross-cutting nature | Implied subordination | Explicit peer |

### The Test

> "When I `ls src/` in a CMD app, can I immediately see every cross-domain integration point?"
>
> If no — PMs are nested inside desks — pull them out into sibling slices.

### The Lesson

> **PMs are cross-slice. They get their own slice. The `on_*` prefix and the slice directory together are the discoverability anchor for business process flow.**

See [PROCESS_MANAGERS.md](../../philosophy/PROCESS_MANAGERS.md) for the canonical pattern and code template.

---

---

## 🔥 Demon 25: Centralized Route Registration Files

**Date exorcised:** 2026-02-16
**Where it appeared:** 15 `*_routes.erl` files across all the daemon-era apps
**Cost:** 15 centralized files deleted, ~102 handlers updated

### The Demon

One file per OTP app that lists all routes for that app's handlers:

```erlang
❌ WRONG: Centralized route file knows about all handlers
-module(breed_snake_gladiators_routes).
-export([routes/0]).

routes() ->
    [{"/api/arcade/gladiators/stables", initiate_stable_api, []},
     {"/api/arcade/gladiators/stables/:stable_id", get_stable_api, []},
     {"/api/arcade/gladiators/stables/:stable_id/champion/duel", start_champion_duel_api, []},
     {"/api/arcade/gladiators/heroes", heroes_api, []},
     {"/api/arcade/gladiators/heroes/:hero_id", get_hero_api, []},
     {"/api/arcade/gladiators/heroes/:hero_id/duel", start_hero_duel_api, []}].
```

### Why It's Wrong

- **Horizontal grouping** — routes are grouped by app, not by the handler that serves them
- **Every new handler requires editing TWO files** — the handler AND the route file
- **Route file knows too much** — it must import or reference every handler module
- **Merge conflicts** — multiple feature branches touching the same routes file
- **Violates screaming architecture** — a handler's URL path is part of its identity, not a separate concern
- **Same demon as #14** (God Module API Handlers) applied to routing

### The Correct Pattern

Each Cowboy handler exports `routes/0` declaring its own routes:

```erlang
✅ CORRECT: Handler owns its route
-module(initiate_stable_api).
-export([init/2, routes/0]).

routes() ->
    [{"/api/arcade/gladiators/stables", ?MODULE, []}].

init(Req0, State) ->
    %% ...
```

A single central aggregator discovers all handlers via OTP module introspection:

```erlang
✅ CORRECT: Auto-discovery aggregator (the ONLY central file)
-module(mcl_api_routes).
-export([compile/0]).

-define(SERVICE_APPS, [{service}_api, guide_venture_lifecycle, ...]).

compile() ->
    cowboy_router:compile([{'_', discover_routes()}]).

discover_routes() ->
    lists:flatmap(fun collect_app_routes/1, ?SERVICE_APPS).

collect_app_routes(App) ->
    Mods = app_modules(App),
    Handlers = [M || M <- Mods, M =/= ?MODULE, exports_routes(M)],
    lists:flatmap(fun(M) -> M:routes() end, Handlers).

app_modules(App) ->
    case application:get_key(App, modules) of
        {ok, Mods} -> Mods;
        _ -> []
    end.

exports_routes(Mod) ->
    code:ensure_loaded(Mod),
    erlang:function_exported(Mod, routes, 0).
```

### The Key Insight

Adding a new API endpoint requires touching exactly ONE file — the handler itself. The aggregator discovers it automatically because it exports `routes/0`.

### The Test

> "Can I add a new API endpoint by creating a single file?"
>
> **Yes** → routes/0 auto-discovery is working.
> **No, I also need to edit a routes file** → you have a centralized route file demon.

### The Lesson

> **Route ownership follows handler ownership.**
> The handler IS the route. The handler declares its path.
> The aggregator discovers — it never enumerates.

---

## 🔥 Demon 59: Hand-Rolled Mesh Capability Advertising

**Date exorcised:** 2026-09-01 (partially — see Status)
**Where it appeared:** `macula-services/mcl-tube`'s `tube_mesh_providers.erl`
**Cost:** Two live bugs on the same duplicated code, five months apart — a `reuse_sup` factory-supervisor leak, then a silent ~48h DHT TTL default that every other mcl-* service didn't have.

### The Demon

A service implements `-behaviour(mcl_om_service)` (the six-callback contract `mcl_om:boot/1` drives) but, instead of declaring its RPC capabilities through `capabilities/0`, hand-rolls its own `gen_server` that calls `macula_response:advertise_direct/7` directly:

```erlang
❌ WRONG: bespoke advertise loop, duplicating mcl_om_capabilities' job
-module(tube_mesh_providers).
-behaviour(gen_server).

try_advertise({ok, Pool, Realm}, {ok, KeyPair}, State) ->
    {ok, ChannelSup} = macula_response:advertise_direct(
        Pool, Realm, <<"tube.lookup_channel">>, advertise_channel_lookup, [],
        KeyPair, Opts(channel_sup)),
    %% ...own retry timer, own reuse_sup bookkeeping, own (missing) ttl_ms...
```

`mcl_om_capabilities.erl` already exists in `mcl-om` and does exactly this job — TTL, `reuse_sup`, cert-chain, org-qualified double-registration — for every other mcl-* service, in one place. The duplicate doesn't get a library fix for free; it has to be independently rediscovered and independently patched. It was: `mcl_om_capabilities.erl`'s own moduledoc names `tube_mesh_providers.erl` as having hit the `reuse_sup` leak "live before this option existed." Five months later the same file was still on the SDK's raw ~48h envelope TTL default — every other service advertising through `mcl_om_capabilities` gets a curated 2-minute one — because nobody re-applies a library-level correctness fix to a hand-rolled copy of the library's own job.

### Why It's Wrong

- **Not vertical slicing — it's accidental horizontal reimplementation.** The service isn't grouping by technical layer on purpose; it just built its own copy of a cross-cutting concern (`capabilities()` `handler => {Mod, Args}`) that mcl-om already generalizes.
- **Fixes don't propagate.** A correctness fix landed in `mcl_om_capabilities` (TTL, `reuse_sup`) helps every service using it, automatically, on the next deploy. A service with its own copy gets nothing until someone notices the copy exists and ports the fix by hand.
- **Silent drift is invisible from the DHT.** The two paths look identical on the wire (same `procedure_advertisement` shape) — nothing about a `mesh_find_records_by_type` dump flags one entry as hand-rolled and another as library-managed. It surfaces only as a live behavioral difference (a stale record surviving 1440x longer than its siblings).

### The Correct Pattern

Declare the capability; let `mcl_om:boot/1` advertise it:

```erlang
✅ CORRECT: declared capability, advertised generically
-module(mcl_tube_service).
-behaviour(mcl_om_service).

capabilities() ->
    [#{name    => <<"tube.lookup_channel">>,
       version => 1,
       handler => {advertise_channel_lookup, []}}].
```

### Status: Fully Reversed for `mcl-tube`, Not Structurally Prevented Fleet-Wide

`tube_mesh_providers.erl` is deleted. All four of `mcl-tube`'s capabilities (`lookup_channel`, `lookup_video_clip`, `lookup_content`, and `watch_video_clip`) now go through `capabilities/0`. The blocker for the fourth was real, not a workaround: `mcl_om_capabilities:advertise_one/6` only ever called `macula_response:advertise_direct/7`, and `tube.watch_video_clip` is `macula_streamer`-backed. Closed in `mcl_om` 0.18.0 by adding `kind => streamer` (default `response`) to `mcl_om_service:capability()` — `advertise_one/6` now dispatches through `provider_module(Cap)`, `macula_streamer` only when a capability opts in. Both provider modules publish the identical `procedure_advertisement` DHT record and read the same `Opts` keys, so this was a one-function dispatch change, not new plumbing — `call_capability/5,7` (the direct-dial CALL path) deliberately stays response-only, since a streamer capability is consumed via `macula_stream_sink:start_link_direct/5,6`, a genuinely different client-side API.

**No lint rule or type refuses a NEW instance of this demon today.** The nearest thing to a mechanism: `mcl_tube_service_tests.erl` (and every sibling `*_service_tests.erl`) pins the exact `#{name, version, handler}` shape `capabilities/0` returns, so a service that has capabilities but declares `[]` fails its own test suite — but nothing stops a service from ALSO running a parallel `macula_response:advertise_direct` or `macula_streamer:advertise_direct` call elsewhere, the way `mcl-tube` did (twice — a `reuse_sup` leak, then the TTL default), and the way `mcl-rag` independently did too (15 capabilities' worth, `mcl_om` 0.17.0's own changelog). Two independent services hit the same demon before either fix existed to copy. A real mechanism would be a repo-sweep (`grep -rL` for `macula_response:advertise_direct(\|macula_streamer:advertise_direct(` outside `mcl_om_capabilities.erl` itself, across `macula-services/*`) run in CI or on a schedule — not yet built.

### The Test

> "Does this service call `macula_response:advertise_direct` or `macula_streamer:advertise_direct` from anywhere other than `mcl_om_capabilities.erl`?"
>
> If yes and the capability is response-shaped (not streaming) — it should be in `capabilities/0` instead.

### The Lesson

> **A hand-rolled copy of shared infrastructure doesn't inherit the shared infrastructure's future fixes.** Duplication meant the `reuse_sup` fix had to be adopted independently in both `mcl_om_capabilities` and tube's own copy when it landed — twice the work for one bug. Five months later, the TTL fix landed only in `mcl_om_capabilities`; tube's copy still existed to NOT have it, and nobody was assigned to notice the gap. Every fix to shared infrastructure is a fix you have to remember to re-apply to every place that opted out of sharing it.

*Add more demons as we exorcise them.* 🔥🗝️🔥
