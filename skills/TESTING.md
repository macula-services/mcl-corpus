---
title: Testing Patterns
layer: skill
audience: [agent, human]
stage: stable
---

# Testing Patterns

Guidelines for testing Macula Erlang applications.

---

## Test Philosophy

> **Tests verify behavior, not implementation.**

Write tests that:
1. Verify the contract (inputs → outputs)
2. Test integration points (pg, SQLite, mesh)
3. Catch regressions before deployment
4. Document expected behavior

---

## Test Before Push

**Never push code without local tests passing.**

```bash
# Run unit tests for specific apps
rebar3 eunit --app=setup_venture,query_ventures

# Run specific test modules
rebar3 eunit --module=emit_venture_initiated_v1_to_mesh_tests

# Verbose output
rebar3 eunit --app=query_ventures -v
```

---

## Test File Location

Tests live alongside the code they test:

```
apps/setup_venture/
├── src/
│   └── initiate_venture/
│       └── venture_initiated_v1_to_mesh.erl
└── test/
    └── emit_venture_initiated_v1_to_mesh_tests.erl   # {module}_tests.erl
```

**Naming:** `{module}_tests.erl` - EUnit auto-discovers tests for a module.

---

## Emitter Tests

The publish path itself is verified by the live check (a real mesh round
trip), not by a unit test. The unit test pins what a unit test can:
which event the emitter subscribes to, and the wire shape of the fact it
builds (the same shape `{app}_facts_tests` pins — see
[MESH_TOPIC_TIERING](MESH_TOPIC_TIERING.md)).

```erlang
-module(emit_my_event_v1_to_mesh_tests).
-include_lib("eunit/include/eunit.hrl").

interested_in_test() ->
    ?assertEqual([<<"my_event_v1">>], emit_my_event_v1_to_mesh:interested_in()).

replay_policy_test() ->
    %% Lifecycle facts must not re-publish on a store replay.
    ?assertEqual(skip, emit_my_event_v1_to_mesh:replay_policy()).
```

## SQLite Integration Tests

### Testing Projections

```erlang
projection_test() ->
    %% Use unique IDs to avoid test pollution
    Id = <<"test-", (integer_to_binary(erlang:system_time(microsecond)))/binary>>,

    Event = #{
        id => Id,
        name => <<"Test Item">>,
        created_at => erlang:system_time(millisecond)
    },

    %% Call projection directly
    ok = my_event_to_sqlite_items:project(Event),

    %% Verify
    {ok, Rows} = my_store:query("SELECT id, name FROM items WHERE id = ?1", [Id]),
    ?assertEqual(1, length(Rows)),
    ?assertMatch([[Id, <<"Test Item">>]], Rows).
```

### Note: esqlite3 Returns Lists

```erlang
%% esqlite3:fetchall returns rows as LISTS, not tuples
{ok, [[Id, Name, Status]]} = my_store:query("SELECT id, name, status FROM items WHERE id = ?1", [Id])

%% NOT tuples:
%% {ok, [{Id, Name, Status}]}  % WRONG assumption
```

---

## Test Patterns by Component

| Component | What to Test | How |
|-----------|-------------|-----|
| **Aggregate** | Execute returns events | Call execute(State, Payload), assert {ok, [EventMaps]} |
| **Emitter** | Subscribers receive messages | Join pg, emit, assert receive |
| **Listener** | Events trigger projections | Emit to pg, check database |
| **Projection** | Correct data written | Call directly, query database |
| **Query** | Correct data returned | Seed database, call query |
| **Handler** | Business logic | Call handle/1, assert events |

---

## Aggregate Tests (CRITICAL)

**Always test aggregates match evoq behaviour callback signatures!**

evoq calls:
- `Module:init(AggregateId)` → `{ok, State}`
- `Module:execute(State, Payload)` → `{ok, [EventMaps]}` or `{error, Reason}`
- `Module:apply(State, Event)` → NewState

### Aggregate Test Pattern

