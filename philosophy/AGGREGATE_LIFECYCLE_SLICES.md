---
title: Aggregate Lifecycle Slices
layer: philosophy
audience: [agent, human]
stage: stable
---

# Aggregate Lifecycle Slices

*Every aggregate has a birth slice and a death slice. Everything else happens between them, in strict order.*

---

## The rule

1. **Birth is `initiate_{aggregate}`.** The aggregate is created by an
   `initiate_{aggregate}_v1` command in an `initiate_{aggregate}/` desk. No
   other command may run against an aggregate that was never initiated.
2. **Death is `archive_{aggregate}`.** The aggregate is removed from the
   live world by an `archive_{aggregate}_v1` command in an
   `archive_{aggregate}/` desk. Nothing may run against an archived
   aggregate, ever — it is dead, not dormant. (Retention of the event
   stream is the event store's concern; the archive slice ends the
   aggregate's life in the domain.)
3. **The slices between are a strict order.** The canonical chain is:

```
initiate → … → start → … → end → … → archive
```

   Not every aggregate needs every slice: an aggregate with no distinct
   "running" phase goes `initiate → … → archive`. But where a running
   phase exists — play in progress, a job executing, a session live — the
   slices exist and the order is enforced: `start` requires the aggregate
   to be ready (e.g. seats filled, prerequisites met), `end` requires
   `start`, `archive` requires `end` (or a sanctioned pre-start shortcut,
   below). A command that arrives in the wrong slice is refused with a
   reason naming the slice, never silently accepted.

## Slice duties

| Slice | Command | May | May never |
|---|---|---|---|
| birth | `initiate_{aggregate}_v1` | create the aggregate, record its first state | be called twice; carry state a later event should decide |
| run-up | domain commands (`claim_seat`, `join_team`, …) | fill in what `start` requires | mutate the aggregate past the point of starting |
| start | `start_{aggregate}_v1` | open the running phase (clocks begin, work begins) | run before the run-up is complete |
| activity | domain commands (`submit_move`, …) | advance the state machine | run before `start` or after `end` |
| end | `end_{aggregate}_v1` | close the running phase, record the outcome | produce a second outcome |
| death | `archive_{aggregate}_v1` | remove the aggregate from the live world | be called before `end` — with one sanctioned exception: a run-up that is abandoned before it ever started (e.g. a game withdrawn before both seats were filled) archives directly, recording that it never existed as a running aggregate |

## Who dispatches the transitions

Callers initiate and act. **The mechanical transitions — start, end,
archive — are dispatched by policies and process managers, not by
callers:** `on_{event}_maybe_{command}` (`on_seat_claimed_v1_maybe_start_game`,
`on_clock_flagged_v1_maybe_end_game`, `on_game_ended_v1_maybe_archive_game`).
A caller-triggerable `archive` exists only where an operator or an external
process needs the death slice on demand; the policy path remains the
canonical one. This keeps the lifecycle deterministic and replayable: every
transition is a consequence of events, and the `maybe_*` handler is where
slice order is enforced (see `philosophy/DDD.md` — the handler reads
aggregate state, never a read model).

## Status bits follow the slices

The aggregate's status is an `evoq_bit_flags` integer with one flag per
slice (`INITIATED`, `OPEN`, `STARTED`, `ENDED`, `ARCHIVED` — see
`skills/EVOQ_BIT_FLAGS.md`). The slice invariants are flag checks:

```erlang
%% maybe_submit_move
case evoq_bit_flags:has_all(Status, [?GAME_STARTED]) andalso
     evoq_bit_flags:has_not(Status, ?GAME_ENDED) of
    true  -> dispatch(SubmitMove, State);
    false -> refuse(submit_move_v1, <<"game_not_running">>)
end
```

## A worked shape: one chess game

```
initiate_game_v1   (birth: game_id, time control, seats open)
  → seat_claimed_v1 ×2
  → on_seat_claimed_v1_maybe_start_game ⇒ start_game_v1
  → game_started_v1    (white's clock starts)
  → move_played_v1 ×n  (clock start/stop per move)
  → game_ended_v1      (checkmate | stalemate | insufficient material | clock_flag | resignation)
  → on_game_ended_v1_maybe_archive_game ⇒ archive_game_v1   (after retention)
  → game_archived_v1   (death: out of the live read model)
```

`macula-services/mcl-chess` applies this end to end; its plan
(`plans/PLAN_MCL_CHESS.md`) is the reference for the slice chain in a real
division.

---

## Related

- [`SESSION_LEVEL_CONSISTENCY.md`](SESSION_LEVEL_CONSISTENCY.md) — `initiate_*`
  commands return the new state; `archive_*` is removal for callers too.
- [`PARENT_CHILD_AGGREGATES.md`](PARENT_CHILD_AGGREGATES.md) — the birth event
  of a child aggregate, and who dispatches it.
- [`DDD.md`](DDD.md) — replay and determinism: the lifecycle is a sequence of
  events, nothing else.
- [`skills/EVOQ_BIT_FLAGS.md`](../skills/EVOQ_BIT_FLAGS.md) — the status
  integer these slices live in.
- [`skills/NAMING_CONVENTIONS.md`](../skills/NAMING_CONVENTIONS.md) — the
  command/event names above follow it exactly.
