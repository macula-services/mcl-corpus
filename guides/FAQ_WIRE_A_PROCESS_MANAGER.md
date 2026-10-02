---
title: "FAQ: Wiring a Process Manager for Cross-Domain Integration"
layer: guide
audience: [agent, human]
stage: stable
---

# FAQ: How Do I Wire a Process Manager for Cross-Domain Integration?

[Back to FAQ index](FAQ.md) · [Back to corpus index](../INDEX.md)

[FAQ: Connecting Phoenix LiveView to the Mesh](FAQ_CONNECT_PHOENIX_LIVEVIEW.md)
already shows one real Process Manager whose job is "publish this event
to the mesh." This page is the general-purpose companion: wiring a PM
for genuine cross-*domain* integration — Domain A's event triggers a
real command in Domain B — using the exact same mechanism.

**Which evoq behaviour first.** evoq 1.26 ships **two** reaction
behaviours, and this page is about the first:

- **`evoq_event_handler`** — subscribes by event type globally; for
  policies, cross-aggregate rules and side effects. This is what every
  shipped service's policy uses (`mcl-bookclub`'s
  `on_member_registered_v1_maybe_plan_party` below). Declare
  `replay_policy() -> skip` when it dispatches.
- **`evoq_process_manager`** — a saga / per-entity state machine: one
  **instance per `correlate/2` id**, `handle/3` returning commands
  (suppressed on replay automatically), optional `compensate/2`. Use it
  when the process has state that must live across events under one id —
  one game, one order, one transfer. Its guide is
  `evoq/guides/process_managers.md`; the philosophy doc's pg/gen_server
  wiring predates it and is illustrative only.

There is **no `evoq_policy` behaviour**. "Policy" is this corpus's word
for the `evoq_event_handler` shape (`on_{event}_maybe_{command}`,
replay-skipping); a policy that needs per-entity instance state *is* a
process manager. Two limits as of evoq 1.26.1: a PM instance cannot
receive a message it sent itself (there is no `handle_info/2` callback —
a deadline belongs to an event handler, or waits on the evoq extension
`mcl-chess` tracks), and an event type only a process manager declares is
not delivered until some event handler also consumes it (evoq #2 — give
the type a handler).

A note on the philosophy doc:
[`philosophy/PROCESS_MANAGERS.md`](../philosophy/PROCESS_MANAGERS.md) is
design intent; the wiring below is what is actually shipped.

---

## The real contract

```erlang
%% evoq_event_handler behaviour
interested_in() -> [binary()].                          % required
init(Config) -> {ok, State} | {error, Reason}.           % required
handle_event(EventType, Event, Metadata, State) ->
    {ok, NewState} | {error, Reason}.                    % required
on_error(Error, Event, FailureContext, State) -> ...      % optional
```

Started via the library's own generic starter —
`evoq_event_handler:start_link(CallbackModule, Config)` — under your
supervision tree. No hand-rolled gen_server, no raw message receiving: the
generic `evoq_event_handler` gen_server does all subscription plumbing;
your callback module is a plain, focused piece of business logic.

## A real example (not just "publish to mesh")

A real policy from `macula-services/mcl-bookclub`, kept here as the
worked illustration of the correct wiring shape: `member_registered_v1`
is emitted by the club's member domain, and the PM reacting to it lives
in the same division — a cross-*aggregate* rule ("every fifth
registration plans a club party") dispatching a command into the club's
own aggregate, never a mesh publish:

```erlang
%% on_member_registered_v1_maybe_plan_party.erl
-module(on_member_registered_v1_maybe_plan_party).
-behaviour(evoq_event_handler).
-export([interested_in/0, init/1, handle_event/4, replay_policy/0]).

interested_in() -> [<<"member_registered_v1">>].

%% A replayed event must not re-dispatch the command.
replay_policy() -> skip.

init(_Config) -> {ok, #{}}.

handle_event(_EventType, Event, _Metadata, State) ->
    Data = maps:get(data, Event, Event),
    %% The cadence rule lives here: count registrations in State and
    %% dispatch plan_party into the club aggregate on every fifth.
    dispatch_plan_party(Data, State).
```

Wired into the division's own supervisor — a one-line child spec, not
a bespoke supervisor of its own:

```erlang
init([]) ->
    Children = [
        emitter(emit_member_registered_v1_to_mesh),
        emitter(on_member_registered_v1_maybe_plan_party)  %% cross-aggregate policy
    ],
    {ok, {SupFlags, Children}}.

emitter(Mod) ->
    #{id => Mod, start => {evoq_event_handler, start_link, [Mod, #{}]},
      restart => permanent, type => worker}.
```


## Naming and location

`on_{source_event}_{action}_{target}`, living in the **target** domain
(the one whose command it dispatches) — this convention is genuinely
followed at scale: dozens of real `on_*` directories exist across
`mcl-tube`, `mcl-victron`, and other org services
alone. This isn't a one-off pattern from a single
example.

## See also

- [`philosophy/PROCESS_MANAGERS.md`](../philosophy/PROCESS_MANAGERS.md) — the conceptual doctrine; its worked example doesn't match real shipped code, see the note above
- [FAQ: Connecting Phoenix LiveView to the Mesh](FAQ_CONNECT_PHOENIX_LIVEVIEW.md) — the same `evoq_event_handler` shape used for "publish to the mesh" instead of cross-domain dispatch
- [FAQ: How do I add event sourcing to a new mcl-* service?](FAQ_ADD_EVENT_SOURCING.md) — the aggregate/command side a PM ultimately dispatches into
