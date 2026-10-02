---
title: Evoq Behaviours
layer: codegen
audience: [codegen]
stage: stable
---

# Evoq Behaviours — Complete Reference

**Package:** `evoq` (hex.pm, `~> 1.26`; this page matches 1.26.1)
**Source:** `reckon-db-org/evoq/src/` — every callback below is copied from the
module's own `-callback` / `-optional_callbacks` attributes, so the source is
the authority if the two ever disagree.

Evoq provides **24 behaviours** in four categories: Core Domain (what you
implement for business logic), Integration (HOPE / FACT / FEEDBACK actors that
cross a bounded-context boundary), Infrastructure/Adapter (pluggable backends),
and Lifecycle/Extension (customization hooks).

---

## Core Domain Behaviours

### 1. `evoq_aggregate` — Consistency Boundary

The aggregate is the consistency boundary in event sourcing. It processes commands and emits events.

**Required callbacks:**

| Callback | Spec | Description |
|----------|------|-------------|
| `state_module/0` | `-> module()` | The `evoq_state` module that owns this aggregate's state record |
| `init/1` | `init(AggregateId :: binary()) -> {ok, State}` | Initialize aggregate state |
| `execute/2` | `execute(State, Command :: map()) -> {ok, [Event]} \| {error, Reason}` | Execute command, return events |
| `apply/2` | `apply(State, Event :: map()) -> NewState` | Apply event to update state |

**CRITICAL:** `execute(State, Command)` and `apply(State, Event)` — **State comes FIRST!**

**Optional callbacks:**

| Callback | Description |
|----------|-------------|
| `snapshot/1` | Serialize state for snapshot storage |
| `from_snapshot/1` | Restore state from snapshot |

**Started via:** `evoq_aggregate:start_link/2,3`. Managed by `evoq_aggregate_registry` (on-demand via `evoq_aggregate_partition_sup`).

**Example:**

```erlang
-module(territory_auction_aggregate).
-behaviour(evoq_aggregate).
-export([state_module/0, init/1, execute/2, apply/2]).

state_module() -> territory_auction_state.

init(_AggregateId) ->
    {ok, #territory_auction{}}.

execute(State, #{command_type := open_territory_auction_v1} = Cmd) ->
    maybe_open_territory_auction:execute(State, Cmd);
execute(State, #{command_type := close_bidding_v1} = Cmd) ->
    maybe_close_bidding:execute(State, Cmd).

apply(State, #{event_type := <<"territory_auction_opened_v1">>} = Event) ->
    %% Update state from event data
    Data = maps:get(data, Event),
    State#territory_auction{status = ?OPENED, ...}.
```

---

### 2. `evoq_state` — The Aggregate's State Record ("default read model")

The state module owns the aggregate's state record: how to create it, how to
fold one event into it, and how to serialize it for feedback and snapshots.
`evoq_aggregate:state_module/0` names it.

**Required callbacks:**

| Callback | Spec | Description |
|----------|------|-------------|
| `new/1` | `new(AggregateId :: binary()) -> State` | Initial state for a fresh dossier |
| `apply_event/2` | `apply_event(State, Event :: map()) -> State` | Pure, deterministic fold of one event |
| `to_map/1` | `to_map(State) -> map()` | Serialize (feedback, snapshots, inspection) |

**Optional callbacks:** `from_map/1` — `from_map(Map) -> {ok, State} | {error, Reason}` (snapshot loading).

---

### 3. `evoq_command` — Command Record

Commands represent intentions to change state.

**Required callbacks:**

| Callback | Spec | Description |
|----------|------|-------------|
| `command_type/0` | `-> atom()` | The command's type atom |
| `new/1` | `new(Params :: map()) -> {ok, Command} \| {error, Reason}` | Construct from a params map |
| `to_map/1` | `to_map(Command) -> map()` | The payload the aggregate's `execute/2` receives |

**Optional callbacks:**

| Callback | Spec | Description |
|----------|------|-------------|
| `validate/1` | `validate(Command) -> ok \| {ok, Command} \| {error, Reason}` | Custom validation |
| `from_map/1` | `from_map(Map) -> {ok, Command} \| {error, Reason}` | Rebuild from a plain map (wire / replay) |

**Usage:**

```erlang
%% Wrap a command for dispatch
Cmd = evoq_command:new(
    open_territory_auction_v1,    %% command_type
    territory_auction_aggregate,  %% aggregate module
    AuctionId,                    %% aggregate_id (the stream id)
    #{territory => Territory, ...}  %% payload
).

%% Dispatch (validate + execute + append)
{ok, Version, Events} = evoq_router:dispatch(Cmd).
```

