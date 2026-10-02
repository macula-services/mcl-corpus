---
title: "Example: Mesh-Fact Read Models"
layer: example
audience: [agent, human]
stage: stable
---

# Example: Mesh-Fact Read Models

*Canonical example: Listener → Policy → Projection for edge services with no aggregate*

> **Relationship to [MESH_INTEGRATION.md](MESH_INTEGRATION.md):** that example's FACTS-vs-EVENTS
> distinction still holds — a mesh fact is external truth, never a domain event. But its
> Correct Way flow (`FACT → LISTENER → COMMAND → AGGREGATE → DOMAIN EVENT → projected`)
> assumes the receiving side is a full Macula Division with an event-sourced aggregate to
> dispatch a command to. A `mcl-om`-based edge service (`macula-services/mcl-<name>`) is
> not that: no desks, no aggregate, no event store — just a mesh-fact listener maintaining a
> direct read model. That shorter shape still needs a Policy step, for a different reason:
> not command validation, but the admit/supersede/expire decision this example is about.

---

## The Pattern

```
Mesh FACT → LISTENER → POLICY (admit / supersede / expire) → PROJECTION (read-model write)
```

An edge service that builds a mesh-wide directory — "what stations exist," "what
capabilities are being served," any read model whose facts arrive from *other* processes
that can die without saying so — has two problems, not one:

1. **Discovery**: how does this service learn about an entity across a mesh with no
   central point that holds the whole record set.
2. **Staleness**: what happens to this service's own copy when the entity it describes
   goes away *ungracefully* — crash, power loss, network partition — with no explicit
   retraction.

A crawl-then-cache design solves neither at scale. A one-time `find_records_by_type`-style
crawl only sees what one queried peer locally holds — every DHT-backed system in this org
documents that explicitly, e.g. macula-station's own `_dht.find_records_by_type` handler:
*"Coverage is the relay's local view (own puts + replicated copies); cross-station
completeness requires querying multiple relays."* That's fine at ten records. It silently
returns an arbitrary slice at a hundred thousand. And a cache that never revisits what it
already ingested has no way to learn that an entity died without being told — which,
for anything that can crash, is the *common* case, not the edge case.

**The fix is one mechanism, reused for both problems: treat "republish" as a heartbeat.**
The source side already needs to periodically re-publish a live entity's own fact (a
`node_record`, a `procedure_advertisement`, whatever the fact type is) before its TTL
expires — that's how the fact itself stays alive in the DHT. Every one of those
re-publishes is *also* a fresh mesh-fact delivery to anything subscribed. A listener that
stays subscribed therefore hears from every live entity repeatedly, forever, for as long
as it's alive — including entities it never saw the original creation of. And an entity
that stops publishing (because it died) simply stops being heard from. Mirror the fact's
own `expires_at` into the read-model doc, and the read model inherits the exact same
self-healing property the DHT already has, instead of inventing a second, independent
liveness scheme.

---

## Wrong Way: Listener straight to Projection, crawl for completeness

This is real, shipped code — `macula-services/mcl-stations`, as of 2026-08-29, not a
hypothetical:

```erlang
%% ingest_node_records.erl — the Listener
try_connect({ok, Pool, _Realm}, State) ->
    {ok, NodeRecords} = macula:find_records_by_type(Pool, ?TYPE_NODE_RECORD),
    lists:foreach(fun ingest_node_record/1, NodeRecords),   % ❌ one relay's local view only
    {ok, _} = macula:subscribe_records(Pool, ?TYPE_NODE_RECORD,
                                       fun(R) -> Self ! {node_record, R} end),
    State#{pool => Pool}.

ingest_node_record(Record) ->
    verified_node_record(macula_record:verify(Record)).

verified_node_record({ok, Record}) ->
    Fields = macula_record:read_node_record(Record),
    station_read_model:upsert_node_record(Fields);   %% ❌ straight to projection
verified_node_record({error, _Reason}) ->
    ok.
```

```erlang
%% station_read_model.erl — the Projection
upsert_node_record(#{node_id := NodeId} = Fields) when is_binary(NodeId) ->
    Doc0 = existing_or_new(node_id_hex(NodeId), NodeId),
    Doc1 = Doc0#{<<"last_node_record_at">> => now_ms()},   %% written...
    Doc2 = maybe_put(Doc1, <<"hostname">>, maps:get(hostname, Fields)),
    %% ...
    put(Doc2).
```

