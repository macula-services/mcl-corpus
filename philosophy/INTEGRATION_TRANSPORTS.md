---
title: Integration Transports
layer: philosophy
audience: [agent, human]
stage: stable
---

# Integration Transports

How divisions integrate: **within a division** by direct evoq subscription
(projections, policies and emitters subscribe to the event store — see
[EVENT_SUBSCRIPTION_FLOW.md](EVENT_SUBSCRIPTION_FLOW.md)), and **across
services and agents** over the mesh. Clients reach a service through its
HTTP handlers or its mesh procedures. Each `mcl-*` service hosts one
division, so integration is exactly two things: evoq within it, mesh
between them.

---

## The one cross-service layer: mesh

1. **WAN-capable** - QUIC transport, NAT traversal
2. **Cross-service** - Service-to-service and agent-to-agent communication
3. **DHT discovery** - Find capabilities across the network
4. **Realm isolation** - Multi-tenant by design

---

## Event Subscription Flow

**Emitters, policies and projections subscribe to the event store via evoq. They are NOT called manually.**

See [EVENT_SUBSCRIPTION_FLOW.md](EVENT_SUBSCRIPTION_FLOW.md) for the full canonical pattern.

```
ReckonDB -> evoq subscription -> emitter (emit_{event}_to_mesh)  -> mesh publish
ReckonDB -> evoq subscription -> policy (on_{event}_maybe_{cmd}) -> command dispatch
ReckonDB -> evoq subscription -> projection ({event}_to_{target}) -> SQLite write
```

**API handlers dispatch commands and return. They do NOT call emitters.**

---

## Domain Events vs Integration Facts

Not every domain event becomes an integration fact.

| Concept | Transport | Decision |
|---------|-----------|----------|
| **Domain Event** | evoq (within the division) | Always available for projections and policies |
| **Integration Fact** | mesh | Selective - only what other services and agents need |

Emitters decide what to publish. They subscribe via evoq and emit autonomously — the real, current shape (`macula-services/mcl-bookclub`):

```erlang
%% emit_member_registered_v1_to_mesh.erl — the only place this event
%% touches the mesh; the dispatch path never waits for it.
-module(emit_member_registered_v1_to_mesh).
-behaviour(evoq_event_handler).
-export([interested_in/0, init/1, handle_event/4, replay_policy/0]).

interested_in() -> [<<"member_registered_v1">>].

%% A restart's replay of the store's history must not re-publish facts
%% that already went out.
replay_policy() -> skip.

init(_Config) -> {ok, #{}}.

handle_event(_EventType, Event, _Metadata, State) ->
    Data = maps:get(data, Event, Event),
    publish(mcl_bookclub_facts:to_wire(mcl_bookclub_facts:member_registered(Data)), State).

publish(Fact, State) ->
    case mcl_om:mesh_handles() of
        {ok, Pool, Realm} -> publish_on(Pool, Realm, Fact, State);
        {error, _} = Error -> Error
    end.
```

A failed publish is an **error return**, so evoq's retry machinery owns
redelivery — a consumer that missed "member registered" is missing state,
not a sample.

---

## Naming Conventions

### Emitters (Publishers)

```
emit_{event}_to_mesh.erl
```

| Transport | Example |
|-----------|---------|
| mesh | `emit_member_registered_v1_to_mesh.erl` |

### Listeners (Subscribers)

**Service-side -- CMD desks** (a mesh fact triggers a command):
```
on_{fact}_from_mesh_maybe_{command}.erl
```

Example:
```
on_division_discovered_v1_from_mesh_maybe_initiate_division.erl
```

**Service-side -- PRJ desks** (a mesh fact triggers a projection):
```
on_{fact}_from_mesh_project_to_{storage}_{target}.erl
```

Example:
```
on_venture_initiated_v1_from_mesh_project_to_sqlite_ventures.erl
```

Same-division projections need no listener at all — they subscribe to the
store via evoq and are named `{event}_to_{storage}_{target}.erl`.

---

## Listener Placement Rule

> **A cross-service listener / PM is its own sibling slice in the target CMD app.** Own directory, own supervisor, own handler. Named `on_{source_fact}_{action}_{target}/`.

Listeners are NOT centralized — no `listeners/` directory, no `*_listeners_sup`. They are also NOT nested inside the desk they trigger. They sit as siblings of desks under the domain supervisor so the `on_*` directories scream which external facts the domain reacts to when you `ls src/`.