`evoq_router:dispatch/1,2` returns `{ok, Version, Events} | {error, Reason}`.
Never discard that result — it is the only error channel (Demon 49).
`evoq_command_router:dispatch_with_state/2` returns
`{ok, Version, Events, State}` for session-level consistency.

---

### 4. `evoq_event` — Event Record

Events are immutable facts, past tense, produced by aggregates.

**Required callbacks:**

| Callback | Spec | Description |
|----------|------|-------------|
| `event_type/0` | `-> atom()` per the spec; every real event module in this workspace returns a **binary** (`<<"x_v1">>`), which is what `evoq_event_handler:interested_in/0` matches on | The event's type |
| `new/1` | `new(Params :: map()) -> Event` | Construct |
| `to_map/1` | `to_map(Event) -> map()` | The stored payload |

**Optional callbacks:** `from_map/1` — `from_map(Map) -> {ok, Event} | {error, Reason}`.

---

### 5. `evoq_event_handler` — Event Subscription (Side Effects)

Event handlers subscribe to event types (not streams) and process events as they are published. **This is what every real emitter, projection and cross-aggregate policy in this workspace implements** — per-entity state machines are `evoq_process_manager` (section 7); see `guides/FAQ_WIRE_A_PROCESS_MANAGER.md` and `guides/FAQ_QUERY_READ_MODELS.md` for live examples.

**Required callbacks:**

| Callback | Spec | Description |
|----------|------|-------------|
| `interested_in/0` | `-> [EventType :: binary()]` | Event types to subscribe to |
| `init/1` | `init(Config :: map()) -> {ok, State} \| {error, Reason}` | Initialize handler state |
| `handle_event/4` | `handle_event(EventType, Event, Metadata, State) -> {ok, NewState} \| {error, Reason}` | Process event |

**Optional callbacks:**

| Callback | Description |
|----------|-------------|
| `on_error/4` | Custom error handling strategy (see `evoq_error_handler`) |
| `replay_policy/0` | `skip \| deliver`. `skip` for anything with a side effect (publishing, dispatching, sending); `deliver` for handlers rebuilding in-memory state. Undeclared delivers and logs a warning naming the handler. |
| `handle_info/2` | Messages the handler scheduled to itself from `handle_event/4`, most usefully a deadline or retry via `erlang:send_after/3`. This is the only evoq reaction surface with it — see section 7. |

**Started via:** `evoq_event_handler:start_link/2,3` — `start_link(CallbackModule, Config)`, a one-line child spec in the owning slice's supervisor. Registers with `evoq_event_type_registry` by event type.

**Example (mesh emitter, real shape — `macula-services/mcl-bookclub`):**

```erlang
-module(emit_member_registered_v1_to_mesh).
-behaviour(evoq_event_handler).
-export([interested_in/0, init/1, handle_event/4, replay_policy/0]).

interested_in() -> [<<"member_registered_v1">>].

%% A restart's replay must not re-publish facts that already went out.
replay_policy() -> skip.

init(_Config) -> {ok, #{}}.

handle_event(_EventType, Event, _Metadata, State) ->
    Data = maps:get(data, Event, Event),
    case mcl_om:mesh_handles() of
        {ok, Pool, Realm} ->
            Fact = mcl_bookclub_facts:to_wire(mcl_bookclub_facts:member_registered(Data)),
            publish_on(Pool, Realm, Fact, State);
        {error, _} = Error ->
            Error
    end.
```

---

### 6. `evoq_projection` — Read Model Builder

Projections transform events into read model updates. They are idempotent (can be replayed safely) and track progress via checkpoints.

**Required callbacks:**

| Callback | Spec | Description |
|----------|------|-------------|
| `interested_in/0` | `-> [EventType :: binary()]` | Event types to project |
| `init/1` | `init(Config) -> {ok, State, ReadModel}` | Initialize with read model |
| `project/4` | `project(Event, Metadata, State, ReadModel) -> {ok, NewState, NewReadModel} \| {skip, State, ReadModel}` | Transform event |

**Optional callbacks:**

| Callback | Description |
|----------|-------------|
| `on_error/4` | Custom error handling |

**Started via:** `evoq_projection:start_link/2,3` (opts: `checkpoint_store`, `start_from`). Supports `rebuild/1,2` to clear and replay.

**Difference from `evoq_event_handler`:** Projections manage a read model, have checkpoint support, and can be rebuilt. Event handlers are for fire-and-forget side effects. In practice every real projection in this workspace is an `evoq_event_handler` writing to its own ETS/SQLite/barrel table (see `guides/FAQ_QUERY_READ_MODELS.md`) — `evoq_projection`'s `init/1 -> {ok, State, ReadModel}` shape exists but is not what shipped code uses.