```erlang
-module(my_aggregate_tests).
-include_lib("eunit/include/eunit.hrl").

%% CRITICAL: Test argument order matches evoq expectations
execute_argument_order_test() ->
    %% Initial state
    State = my_aggregate:initial_state(),

    %% Command payload (from command:to_map/1)
    Payload = #{
        command_type => <<"my_command">>,
        id => <<"test-123">>,
        name => <<"Test">>
    },

    %% Execute with correct order: State, Payload
    Result = my_aggregate:execute(State, Payload),

    %% Should return {ok, [EventMap]}
    ?assertMatch({ok, [_]}, Result),

    {ok, [EventMap]} = Result,
    ?assertEqual(<<"my_event_v1">>, maps:get(event_type, EventMap)).

%% Test unknown command returns error
unknown_command_test() ->
    State = my_aggregate:initial_state(),
    Payload = #{command_type => <<"unknown">>},
    ?assertEqual({error, unknown_command}, my_aggregate:execute(State, Payload)).
```

### Why This Matters

The aggregate bug (2026-02-09) was caused by wrong argument order:
- **Wrong:** `execute(Payload, State)` - fails silently with "unknown_command"
- **Correct:** `execute(State, Payload)` - matches evoq behaviour

This test catches the bug immediately. Without it, the bug only appeared at runtime when evoq dispatched a command and the aggregate returned `{error, unknown_command}`.

### evoq-testkit — Sequence-Driven CMD Testing (2026-05-31)

For aggregate/CMD testing, prefer **`evoq_testkit`** (hex `~> 0.1`,
`reckon-db-org/evoq-testkit`) over hand-rolled `execute/2` calls. It is
sequence-driven: inject a command sequence and after EACH command assert
(1) expected events, (2) no unexpected events, (3) no failure / expected
error, (4) correct state.

Two layers:

- **Layer A `evoq_aggregate_spec`** (pure, no store) — `run/3` drives
  `execute/2` + folds `apply/2`. Exact ordered event-type match. The
  command type is carried INSIDE the payload as `command_type` (matching
  the runtime `Command#evoq_command.payload`).
- **Layer B `evoq_cmd_case`** (persistence) — `with_mem_store/1` swaps in
  `mem_evoq_adapter`, `dispatch_all/4` replays the scenario through
  `evoq_dispatcher` asserting each `{ok, _, _}`, `assert_stream/3` reads
  back and compares, and `assert_valid_stream_id/1` runs the reckon_gater
  guard.

> **Always include `evoq_cmd_case:assert_valid_stream_id/1`.** mem-evoq's
> append does NOT enforce reckon-db's `^[a-z]{1,32}-[a-f0-9]{32}$` stream-id
> regex, so a Layer-B test passes while production rejects every write
> (antipatterns Demon 51). This assertion is the only thing that catches a
> human-readable aggregate id in a test.

### eunit Aggregate Gotchas

- **Callbacks must be a separate module.** Put `init/execute/apply` in a
  real aggregate module (e.g. `lamp_aggregate`), not inline in the
  `_tests` module — inline callbacks aren't found and dispatch fails with
  `undef`.
- **`whereis(SomeAggregate)` is always `undefined`** for evoq
  aggregates/projections started via `gen_server:start_link(?MODULE, ...)`
  with no registered name. Don't read "the process is dead" into it — it
  was never named. (Cost a whole wrong "keeper" fix once.)

---

## Common Test Fixtures

### Unique IDs to Avoid Pollution

```erlang
unique_id() ->
    <<"test-", (integer_to_binary(erlang:system_time(microsecond)))/binary>>.
```

### Waiting for Async Operations

```erlang
%% Give async processes time to work
timer:sleep(200),

%% Or poll with timeout
wait_for(Fun, Timeout) ->
    wait_for(Fun, Timeout, 50).

wait_for(Fun, Timeout, _Interval) when Timeout =< 0 ->
    Fun();  % Final attempt
wait_for(Fun, Timeout, Interval) ->
    case Fun() of
        {ok, _} = Result -> Result;
        _ ->
            timer:sleep(Interval),
            wait_for(Fun, Timeout - Interval, Interval)
    end.
```