`last_node_record_at` is written on every upsert and **never read anywhere** — no
staleness filter in the RPC handler that serves queries, no expiry sweep. There is no
Policy step between "verified fact arrived" and "write it," so there is nowhere the
admit/supersede/expire decision could live even if someone wanted to add it. A station
that dies ungracefully is served as live, forever, by this service — while the underlying
DHT record it was copied from correctly expires within about 48 hours on its own. The
persisted copy silently outlives the thing it is a copy of.

This antipattern:
- Treats "a fact arrived" as sufficient reason to write the read model
- Has no place to encode "is this fresher than what I already have"
- Has no place to encode "has this simply stopped being refreshed"
- Only ever removes an entry on an *explicit* signal (a tombstone), which never arrives
  for the failure mode that actually matters (crash, not graceful shutdown)

---

## Correct Way: Policy owns admit / supersede / expire

### Receiving Facts (Listener) — unchanged in shape, `mcl_om_pubsub` does this already

```erlang
%% my_x_service.erl
subscriptions() ->
    [{<<"_dht.records.1.stored">>, ingest_node_record_listener, []}].
```

```erlang
%% ingest_node_record_listener.erl — LISTENER
-module(ingest_node_record_listener).
-behaviour(macula_subscriber).
-export([init/1, handle_event/4]).

init(Args) -> {ok, Args}.

handle_event(_Topic, Record, _Meta, State) ->
    %% The listener's only job: verify transport-level authenticity,
    %% then hand off. It does not decide freshness — that's Policy's job.
    case macula_record:verify(Record) of
        {ok, Verified} -> on_node_record_maybe_admit:handle(Verified);
        {error, _}     -> ok
    end,
    {noreply, State}.
```

### Policy — the admit / supersede / expire decision, a pure function

```erlang
%% on_node_record_maybe_admit.erl — POLICY
%%
%% Naming convention: on_{source_fact}_{action}_{target}
-module(on_node_record_maybe_admit).
-export([handle/1, decide/2]).

handle(Record) ->
    Fields = macula_record:read_node_record(Record),
    ExpiresAt = macula_record:expires_at(Record),
    Existing = station_read_model:find(node_id_hex(maps:get(node_id, Fields))),
    case decide(Existing, ExpiresAt) of
        admit -> station_read_model:upsert_node_record(Fields, ExpiresAt);
        stale -> ok   % a delayed/out-of-order delivery of an older fact -- drop it
    end.

%% Pure decision function — no mesh call inside it, testable with plain terms.
%% This is the whole fix: give the "should this be written" question a home.
-spec decide(ExistingDoc :: map() | undefined, IncomingExpiresAt :: integer()) ->
    admit | stale.
decide(undefined, _IncomingExpiresAt) ->
    admit;                                             % never seen this entity before
decide(#{<<"expires_at">> := CurrentExpiresAt}, IncomingExpiresAt)
  when IncomingExpiresAt >= CurrentExpiresAt ->
    admit;                                             % a fresher republish (or first-ever)
decide(_Existing, _IncomingExpiresAt) ->
    stale.                                              % an older fact arriving late
```

### Projection — now genuinely dumb, and expiry-aware at read time

```erlang
%% station_read_model.erl — PROJECTION
upsert_node_record(Fields, ExpiresAt) ->
    Doc = existing_or_new(...),
    put(Doc#{<<"expires_at">> => ExpiresAt, ... }).

%% Filter at READ time — correctness holds even with zero background sweep,
%% since a dead entity's mirrored expires_at simply ages past `now()`.
fold(Fun, Acc) ->
    Now = now_ms(),
    fold_docs(fun(Doc, A) ->
        case maps:get(<<"expires_at">>, Doc, 0) > Now of
            true  -> Fun(Doc, A);
            false -> {ok, A}   %% expired -- skip, don't surface as live
        end
    end, Acc).
```