---

### 7. `evoq_process_manager` — Cross-Aggregate Saga

Coordinates long-running business processes spanning multiple aggregates. Correlates events to process instances and dispatches commands.

**Required callbacks:**

| Callback | Spec | Description |
|----------|------|-------------|
| `interested_in/0` | `-> [EventType :: binary()]` | Event types to handle |
| `correlate/2` | `correlate(Event, Metadata) -> {start, ProcId} \| {continue, ProcId} \| {stop, ProcId} \| false` | Route event to process instance |
| `handle/3` | `handle(State, Event, Metadata) -> {ok, NewState} \| {ok, NewState, [#evoq_command{}]} \| {error, Reason}` | Process event, optionally dispatch commands |
| `apply/2` | `apply(State, Event) -> NewState` | Apply event to PM state |

**Optional callbacks:**

| Callback | Spec | Description |
|----------|------|-------------|
| `init/1` | `init(ProcessId :: binary()) -> {ok, State}` | Initialize PM state for a new process instance |
| `compensate/2` | `compensate(State, FailedCommand :: #evoq_command{}) -> {ok, [#evoq_command{}]} \| skip` | Compensating commands for saga rollback |

**Started via:** `evoq_process_manager:start/2,3`. Routes via `evoq_pm_router` -> `evoq_pm_instance`, one instance per `{process manager module, ProcessId}` (1.26.0; before that two managers correlating on the same id shared an instance). The simple, stateless "on event X dispatch command Y" policies this workspace names `on_{event}_{action}_{target}` are `evoq_event_handler`s, not `evoq_process_manager`s — reach for this behaviour only when a process genuinely has per-instance state across several events.

**Replay:** on a restart, `handle/3` and `apply/2` run for every replayed event and the instance rebuilds exactly the state it had — but **the commands `handle/3` returns are not dispatched** (dispatching again would re-issue its whole history). Events appended while the node was down arrive as new and dispatch normally. This is the behaviour's replay guarantee; an `evoq_event_handler` must declare `replay_policy/0` instead.

