---
title: evoq_bit_flags — status bits and the full API
layer: skill
audience: [agent, human]
stage: stable
---

# EVOQ_BIT_FLAGS

*Aggregate status is a bit-flag integer. Labels are computed in projections, never client-side.*

---

## The rule

1. **Every aggregate status is an integer of `evoq_bit_flags` — never a
   string, never a bare atom.** Flags are powers of 2, defined in the
   aggregate's status header (`{aggregate}_status.hrl`), one flag per
   lifecycle slice (`skills/`'s sibling rule lives in
   `philosophy/AGGREGATE_LIFECYCLE_SLICES.md`).
2. **Transitions in the domain, checks in the domain.** Handlers and
   policies transition with `set/2`/`unset/2` and check with
   `has/2`, `has_not/2`, `has_all/2`, `has_any/2`. A wrong-slice command is
   refused on a flag check, never on a string compare.
3. **Labels are a projection concern.** The flag map lives in one place —
   the `.hrl` — and the human-readable label is computed at projection time
   with `to_string/2` and stored beside the integer. The frontend reads the
   pre-computed label, never decodes bits. This is
   [`STATUS_LABELS_IN_PROJECTIONS.md`](../philosophy/STATUS_LABELS_IN_PROJECTIONS.md),
   which remains the authority on the label half of this rule.

The module is `evoq_bit_flags.erl` in the evoq library (the module doc says
it plainly: "Bit flag manipulation for aggregate state management … a finite
state machine").

## The shape

```erlang
%% game_status.hrl
-define(GAME_NONE,      0).   %% 2#00000000
-define(GAME_INITIATED, 1).   %% birth slice
-define(GAME_OPEN,      2).   %% accepting seats
-define(GAME_STARTED,   4).   %% playing; a clock is running
-define(GAME_ENDED,     8).   %% terminal
-define(GAME_ARCHIVED, 16).   %% death slice
-define(GAME_STATUS_FLAG_MAP, #{
    0  => <<"none">>,
    1  => <<"initiated">>,
    2  => <<"open">>,
    4  => <<"started">>,
    8  => <<"ended">>,
    16 => <<"archived">>}).
```

## Transitions are business logic

`set/2` and `unset/2` are not decoration: **which event sets which bit, and
which bit it clears, is a domain decision written down per event.** The
safe shape for a lifecycle (one flag per slice) is: set the new slice's
flag and clear the previous slice's flag in the same projection write, so
the mask never tells two stories at once and `to_string/2` names the
current slice. `INITIATED` stays set for the dossier's whole life — every
guard checks it — and `ARCHIVED` is the only flag a dead aggregate keeps
besides it.

A real, pinned example (`macula-services/mcl-chess`,
`plans/PLAN_MCL_CHESS.md` §3.1):

| Event | unset | set | status | label |
|---|---|---|---|---|
| `game_initiated_v1` | — | `INITIATED`, `OPEN` | 3 | `initiated, open` |
| `game_started_v1` | `OPEN` | `STARTED` | 5 | `initiated, started` |
| `game_ended_v1` | `STARTED` | `ENDED` | 9 | `initiated, ended` |
| `game_archived_v1` | `ENDED` | `ARCHIVED` | 17 | `initiated, archived` |

A projection that performs both does the unset first (`unset_all` then
`set_all` for multi-flag rows), never one without the other — a transition
that only sets accumulates history in the label, and one that only unsets
leaves the slice unnamed.

## The full API

`-type flags() :: non_neg_integer()`, `-type flag() :: pos_integer()`,
`-type flag_map() :: #{non_neg_integer() => binary() | string()}`.

### Core

| Call | Returns | Purpose |
|---|---|---|
| `set(Target, Flag)` | `Target bor Flag` | set one flag |
| `unset(Target, Flag)` | `Target band bnot Flag` | clear one flag |
| `set_all(Target, [Flag])` | fold of `bor` | set several at once |
| `unset_all(Target, [Flag])` | fold of `band bnot` | clear several at once |

### Queries

| Call | True when | Purpose |
|---|---|---|
| `has(Target, Flag)` | the flag is set | single-flag check |
| `has_not(Target, Flag)` | the flag is not set | negative check (cleaner than `not has/2`) |
| `has_all(Target, [Flag])` | every flag is set | "fully started and not yet ended"-style guards |
| `has_any(Target, [Flag])` | at least one is set | "any terminal state" guards |

### Conversion and analysis

| Call | Returns |
|---|---|
| `to_list(Flags, FlagMap)` | the descriptions of every set flag (map key `0` covers the zero state) |
| `to_string(Flags, FlagMap)` | the descriptions joined by `", "` — the canonical label |
| `to_string(Flags, FlagMap, Sep)` | same, custom separator |
| `decompose(Flags)` | the powers of two that make up the value — audit and debug |
| `highest(Flags, FlagMap)` | description of the highest set flag (severity-style ordering) |
| `lowest(Flags, FlagMap)` | description of the lowest set flag |

## The projection pattern (with the label)

```erlang
%% projection
NewStatus = evoq_bit_flags:set(CurrentStatus, ?GAME_ARCHIVED),
StatusLabel = evoq_bit_flags:to_string(NewStatus, ?GAME_STATUS_FLAG_MAP),
project_games_store:execute(Db,
    "UPDATE games SET status = ?1, status_label = ?2 WHERE game_id = ?3",
    [NewStatus, StatusLabel, GameId]).
```

The query desk returns both fields, and the label is passed through —
never recomputed at the query, never decoded client-side.

## Anti-patterns

| Anti-pattern | Why it's wrong |
|---|---|
| A status as a string or atom in the aggregate | no finite-state machine, string compares, drift |
| Flag constants duplicated in the frontend | a copy of server truth that drifts (a real bug this corpus has already caught: `VL_DISCOVERING=1` client-side vs `8` server-side) |
| Computing the label in the query desk | too late — the projection already ran |
| A second flag map anywhere outside the `.hrl` | two sources of truth for the same bits |

---

## Related

- [`../philosophy/STATUS_LABELS_IN_PROJECTIONS.md`](../philosophy/STATUS_LABELS_IN_PROJECTIONS.md) — the label doctrine, authority for the display half.
- [`../philosophy/AGGREGATE_LIFECYCLE_SLICES.md`](../philosophy/AGGREGATE_LIFECYCLE_SLICES.md) — the slices these flags represent.
- [`NAMING_CONVENTIONS.md`](NAMING_CONVENTIONS.md) — the status header row (`{aggregate}_status.hrl`).
