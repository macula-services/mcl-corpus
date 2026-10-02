---
title: "FAQ: Adding Event Sourcing to a New Macula Service"
layer: guide
audience: [agent, human]
stage: stable
---

# FAQ: How Do I Add Event Sourcing (reckon-db + evoq) to a New Macula Service?

[Back to FAQ index](FAQ.md) · [Back to corpus index](../INDEX.md)

This is the practical CMD-department walkthrough: command → aggregate →
event → dispatch, using a real, live example
(`macula-services/mcl-whiteboard`'s `GuideBoardLifecycle` app) rather
than an abstract description.

---

## The four things `evoq` actually requires

An aggregate is a module implementing the `evoq_aggregate` behaviour
(`reckon-db-org/evoq/src/evoq_aggregate.erl`) — four required callbacks:

```erlang
state_module() -> module().
init(AggregateId) -> {ok, State}.
execute(State, Command) -> {ok, [Event]} | {error, Reason}.
apply(State, Event) -> NewState.
```

(Optional: `snapshot/1`, `from_snapshot/1`.) A command implements
`evoq_command` — `command_type/0`, `new/1`, `to_map/1` required,
`validate/1`/`from_map/1` optional. An event implements `evoq_event` —
`event_type/0`, `new/1`, `to_map/1` required, `from_map/1` optional.
**One thing worth knowing before you copy the spec literally**:
`evoq_event`'s own callback spec says `event_type() -> atom()`, but
every real event module in this workspace returns a plain binary/string
instead — that's what actually matches `evoq_event_handler`'s contract
(`interested_in() -> [binary()]`), and binary is what's load-bearing for
dispatch matching in practice.

## A real, minimal trio (the three files as they are, minus their comments)

`host_board/` desk, `GuideBoardLifecycle` app — command:

```elixir
defmodule GuideBoardLifecycle.HostBoard.HostBoardV1 do
  @behaviour :evoq_command
  defstruct [:board_id]
  @impl true
  def command_type, do: :host_board
  @impl true
  def new(%{board_id: id}) when is_binary(id) and id != "", do: {:ok, %__MODULE__{board_id: id}}
  def new(_), do: {:error, :board_id_required}
  @impl true
  def to_map(%__MODULE__{} = cmd), do: %{command_type: command_type(), board_id: cmd.board_id}
  @impl true
  def from_map(%{board_id: id}), do: {:ok, %__MODULE__{board_id: id}}
  def from_map(_), do: {:error, :missing_required_fields}

  def board_id(%__MODULE__{board_id: v}), do: v
end
```

event:

```elixir
defmodule GuideBoardLifecycle.HostBoard.BoardHostedV1 do
  @behaviour :evoq_event
  alias GuideBoardLifecycle.HostBoard.HostBoardV1
  defstruct [:board_id, :hosted_at]
  @impl true
  def event_type, do: "board_hosted_v1"   # a string, not an atom -- see note above
  @impl true
  def new(%{board_id: id}), do: %__MODULE__{board_id: id, hosted_at: System.system_time(:millisecond)}
  def from_command(%HostBoardV1{} = cmd), do: new(%{board_id: HostBoardV1.board_id(cmd)})
  @impl true
  def to_map(%__MODULE__{} = e), do: %{event_type: event_type(), board_id: e.board_id, hosted_at: e.hosted_at}
  def board_id(%__MODULE__{board_id: v}), do: v
end
```

application-service dispatch entry point:

```elixir
defmodule GuideBoardLifecycle.HostBoard.MaybeHostBoard do
  alias GuideBoardLifecycle.BoardAggregate
  alias GuideBoardLifecycle.HostBoard.BoardHostedV1
  alias GuideBoardLifecycle.HostBoard.HostBoardV1

  def handle(%HostBoardV1{} = cmd) do
    event = BoardHostedV1.from_command(cmd)
    {:ok, [BoardHostedV1.to_map(event)]}
  end

  # Called from the aggregate's own execute/2 (see below) with the raw
  # command map evoq hands it, going through HostBoardV1.from_map/1
  # first rather than assuming the map is already a struct.
  def handle_from_map(payload) do
    case HostBoardV1.from_map(payload) do
      {:ok, cmd} -> handle(cmd)
      {:error, _} = error -> error
    end
  end

  def dispatch(%{board_id: board_id} = params) do
    case HostBoardV1.new(params) do
      {:ok, cmd} ->
        evoq_cmd = :evoq_command.new(:host_board, BoardAggregate, BoardAggregate.stream_id(board_id), HostBoardV1.to_map(cmd))
        :evoq_router.dispatch(evoq_cmd)
      {:error, _} = error -> error
    end
  end
end
```

`:evoq_router.dispatch/1` returns `{ok, Version, Events} | {error, Reason}`
— this is exactly the `Maybe*.dispatch/1` chain
[FAQ: Connecting Phoenix LiveView to the Mesh](FAQ_CONNECT_PHOENIX_LIVEVIEW.md)
already shows a LiveView calling: `handle_event("stroke", ...)` →
`MaybeDrawStroke.dispatch/1` → this same `evoq_router.dispatch` shape.

The real aggregate (`BoardAggregate`) dispatches on `command_type` to a
guard-checked handler that checks the current bit-flag status *before*
delegating:

```elixir
defp do_execute(:host_board, status, payload) do
  cond do
    :evoq_bit_flags.has_not(status, BoardStatus.initiated()) -> {:error, :not_initiated}
    :evoq_bit_flags.has(status, BoardStatus.archived()) -> {:error, :archived}
    true -> MaybeHostBoard.handle_from_map(payload)
  end
end
```

matching this workspace's own documented convention that status fields
are bit flags manipulated via `evoq_bit_flags:set/2`, `unset/2`, `has/2`,
`has_not/2` — all real exports of `evoq_bit_flags` (reckon-db-org/evoq).

## The evoq-only rule (application surface)

Application code — desks, aggregates, policies, projections, emitters,
process managers — uses **evoq's own behaviours and API**, and nothing
below it. In particular, no module in `apps/` calls
`reckon_evoq_adapter`, `reckon_gater` or `reckon_db` directly; the adapter
is named **once, in `config/sys.config.src`** (see the scaffold section
below), and `evoq_store_subscription` is what delivers events to whatever
your app registered. This is what keeps a service portable across stores
and testable without a running reckon cluster.

| Need | evoq surface |
|---|---|
| Command / Event | `evoq_command`, `evoq_event` |
| Aggregate + state | `evoq_aggregate` + the state module |
| Policy / side effect (by event type) | `evoq_event_handler` (+ `replay_policy/0`) |
| Per-entity state machine / saga | `evoq_process_manager` (+ `compensate/2`) |
| Projection into a read model | `evoq_event_handler` today (the deployed practice; `evoq_projection` is documented but not yet exercised in the fleet) |
| Mesh fact / listener | `evoq_emitter`, `evoq_listener` |
| Dispatch | `evoq_router:dispatch/1`, `evoq_command_router:dispatch_with_state/2` |
| Status bits | `evoq_bit_flags` |

**Known gaps (2026-10, evoq 1.26.1).** Three needs have no evoq-only
answer yet, and are tracked rather than worked around: an
`evoq_process_manager` instance cannot receive a message it sent itself
(no `handle_info/2` callback, so a deadline/timer needs an event handler
or an evoq extension); there is no evoq API to mint a store-valid
aggregate id (`reckon_gater_stream_id` lives below the line); and the
canonical `store=1` scaffold's `<name>_app` opens the store by calling
`reckon_db_sup:start_store/1` and `#store_config{}` directly (only
`evoq_store_subscription` is evoq) — either declare boot wiring the
sanctioned exception or add an `evoq_store:open/1` facade. `mcl-chess`'s
plan proposes `handle_info/2` on the PM and
`evoq_adapter:new_stream_id/1`, and adopts the scaffold as-is with the
bootstrap debt recorded.

## Turning on a real store: the scaffold's `store` option

[FAQ: How do I deploy my own mcl-* service?](FAQ_DEPLOY_SERVICES.md)
already covers `rebar3 new mcl_service ...` — here's what the
`store` variable actually does. The template's own doc comment
(`macula-services/mcl-om/priv/templates/mcl_service.template`):

> OFF BY DEFAULT. Empty means no store, which is what most services
> want. Set it to **`1`** and the service opens a reckon-db store called
> `<name>_store`: `store_id/0` and `data_dir/0` are generated,
> `sys.config` gains the evoq adapter block without which the node will
> not boot, the compose file gains a volume, and three boundary guards
> are generated to keep them in step. **WARNING: the value must be
> EXACTLY ONE CHARACTER** — `1` and not `yes`. rebar3 passes template
> variables as strings and mustache iterates a string as a list, so a
> longer value repeats every generated block once per character and the
> result does not compile — a limitation of the template engine, not a
> preference.

So the real invocation is `rebar3 new mcl_service ... store=1` — the
literal digit, not a letter or word. This generates, in
`sys.config.src`:

```erlang
{evoq, [
    {event_store_adapter,    reckon_evoq_adapter},
    {subscription_adapter,   reckon_evoq_adapter},
    {snapshot_store_adapter, reckon_evoq_adapter},
    {store_id,               <name>_store}
]},
```

and in `<name>_service.erl`:

```erlang
-export([store_id/0, data_dir/0]).
store_id() -> <name>_store.
data_dir() -> chosen(os:getenv("MCL_DATA_DIR")).
chosen(false) -> "/tmp/<name>";
chosen("")    -> "/tmp/<name>";
chosen(Path)  -> Path.
```

**Real incident behind the "three boundary guards" line**: a sibling
service once shipped `store_id/0`/`data_dir/0` exported with no `evoq`
sys.config block at all, which put **two of three fleet nodes into a
boot-crash loop** (`{not_configured, event_store_adapter}`) — because
`evoq` starts as a release-boot application *before* any service's
`start/2` runs, so `mcl_om` cannot inject the adapter config at
runtime, unlike capability registration. That's the specific, documented
incident behind adding this as a scaffold option instead of three manual
steps.

A second, related failure mode the generated test suite guards against —
`service.erl`'s `store_id/0` disagreeing with the `evoq` sys.config
block's own `store_id` — doesn't have its own separately-documented
incident of the same scale, but the template's own test comment explains
why it's still checked: "disagreeing opens one store and addresses
another." The generated `the_store_id_agrees_between_erlang_and_config_test/0`
compares the two values directly so this can't ship silently either.

## See also

- [FAQ: How do I query a read model (QRY+PRJ)?](FAQ_QUERY_READ_MODELS.md) — the other side of what these events feed
- [FAQ: How do I wire a Process Manager for cross-domain integration?](FAQ_WIRE_A_PROCESS_MANAGER.md) — reacting to these events outside this aggregate's own boundary
- [FAQ: Developing Edge Services in BEAM Languages](FAQ_DEVELOP_EDGE_SERVICES_BEAM.md) — the `mcl_om_service` scaffold this builds on
- [FAQ: How do I deploy my own mcl-* service?](FAQ_DEPLOY_SERVICES.md) — the `rebar3 new mcl_service` scaffold itself
- [FAQ: How do I call event sourcing from a non-BEAM app?](FAQ_CALL_RECKON_GATEWAY.md) — the same reckon-db store, reached over gRPC instead of in-process evoq