An optional periodic purge (matching the DHT's own ~1h reap cadence) bounds storage growth
too, but is not required for *correctness* — the read-time filter alone means a dead
entity stops being served the moment its mirrored `expires_at` passes, with no dependency
on a tombstone ever arriving.

**Key points:**
- Listener verifies transport authenticity only — it does not decide freshness
- Policy is a pure function (`decide/2`): no mesh call inside it, trivially unit-testable
  with plain terms, no live station needed
- Projection mirrors `expires_at` and filters by it at read time — self-healing against
  ungraceful death, no explicit tombstone required
- The *source* side's own periodic republish-before-TTL-expiry (already required for the
  fact to stay valid in the DHT at all) is what makes this work — nothing new needs
  building there, the read model just needs to stop ignoring `expires_at`

---

## Why this also answers "does discovery scale"

The crawl-based half of the Wrong Way example doesn't just risk staleness — the code that
serves it is explicit that it isn't mesh-wide complete in the first place. Coverage from
one relay is fine when the whole fleet fits in one relay's local replica set (true at ten
entities), and silently wrong once it doesn't (true at thousands). The reactive half —
`subscribe_records`/`mcl_om_pubsub` subscriptions — doesn't have that ceiling: every
live entity's own republish-before-TTL cycle delivers it to every listener still
subscribed, mesh-wide, via the same multi-hop pubsub relay every other fact already uses.
A listener that stays connected converges to complete coverage within one TTL cycle of the
fleet, with no crawl, no matter how large the fleet gets. Treat the initial
`find_records_by_type` crawl (if used at all) as a *warm-start optimization for faster
initial convergence*, never as the mechanism completeness depends on.

---

## What NOT To Do

| Antipattern | Why It's Wrong | Correct Approach |
|-------------|-----------------|-------------------|
| Fact → Projection directly | No home for the admit/supersede/expire decision | Fact → Listener → Policy → Projection |
| Treating a crawl as authoritative | One relay's local view, not mesh-wide, at any real scale | Crawl only as a warm-start; trust the subscription for completeness |
| Removing entries only on an explicit tombstone | Never fires for a crash, power loss, or partition — the common failure mode | Mirror `expires_at`; filter by it at read time |
| A background expiry sweep as the *only* staleness defense | Read-time filtering is strictly required for correctness between sweeps; a sweep alone leaves a stale window up to its own interval | Filter at read time; a sweep is an optional storage-bound optimization on top |
| A short live-republish cadence with a long/default TTL | Freshness improves, but failure-detection time doesn't — a dead entity's fact still survives up to the *TTL*, however often live entities refresh | Set an explicit `ttl_ms` proportioned to the republish cadence (e.g. TTL ≈ 3–4× the interval), the same discipline `macula_station_announcer` already applies (refresh at 75% of TTL) |

---

## Key Takeaways

1. **A mesh fact and a domain event are still different things** — this doesn't relax
   [MESH_INTEGRATION.md](MESH_INTEGRATION.md)'s FACTS-vs-EVENTS distinction, it applies it
   to a service with no event store to convert facts into commands for.
2. **Policy is where "should this be written" lives** — a Listener that hands facts
   straight to a Projection has nowhere to put that decision, which is exactly how a real
   staleness bug shipped.
3. **A republish is a heartbeat** — the same mechanism that keeps a DHT fact alive also
   delivers it to every subscriber again, which is what makes reactive listening converge
   to completeness without a mesh-wide crawl.
4. **Mirror the TTL, don't reinvent liveness** — `expires_at` already exists on the fact;
   copying it into the read model and filtering by it at read time is the whole fix.
5. **A short republish cadence needs a proportionally short TTL** — refreshing often
   doesn't bound failure-detection time by itself if the TTL wasn't shortened to match.

---

## Training Note

This example teaches:
- Why an edge service with no aggregate (a `mcl-om`-based `macula-services/mcl-<name>`
  service) still needs a Policy step between Listener and Projection, for a different
  reason than command validation: the admit/supersede/expire decision.
- Why a DHT-crawl-based discovery mechanism silently stops being complete at scale, and
  why a reactive mesh-fact subscription doesn't have that ceiling.
- Why "the source stopped saying it's alive" (TTL expiry) is a better liveness signal for
  a read model to depend on than "the source explicitly said it died" (a tombstone) —
  the latter never fires for the failure mode that matters most.
- The general shape: Listener (transport verification only) → Policy (pure decision
  function, no mesh call inside it) → Projection (dumb write + read-time expiry filter).

*Date: 2026-08-29*
*Origin: `macula-services/mcl-stations` staleness/scale investigation — a real,
verified gap in shipped code, not a hypothetical.*