> **Decision history:** Earlier guidance (2026-02-08) placed listeners INSIDE the desk they trigger. That was reversed 2026-03-12 / reinforced 2026-05-24 — see [antipatterns/structure.md Demon 18](../skills/antipatterns/structure.md#-demon-18-process-managers-inside-desks) and [PROCESS_MANAGERS.md Location Rule](PROCESS_MANAGERS.md#location-rule).

---

## CMD Slice Structure

The target division's CMD app contains two kinds of slices:

```
apps/design_division/src/
├── initiate_division/                                          # desk slice
│   ├── initiate_division_desk_sup.erl
│   ├── initiate_division_v1.erl
│   ├── division_initiated_v1.erl
│   ├── emit_division_initiated_v1_to_mesh.erl
│   ├── maybe_initiate_division.erl
│   └── initiate_division_api.erl
│
└── on_division_discovered_initiate_division/                   # PM sibling slice
    ├── on_division_discovered_initiate_division_sup.erl
    └── on_division_discovered_initiate_division.erl
```

**PM supervision:**
```erlang
%% on_division_discovered_initiate_division_sup.erl
init([]) ->
    Children = [
        #{id => on_division_discovered_initiate_division,
          start => {on_division_discovered_initiate_division, start_link, []},
          restart => permanent,
          type => worker}
    ],
    {ok, {#{strategy => one_for_one, intensity => 10, period => 10}, Children}}.
```

The domain supervisor starts both the desk sup and each PM slice sup.

---

## PRJ Desk Structure

```
apps/query_ventures/src/
└── venture_initiated_v1_to_ventures/
    ├── venture_initiated_v1_to_ventures_sup.erl
    └── venture_initiated_v1_to_sqlite_ventures.erl
```

**Pattern:**
| Component | Naming |
|-----------|--------|
| Directory (desk) | `{event}_to_{target}/` |
| Supervisor | `{event}_to_{target}_sup.erl` |
| Projection | `{event}_to_{storage}_{target}.erl` (same division, evoq) or `on_{event}_from_mesh_project_to_{storage}_{target}.erl` (another service's fact) |

---

## Supervision Hierarchy

```
query_ventures_sup (domain supervisor)
├── venture_initiated_v1_to_ventures_sup (desk supervisor)
│   └── venture_initiated_v1_to_sqlite_ventures (worker)
├── venture_brief_updated_v1_to_ventures_sup (desk supervisor)
│   └── venture_brief_updated_v1_to_sqlite_ventures (worker)
└── query_ventures_store (SQLite connection worker)
```

```
design_division_sup (domain supervisor)
├── design_division_store (ReckonDB store)
├── initiate_division_desk_sup (desk supervisor)
│   └── initiate_division workers
├── complete_division_desk_sup (desk supervisor)
│   └── complete_division workers
├── on_division_discovered_initiate_division_sup (PM slice supervisor)
│   └── on_division_discovered_initiate_division (evoq_event_handler)
└── on_all_desks_implemented_complete_division_sup (PM slice supervisor)
    └── on_all_desks_implemented_complete_division (evoq_event_handler)
```

---

## Implementation Examples

### Mesh emitter (subscribes via evoq, publishes facts)

See the `emit_member_registered_v1_to_mesh` example under "Domain Events
vs Integration Facts" above — it is the real, current shape.

### Mesh listener (CMD desk -- cross-service integration)

```erlang
%% on_division_identified_v1_from_mesh_maybe_initiate_division.erl
-module(on_division_identified_v1_from_mesh_maybe_initiate_division).
-behaviour(evoq_event_handler).
-export([interested_in/0, init/1, handle_event/4, replay_policy/0]).

interested_in() -> [<<"division_identified_v1">>].

%% A replayed fact must not re-dispatch the command.
replay_policy() -> skip.

init(_Config) -> {ok, #{}}.

handle_event(_EventType, Event, _Metadata, State) ->
    case initiate_division_v1:from_fact(Event) of
        {ok, Cmd} -> maybe_initiate_division:dispatch(Cmd);
        {error, _Reason} -> ok
    end,
    {ok, State}.
```

### Projection via evoq subscription (same division, direct)

```erlang
%% venture_initiated_v1_to_sqlite_ventures.erl
-module(venture_initiated_v1_to_sqlite_ventures).
-behaviour(evoq_event_handler).
-export([interested_in/0, init/1, handle_event/4, replay_policy/0]).

interested_in() -> [<<"venture_initiated_v1">>].

%% A projection's write is idempotent: replaying is safe, so it declares
%% `deliver` (unlike emitters and policies, which declare `skip`).
replay_policy() -> deliver.

init(_Config) -> {ok, #{}}.

handle_event(_EventType, Event, _Metadata, State) ->
    project(Event, State).
```

---

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Correct Approach |
|--------------|----------------|------------------|
| `src/listeners/` directory | Horizontal grouping by technical concern | One PM = one sibling slice named `on_*/` |
| `*_listeners_sup.erl` | Central supervisor for all listeners | Each PM slice owns its own supervisor |
| PM nested inside the desk it triggers | Hides cross-service integration points from `ls src/` | PM as sibling slice (Demon 18) |
| mesh for within-division chatter | Massive overhead, wrong tool | evoq subscription |
| Anonymous listener without `on_*` naming | Unclear purpose; not discoverable | Every PM names what it reacts to AND what it does |
| SSE streaming to frontends | Complexity for little benefit | Use polling or WebSocket (future) |

---

## Decision Record

| Date | Decision |
|------|----------|
| 2026-02-08 | Use `mesh` for external integration (WAN/cross-service) |
| 2026-02-08 | ~~Listeners live in the desk they trigger~~ (REVERSED 2026-03-12 — see entry below) |
| 2026-03-12 | PMs / cross-service listeners are sibling slices in the target CMD app (own slice dir, own sup). Reversed 2026-02-08 decision. Rationale: `on_*` directories provide filesystem-level discoverability of integration points; PMs are cross-slice by nature. Reinforced 2026-05-24. |
| 2026-02-08 | Naming: `on_{event}_from_{transport}_maybe_{command}.erl` |
| 2026-02-08 | Naming: `on_{event}_from_{transport}_project_to_{storage}_{target}.erl` |
| 2026-02-08 | PRJ desk directory: `{event}_to_{target}/` |
| 2026-02-13 | Emitters subscribe to ReckonDB via evoq -- not called manually from API handlers |
| 2026-02-13 | Emitters are projections -- same subscription mechanism, different output target |
| 2026-02-13 | Same-division projections subscribe via evoq; another service's facts arrive via mesh listeners |
| 2026-02-13 | See [EVENT_SUBSCRIPTION_FLOW.md](EVENT_SUBSCRIPTION_FLOW.md) for canonical pattern |
