---
title: "FAQ: Connecting a Phoenix LiveView Website to the Mesh"
layer: guide
audience: [agent, human]
stage: stable
---

# FAQ: How Do I Connect My Phoenix LiveView Website to the Mesh?

[Back to FAQ index](FAQ.md) · [Back to corpus index](../INDEX.md)

The hard rule first, from `macula-io/CLAUDE.md`: **LiveViews must never
call backend or library services directly.** A LiveView only ever
subscribes to `Phoenix.PubSub` and reacts; something else calls the mesh
and broadcasts the result. `macula-services/mcl-whiteboard` is a real,
live app that follows this, verified below with the actual code — not
just the documented rule.

---

## Inbound: mesh → your app → the browser

```
macula-station  →  :macula_subscriber  →  Phoenix.PubSub.broadcast  →  LiveView handle_info/2  →  browser
```

**The subscriber**, real and complete (`board_lifecycle_mesh_subscriber.ex`,
75 lines total):

```elixir
defmodule ProjectBoards.BoardLifecycleMeshSubscriber do
  @behaviour :macula_subscriber

  @topics [
    "io.macula/whiteboard-commons/whiteboard/board_initiated_v1",
    "io.macula/whiteboard-commons/whiteboard/board_hosted_v1",
    "io.macula/whiteboard-commons/whiteboard/board_archived_v1",
    "io.macula/whiteboard-commons/whiteboard/board_unarchived_v1",
    "io.macula/whiteboard-commons/whiteboard/board_renamed_v1"
  ]
  def topics, do: @topics

  @impl true
  def init(_args), do: {:ok, nil}

  @impl true
  def handle_event(topic, payload, _meta, state) when is_map(payload) do
    if topic in @topics do
      # normalize/1 unwraps {:text, Bin}-tagged mesh wire VALUES first --
      # skipping it and reading straight off `payload` works by accident
      # against a plain map and breaks silently against a real wire
      # payload still carrying those tags.
      raw = normalize(payload)
      fact = %{board_id: field(:board_id, raw), title: field(:title, raw),
               owner: field(:owner, raw), host: field(:host, raw)}
      Phoenix.PubSub.broadcast(MaculaWhiteboardWeb.PubSub, "boards:remote",
        {:remote_board_event, event_type(topic), fact})
    end
    {:noreply, state}
  end
  def handle_event(_topic, _payload, _meta, state), do: {:noreply, state}

  defp event_type(topic), do: topic |> String.split("/") |> List.last()

  defp field(key, map) when is_atom(key) do
    Map.get(map, key, Map.get(map, Atom.to_string(key)))
  end

  defp normalize({:text, b}) when is_binary(b), do: b
  defp normalize(:undefined), do: nil
  defp normalize(m) when is_map(m), do: Map.new(m, fn {k, v} -> {normalize(k), normalize(v)} end)
  defp normalize(l) when is_list(l), do: Enum.map(l, &normalize/1)
  defp normalize(v), do: v
end
```

Worth noticing: **five distinct mesh topics collapse into one Phoenix.PubSub
topic** (`"boards:remote"`), disambiguated by `event_type` carried inside
the broadcast tuple rather than mirrored 1:1. The topic space you design
for your Phoenix app doesn't have to match the mesh's topic space — it
should match what your LiveViews actually need to subscribe to.

**Starting the subscriber** goes through a "Starter" `GenServer` in the
supervision tree, not the raw `:macula_subscriber` directly — it retries
until `:mcl_om.mesh_handles()` returns `{:ok, pool, realm}` (the mesh
pool connects asynchronously off its own init path, so a naive one-shot
start can race it and lose). `:macula_subscriber`'s topic argument is one
binary, not a list, so the starter spawns **one subscriber process per
topic** against the same shared callback module — five children here, not
one (`board_lifecycle_mesh_subscriber_starter.ex`):

```elixir
def handle_info(:start_subscribers, state) do
  case :mcl_om.mesh_handles() do
    {:ok, pool, realm} ->
      Enum.each(
        ProjectBoards.BoardLifecycleMeshSubscriber.topics(),
        &start_subscriber(pool, realm, &1)
      )
      {:noreply, %{state | started: true}}

    _other ->
      Process.send_after(self(), :start_subscribers, @retry_ms)
      {:noreply, state}
  end
end

defp start_subscriber(pool, realm, topic) do
  spec = %{
    id: {ProjectBoards.BoardLifecycleMeshSubscriber, topic},
    start: {:macula_subscriber, :start_link,
      [ProjectBoards.BoardLifecycleMeshSubscriber, pool, realm, topic, [], %{}]},
    restart: :permanent
  }
  DynamicSupervisor.start_child(ProjectBoards.MeshSubscriberSupervisor, spec)
end
```

**The LiveView side — subscribe and react, nothing else**
(`board_live.ex` is a genuinely large file — around 500 lines, most of it
board-specific view logic; below is the mesh-relevant shape only, not a
verbatim excerpt of consecutive lines):