**Two limits as of 1.26.1:** an instance cannot receive a message it sent itself (there is no `handle_info/2` callback and the idle timer only logs), so a timer or deadline needs an `evoq_event_handler` with `handle_info/2` — or the evoq extension `mcl-chess` tracks; and an event type only a process manager declares is not delivered until some event handler also consumes it (evoq #2). Run one on one node for now (instance routing is cluster-wide, evoq #10).

---

### 8. `evoq_decision` — Dynamic Consistency Boundary (DCB)

A Decision sits alongside the aggregate on the write side: where an aggregate locks on its own stream version, a Decision locks on the absence of new events matching a tag-filter context (`append_if_no_tag_matches`). See `philosophy/CONSISTENCY_BOUNDARIES.md` and `examples/DCB_COUNTER.md`.

**Required callbacks:**

| Callback | Spec | Description |
|----------|------|-------------|
| `context/1` | `context(Command) -> context_filter()` | The tag filter this decision reads before deciding (`{any_of, Tags}`, `{all_of, Tags}`, `{event_type, Bin}`, `{and_, [...]}`, `{or_, [...]}`) |
| `decide/2` | `decide(ContextEvents, Command) -> {ok, [Event]} \| {error, Reason}` | Pure decision over the context events |

**Optional callbacks:**

| Callback | Spec | Description |
|----------|------|-------------|
| `retry_budget/0` | `-> non_neg_integer()` | Retries on `context_changed` conflicts (default 3) |
| `boundary_key/1` | `boundary_key(Command) -> binary() \| undefined` | Opt into the per-node stateful actor by naming a stable partition key |
| `init_decision_model/0` | `-> Model` | With `apply_context_event/2`: fold the context into a model instead of handing `decide/2` the raw event list |
| `apply_context_event/2` | `apply_context_event(Model, Event) -> Model` | The fold step for that model |

**Dispatched via:** `evoq_decision_runtime:dispatch/3`.

---

## Integration Behaviours (HOPE / FACT / FEEDBACK)

These cross a bounded-context boundary. Domain events stay internal; what leaves is a **fact** (fire-and-forget) or the **feedback** to a **hope** (request/response). See `philosophy/INTEGRATION_TRANSPORTS.md` and `skills/INTEGRATION_ACTORS.md`.

### 9. `evoq_fact` — Integration Fact Contract

Translates a domain event into a serializable payload other bounded contexts consume, via pg (local) or mesh (WAN).

**Required:** `fact_type/0 -> binary()`, `from_event(EventType :: atom(), EventData :: map(), Metadata :: map()) -> {ok, Payload :: map()} | skip`.
**Optional:** `serialize/1`, `deserialize/1`, `schema/0`.

### 10. `evoq_emitter` — Event → Fact Publisher

Subscribes to one domain event and publishes it as a fact on a transport.

**Required:** `source_event/0 -> atom()`, `fact_module/0 -> module()` (an `evoq_fact`), `transport/0 -> pg | mesh`, `emit(FactType :: binary(), Payload :: map(), Metadata :: map()) -> ok | {error, Reason}`.

### 11. `evoq_listener` — Fact → Command Entry Point

Receives integration facts from a transport and dispatches commands to the local aggregate — the entry point for cross-domain integration.

**Required:** `source_fact/0 -> binary()`, `transport/0 -> pg | mesh`, `handle_fact(FactType :: binary(), Payload :: map(), Metadata :: map()) -> ok | skip | {error, Reason}`.

### 12. `evoq_hope` — Outbound Request Contract

A hope is the request half of an RPC between agents or bounded contexts; unlike a fact it expects a response.

**Required:** `hope_type/0 -> binary()`, `new(Params) -> {ok, Hope} | {error, Reason}`, `to_payload(Hope) -> map()`, `from_payload(Payload) -> {ok, Hope} | {error, Reason}`.
**Optional:** `validate/1`, `serialize/1`, `deserialize/1`, `schema/0`.

### 13. `evoq_feedback` — Response Contract

The response to a hope. Carries the post-event aggregate state so the caller gets session-level consistency (`philosophy/SESSION_LEVEL_CONSISTENCY.md`).

**Required:** `feedback_type/0 -> binary()`, `from_result({ok, State} | {error, Reason}) -> map()` (binary keys, JSON-serializable, MUST include `<<"status">>` = `"ok"` | `"error"`), `to_result(Payload :: map()) -> {ok, State} | {error, Reason}`.
**Optional:** `serialize/1`, `deserialize/1`.

### 14. `evoq_responder` — Hope → Command → Feedback

Receives a hope, dispatches the command, and returns the post-event aggregate state as feedback.

**Required:** `hope_type/0 -> binary()`, `handle_hope(HopeType :: binary(), Payload :: map(), Metadata :: map()) -> {ok, State} | {error, Reason}`.
**Optional:** `feedback_module/0 -> module()` (which `evoq_feedback` serializes the response).

### 15. `evoq_requester` — Send Hope, Await Feedback

The caller side of the RPC.

**Required:** `hope_module/0 -> module()` (an `evoq_hope`), `send(Hope, Opts :: map()) -> {ok, Feedback :: map()} | {error, Reason}`.

---

## Infrastructure/Adapter Behaviours

### 16. `evoq_adapter` — Event Store Backend

Pluggable event store interface. Implementation: `reckon_evoq_adapter` (connects to ReckonDB via reckon_gater). `evoq_event_store` is the facade evoq itself calls.

| Callback | Description |
|----------|-------------|
| `append/4` | Append events with version check (-1=NO_STREAM, -2=ANY, N>=0=exact) |
| `read/5` | Read events from stream (start, count, direction) |
| `read_all/3` | Read all events from stream |
| `read_by_event_types/3` | Read events by type across all streams |
| `version/2` | Get current stream version |
| `exists/2` | Check if stream exists |
| `list_streams/1` | List all streams |
| `delete_stream/2` | Delete stream and events |

**Optional:** `read_all_global/3`, `ccc_read_by_payload/4`, `ccc_read_by_payload_hash/4`, `payload_indexes/1`, `payload_hash_indexes/1` (the CCC secondary-index surface, reckon-db 5.x).

Config: `{evoq, [{event_store_adapter, reckon_evoq_adapter}]}` — the `store=1` scaffold option generates this block (see `guides/FAQ_ADD_EVENT_SOURCING.md`).

### 17. `evoq_subscription_adapter` — Subscription Backend

| Callback | Description |
|----------|-------------|
| `subscribe/5` | Create subscription (types: stream, event_type, event_pattern, event_payload, tags) |
| `unsubscribe/2` | Remove subscription |
| `ack/4` | Acknowledge event processed |
| `get_checkpoint/2` | Get current checkpoint position |
| `list/1` | List all subscriptions |
| `get_by_name/2` | Get subscription by name |

### 18. `evoq_snapshot_adapter` — Snapshot Backend

| Callback | Description |
|----------|-------------|
| `save/5` | Save snapshot at version |
| `read/2` | Read latest snapshot |
| `read_at_version/3` | Read snapshot at exact version |
| `delete/2` | Delete all snapshots for stream |
| `delete_at_version/3` | Delete specific snapshot version |
| `list_versions/2` | List all snapshot versions |

### 19. `evoq_read_model` — Read Model Store

**Required:** `init/1`, `get/2`, `put/3`, `delete/2`
**Optional:** `list/2`, `clear/1`
**Reference impl:** `evoq_read_model_ets` (ETS-backed, in-memory)

### 20. `evoq_checkpoint_store` — Projection Checkpoint Persistence

**Required:** `load/1`, `save/2`
**Optional:** `delete/1`
**Reference impls:** `evoq_checkpoint_store_ets` (ETS-backed, lost on restart), `reckon_evoq_checkpoint_store` (durable, in reckon_evoq)

---

## Lifecycle/Extension Behaviours

### 21. `evoq_aggregate_lifespan` — Aggregate Lifecycle Control

Controls idle timeouts, hibernation, and passivation (snapshot + stop).

**Required:**

| Callback | Description |
|----------|-------------|
| `after_event/1` | Return action after processing event |
| `after_command/1` | Return action after processing command |
| `after_error/1` | Return action after error |

**action() type:** `timeout() | infinity | hibernate | stop | passivate`

**Optional:** `on_timeout/1`, `on_passivate/1`, `on_activate/2`
**Default impl:** `evoq_aggregate_lifespan_default` (30min idle, 5min error, auto-snapshot on passivate)

### 22. `evoq_middleware` — Command Pipeline Interceptor

All optional: `before_dispatch/1`, `after_dispatch/1`, `after_failure/1`, each `(#evoq_pipeline{}) -> #evoq_pipeline{}`.
Config: `{evoq, [{middleware, [my_middleware]}]}` or per-dispatch opts.

Pipeline record: `#evoq_pipeline{command, context, assigns, halted, response}`

### 23. `evoq_event_upcaster` — Event Schema Evolution

**Required:** `upcast(Event, Metadata) -> {ok, Transformed} | {ok, Transformed, NewEventType :: binary()} | skip`
**Optional:** `version() -> pos_integer()`
Registered with `evoq_type_provider`. Chainable via `chain_upcasters/3`.

### 24. `evoq_error_handler` — Error Handling Strategy

All optional: `on_error/4`, `max_retries/0`, `backoff_ms/1`
**error_action():** `retry | {retry, DelayMs} | skip | stop | {dead_letter, Reason}`
Default: exponential backoff (100ms base, 30s max), 5 retries, then dead letter.

---

## Quick Decision Guide

| Need | Behaviour |
|------|-----------|
| Enforce business rules, emit events | `evoq_aggregate` (+ `evoq_state` for the record) |
| Cross-cutting invariant over a tag set, not one stream | `evoq_decision` |
| Define / validate a command | `evoq_command` |
| Define an event | `evoq_event` |
| React to events (side effects, pg/mesh, read-model writes, `on_*` policies) | `evoq_event_handler` |
| Build a checkpointed, rebuildable read model | `evoq_projection` |
| Coordinate across aggregates with per-instance state (saga) | `evoq_process_manager` |
| Publish a domain event to another bounded context | `evoq_fact` + `evoq_emitter` |
| Consume another context's fact | `evoq_listener` |
| Request/response across contexts | `evoq_hope` + `evoq_requester` (caller), `evoq_responder` + `evoq_feedback` (callee) |
| Transform old event versions | `evoq_event_upcaster` |
| Add logging/auth/metrics to dispatch | `evoq_middleware` |
| Control aggregate memory lifecycle | `evoq_aggregate_lifespan` |
| Plug in different event store | `evoq_adapter` |
| Plug in subscription mechanism | `evoq_subscription_adapter` |
| Plug in snapshot storage | `evoq_snapshot_adapter` |
| Plug in read model storage | `evoq_read_model` |
| Plug in checkpoint persistence | `evoq_checkpoint_store` |
| Custom error recovery strategy | `evoq_error_handler` |

## Common Patterns in Our Codebase

**Emitter (event handler → mesh):** `emit_{event}_to_mesh.erl` — subscribes to event, publishes a fact to the mesh
**Projection (event → table):** `{event}_to_{table}.erl` — projects event to an ETS/SQLite/barrel read model
**Process Manager:** `on_{event}_{action}_{target}.erl` policies react to one event and dispatch one command — an `evoq_event_handler` living in the target domain. A process with per-instance state across events (one clock per game, one saga per order) is an `evoq_process_manager` with `correlate/2` keying the instance.
