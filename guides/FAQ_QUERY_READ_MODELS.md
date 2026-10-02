---
title: "FAQ: Querying a Read Model (QRY+PRJ)"
layer: guide
audience: [agent, human]
stage: stable
---

# FAQ: How Do I Query a Read Model (the QRY+PRJ Departments)?

[Back to FAQ index](FAQ.md) · [Back to corpus index](../INDEX.md)

The companion to
[FAQ: How do I add event sourcing to a new mcl-* service?](FAQ_ADD_EVENT_SOURCING.md) —
projections turn events into a read model, and a query desk answers
questions against it. Real examples below from
`macula-services/mcl-whiteboard` and `macula-services/mcl-stations`.

---

## The real `query_{read_model}` app, and its desks

`mcl-whiteboard`'s `query_boards` is a genuinely separate Mix app,
with desks named exactly per this workspace's own convention:
`get_board_snapshot_by_id/`, `get_board_snapshot_by_id_over_mesh/`,
`list_hosted_boards/`, `list_archived_boards/`, `list_boards_over_mesh/`,
plus two projection-facing desks,
`answer_board_snapshot_queries/`/`answer_board_list_queries/`.

**Local read, real code**:

```elixir
def call(board_id) do
  case :ets.lookup(Store.boards_table(), board_id) do
    [{^board_id, board}] ->
      shapes = :ets.lookup(Store.board_shapes_table(), board_id) |> Enum.map(fn {_id, stroke} -> stroke end)
      as_of_version = Store.shape_version(board_id)
      {:ok, %{board: Map.put(board, :board_id, board_id), shapes: shapes, as_of_version: as_of_version}}
    [] -> {:error, :not_found}
  end
end
```

**Worth saying plainly**: this workspace's own documentation states QRY+PRJ
apps default to SQLite read models — but this real, live example uses a
plain in-memory **ETS table** instead. Both are legitimate; don't treat
SQLite as the only real pattern just because it's the documented default.

**The local-first, mesh-fallback pattern** — `GetBoardSnapshotByIdOverMesh`,
already referenced in
[FAQ: Connecting Phoenix LiveView to the Mesh](FAQ_CONNECT_PHOENIX_LIVEVIEW.md)'s
`board_live.ex` snippet, is a genuinely good real pattern worth copying
directly: publish a query fact naming a fresh, per-call reply topic;
**subscribe to that reply topic first**, before publishing the query
(avoids racing a fast responder's reply against your own subscribe
call); go through `:macula_publisher`/`:macula_subscriber` rather than
raw `macula:publish/4`, same convention as every other mesh-facing module
in this corpus; and on reply, materialize the result into the *same* ETS
tables the local path reads, so both `mount/3` clauses in the LiveView
return an identical shape regardless of which path answered.

## The projection: `{event}_to_{table}`, and the `evoq_event_handler` gotcha (again)

```elixir
defmodule ProjectBoards.BoardLifecycleToBoards.BoardLifecycleToBoards do
  # @behaviour :evoq_event_handler, NOT :evoq_projection -- the latter's
  # init/1 -> {ok, State, ReadModel} shape was only ever documented,
  # never exercised anywhere real.
  @behaviour :evoq_event_handler

  @impl true
  def interested_in, do: ["board_initiated_v1", "board_hosted_v1", "board_archived_v1",
                           "board_unarchived_v1", "board_renamed_v1"]

  @impl true
  def init(_config), do: {:ok, %{}}

  @impl true
  def handle_event(event_type, event, _metadata, state) do
    data = field(:data, event)
    board_id = field(:board_id, data)
    table = Store.boards_table()
    existing = case :ets.lookup(table, board_id) do
      [{^board_id, row}] -> row
      [] -> %{owner: nil, title: nil, status: 0}
    end
    updated = apply_event(event_type, existing, data)
    :ets.insert(table, {board_id, updated})
    Phoenix.PubSub.broadcast(MaculaWhiteboardWeb.PubSub, "board:" <> board_id, {:board_updated, updated})
    {:ok, state}
  end

  defp apply_event("board_hosted_v1", row, _data), do: %{row | status: :evoq_bit_flags.set(row.status, 4)}
  # ... one clause per event type, each doing exactly one bit-flag/field update

  # Events arrive with atom OR string keys depending on the path (fresh
  # dispatch vs. replay from the store) -- read both, in that order.
  defp field(key, map) when is_atom(key) do
    Map.get(map, key, Map.get(map, Atom.to_string(key)))
  end
end
```

This is the workspace's own real, current confirmation of the
`evoq_event_handler`-not-`evoq_projection` gotcha this corpus already
documents as a wire-format gotcha elsewhere — read it directly here
rather than taking that gotcha on faith. Note it does **all
calculations in the projection**, matching this workspace's CQRS
convention, and pushes the live update straight to any subscribed
LiveView via `Phoenix.PubSub` — the same "PM decides what's
mesh-worthy, projection decides what's read-model-worthy" split.

## A second, genuinely different real pattern: no separate QRY app at all

`macula-services/mcl-stations` does **not** split into a
`query_stations` app — it's a single `mcl_stations` app whose RPC
handler reads directly from a `barrel_docdb`-backed module, with no
aggregate, command, or event anywhere in this path:

```erlang
%% list_stations.erl
-module(list_stations).
-behaviour(macula_response).
handle_request(Payload, State) ->
    {ok, Rows} = station_read_model:fold(fun(Doc, Acc) -> {ok, [Doc | Acc]} end, []),
    {reply, #{stations => apply_filters(Payload, Rows)}, State}.
```

`station_read_model` is populated by ingesting DHT records directly
(`ingest_node_records/`), not by evoq events at all. **The
`query_{read_model}` app-per-department split is a convention for
larger, multi-desk services — not an absolute rule.** A single-capability
service like `mcl-stations` keeping read-model ingestion and
query-answering in one app is a legitimate, real, deployed pattern too.

## See also

- [FAQ: How do I add event sourcing to a new mcl-* service?](FAQ_ADD_EVENT_SOURCING.md) — the CMD side these projections consume from
- [FAQ: Connecting Phoenix LiveView to the Mesh](FAQ_CONNECT_PHOENIX_LIVEVIEW.md) — `board_live.ex` calling `GetBoardSnapshotById`/`GetBoardSnapshotByIdOverMesh` directly
- [FAQ: Developing Edge Services in BEAM Languages](FAQ_DEVELOP_EDGE_SERVICES_BEAM.md) — `mcl_stations_service.erl`'s `read_model_id/0`/`data_dir/0` barrel_docdb pattern