```elixir
# mount/3 has a second clause for a board_id URL param, both funneling
# into a shared render_board/4 helper that does the actual subscribe:
def mount(_params, _session, socket) do
  {:ok, %{board: board, shapes: shapes}} = find_or_host_default_board()
  {:ok, render_board(socket, default_board_id(), board, shapes)}
end

defp render_board(socket, board_id, board, shapes) do
  if connected?(socket) do
    Phoenix.PubSub.subscribe(MaculaWhiteboardWeb.PubSub, "board:" <> board_id)
  end
  # ... assign board_id, peer presence, etc.
end

def handle_info({:board_updated, board}, socket) do
  {:noreply, assign_board_status(socket, board)}
end

def handle_info({:stroke_drawn, stroke}, socket) do
  socket =
    socket
    |> update(:stroke_count, &(&1 + 1))
    |> push_event("shapes:append", stroke)

  {:noreply, socket}
end
# ... :shape_placed, :shape_moved, :cursor_settled, etc. — every clause
# just assign/push_event, none of them touch the mesh
```

No clause anywhere calls `:macula`, `:macula_subscriber`, `:macula_publisher`,
or `:mcl_om` — confirmed by reading the whole module, not assumed from
the rule.

## Outbound: browser → your app → the mesh

This one has more hops than "LiveView calls a service" suggests, because
this codebase (like every mcl-* service) is event-sourced end to end —
the "service" the rule refers to is really the whole CMD→event→PM chain:

```
browser event  →  LiveView handle_event/3  →  application-service dispatch
     →  evoq event persisted  →  PM/emitter (subscribes to that event type)  →  :macula_publisher
```

`handle_event("stroke", params, socket)` calls
`MaybeDrawStroke.dispatch(params)` — an application-service command
handler — never touches `:macula` itself. That dispatch persists an evoq
event. A separate process-manager module,
`board_lifecycle_v1_to_mesh.ex` (`@behaviour :evoq_event_handler`,
`interested_in/0` names the event types it reacts to), picks the event up
**asynchronously** and does the actual mesh publish:

```elixir
{:ok, pool, realm} = :mcl_om.mesh_handles()
:macula_publisher.start_link(GuideBoardLifecycle.MeshPublisher, pool, realm,
                              topic(event_type), fact, [])
```

with the publisher callback itself as small as this (full file,
`mesh_publisher.ex`):

```elixir
defmodule GuideBoardLifecycle.MeshPublisher do
  # Trivial fire-and-forget :macula_publisher callback shared by every
  # mesh-fact emitter in this app -- none of them need to react to the
  # publish outcome, they just want the supervised pid/mesh-fact
  # machinery macula_publisher already provides around a bare
  # macula:publish/4. Mirrors mcl-tube's tube_mesh_publisher.erl.
  @behaviour :macula_publisher

  @impl true
  def init(_args), do: {:ok, nil}

  @impl true
  def handle_published(result, state) do
    require Logger
    Logger.info("[MeshPublisher] outcome: #{inspect(result)}")
    {:stop, :normal, state}
  end
end
```

The LiveView never knows the mesh exists. Neither does the application
service, directly — it just persists an event; the PM decides that event
is mesh-worthy and publishes it. This is the same Process Manager pattern
this corpus documents generally (see
[`philosophy/PROCESS_MANAGERS.md`](../philosophy/PROCESS_MANAGERS.md)),
applied to "publish to the mesh" as the cross-cutting concern instead of
"trigger another Division."

## Building this in your own app

1. Write your `:macula_subscriber`/`:macula_publisher` callback modules —
   see [FAQ: Developing Edge Services in BEAM Languages](FAQ_DEVELOP_EDGE_SERVICES_BEAM.md)
   for the raw behaviour shapes.
2. Start the subscriber under your supervision tree via a retry-until-ready
   "Starter" wrapper, not directly — the mesh pool isn't guaranteed ready
   at your app's boot.
3. In the subscriber's `handle_event/4`, broadcast to a `Phoenix.PubSub`
   topic your LiveViews actually want to subscribe to — it does not need
   to match the mesh topic name.
4. LiveViews call `Phoenix.PubSub.subscribe/2` in `mount/3` (guarded by
   `connected?(socket)`) and react in `handle_info/2`. Never call `:macula`
   from a LiveView module, in either direction.
5. For the outbound direction, let your existing CQRS/event-sourcing
   pipeline own it: a PM subscribed to the relevant evoq event type calls
   `:macula_publisher`, not the LiveView or the command handler directly.

Only `mcl-whiteboard` was verified firsthand for this FAQ — treat it as
one confirmed real example, not a claim that every Phoenix+macula app in
this workspace follows an identical shape.

## See also

- [`philosophy/PROCESS_MANAGERS.md`](../philosophy/PROCESS_MANAGERS.md) — the general pattern this section's outbound chain is an instance of
- [FAQ: Developing Edge Services in BEAM Languages](FAQ_DEVELOP_EDGE_SERVICES_BEAM.md) — the raw `:macula_publisher`/`:macula_subscriber` behaviours
- [FAQ: Connecting Blazor to the Mesh](FAQ_CONNECT_BLAZOR.md) — the closest analog in a different web stack, no comparable prior art there