---

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Correct Approach |
|--------------|----------------|------------------|
| Push without tests | Bugs reach prod | `rebar3 eunit` before push |
| Test implementation | Brittle tests | Test behavior/contracts |
| Shared test state | Flaky tests | Unique IDs per test |
| No async wait | Race conditions | `timer:sleep` or polling |
| Killing registered processes | Affects other tests | Don't cleanup registered |

---

## Running Tests in CI

The CI workflow runs:

```yaml
- name: Run tests
  run: rebar3 eunit
```

All tests must pass before the Docker image is built.

### A path a test compares against a tool's answer is taken resolved

When a test builds a fixture path from a temporary root and then compares it with a path a tool answered — `git worktree list`, `git rev-parse --show-toplevel`, a file walker — take the root's real path where it is made (`realpathSync(mkdtempSync(...))`, `pwd -P`, the language's equivalent), and build every expectation in the file from that. Tools answer with the place they resolved; a temporary root reached through a link is therefore a different spelling of the same place.

**Why:** one CI job runs the whole suite under a temporary root reached through a link, deliberately. A test whose fixture root was not resolved compared `…/_temp/private/var/…` (the tool's answer) with `…/_temp/var/…` (its own) and failed there alone. The same suite was green locally, so it read as a load flake. Prove a fix for it under the same condition the CI creates — a symlink in the temp root's path, red on the old bytes and green on the new — rather than by re-running until it passes.

### "It passes when run alone" is a claim about a run that was actually scoped

A filter handed to a package's test entry point may not reach the runner: arguments are appended to a chain of commands, and a runner that does not understand the flag runs everything anyway. Check the scope before quoting it — a run that reports the whole suite's test count was not the one-file run the claim needs.

---

## Running the suite by hand

A suite is bounded by what its own entry point states. A hand-run invocation is bounded by nothing unless it repeats every one of those statements, so the rules below apply to any run started outside the entry point.

### Build a runner's arguments in bash, not in the interactive shell

Assemble a test runner's flags and file list in a bash script with `set -euo pipefail`, and print the final argument list before anything runs (the rule against an empty argument list is in `SHELL.md`). An interactive shell's array syntax is not portable between shells: a shell without `mapfile` leaves the array empty without an error, and the loop after it passes nothing.

**Why:** an empty pattern once turned a one-file run into a sweep of every test file the search could reach, including other checkouts on the same machine, with the cases that start real processes live.

### A test run that can start real work runs in its own process namespace

A suite whose cases start real processes, servers or recorded hosts runs inside `unshare --user --pid --fork --mount-proc`, with a temporary directory of its own. Anything whose tear-down signals a process group by bare pid is confined the same way.

Inside the namespace the run is not the user it was: a private home leaves a version manager's shims with no version to pick, and the checkout belongs to another user, so version control refuses it as unsafe. Put the real runtime's directory first on the path, and mark the checkout safe for that run only, through the environment rather than a config file.

**Why:** a tear-down that signals by pid can reach a process it never started, and the broad sweep above is exactly the run that puts unrelated processes within reach.

### A killed run takes its children with it

A runner that starts a child per test file ties that child's life to nothing. A runner killed from outside leaves each child reparented and running, holding every descriptor and credential it inherited. Every documented way to run the suite states a timeout, a force-exit, and a guard that ends the file's process once the process that started it is gone. Run the suite through the project's entry point; a hand-run command carries all three or it does not run.

**Why:** five such orphans were found alive hours after their runners died, one of them holding a live session credential, and the person who owned it could not start a new session until the orphans were killed by hand. The flags bound a run that is allowed to finish; they do nothing for a run killed outright.

---

## Decision Record

| Date | Decision |
|------|----------|
| 2026-02-08 | Tests required before push |
| 2026-02-08 | Use `{module}_tests.erl` naming for auto-discovery |
| 2026-02-08 | pg tests use scope `pg` (OTP default) |
| 2026-02-08 | Use unique IDs to avoid test pollution |
| 2026-05-31 | CMD/aggregate tests use `evoq_testkit` (Layer A pure + Layer B mem-evoq persistence); always assert `assert_valid_stream_id/1` |
