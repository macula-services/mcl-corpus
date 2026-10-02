---
title: The Macula tier model
layer: philosophy
audience: [agent, human]
stage: stable
---

# The Macula tier model

The cut between the **user surface** and the **always-on realm services**.
A user reaches the mesh through one of four channels: the terminal, a
coding agent (`macula-mcp`), an "operator website" hosted by an edge
service, or a mobile app / classic public website. The identity/auth
design for the four channels is in [AUTH_MODEL.md](AUTH_MODEL.md).

This document is shaping material. Future Claude sessions, future
contributors, and grant-reviewer audiences should be able to read it
in five minutes and answer "where does X belong?" without asking
anyone.

---

## The tiers

```
Layer 2 — services    macula-services/mcl-{om, rag, git, …}
                      Always-on, multi-tenant, realm-bound, each with
                      its own SERVICE-PRINCIPAL identity.
                      EDGE-FIRST: hosted wherever the operator puts
                      them (BEAM cluster, relay box, lab machine,
                      laptop, Cerbo) and DIALLING OUT to a station.

Layer 1 — identity    macula-realm
                      Issues human realm-membership certs AND service
                      principal certs.

Layer 0 — kernel      macula-station
                      QUIC peering, DHT, SWIM liveness, routing.
                      Realm-agnostic. One per node, every node.
```

Every node runs Layer 0 (`macula-station`). Layer 1 (`macula-realm`)
runs where the realm's stewards put it. Layer 2 services dial out to a
station from wherever they are hosted.

**The cut is lifecycle and identity, never hardware.** What makes
something Layer 2 is that it runs without a logged-in user and answers
as itself with its own service-principal credential. The box under it
is not part of the definition, because a Layer-2 service needs no
inbound port and no public address: it dials out over QUIC and the
station does the peering, the DHT and the routing. That is what lets a
service behind a domestic NAT be reachable by every other service in
the realm.

## Cut criteria

When deciding where a new capability belongs, walk the list:

**Service (Layer 2)** if **any** of:

- Runs always-on without a logged-in user
- Heavy resource shape (>200 MB RAM resident, GPU, big disk)
- Multi-tenant (serves multiple humans on the same box)
- Maps to one of the four workload classes
- Holds shared mutable state that survives sessions
- Has its own external dependency (API keys, model weights, …)
- Translates an external data source (vendor MQTT, file watcher,
  smart-meter readout, IoT gateway, …) into mesh facts. These
  **ingestion adapters** are L2 by default — never session sidecars or
  per-user plugins. See "Offline operation via reckon-db" below.

**Client surface (one of the four channels)** if **all** of:

- User-facing UI surface, or a per-session event handler
- Per-session state only
- Cheap (kilobytes of memory, no heavy I/O)
- Coordinates rather than computes (calls Layer-2 services for
  the actual work)

If you can't decide, default to Layer 2 (be paranoid about the
grab-bag). It's easier to merge a small service into a bigger one
later than to extract a heavy plugin under load.

### Format contracts belong in the protocol layer

The above criteria cut by *capability*. Cut criteria also exist for
*types* and *formats*: identifier shapes, envelope layouts, snapshot
serialization, subscription protocol, anything with a regex or schema
contract. These belong in the **protocol layer** (`reckon-gater`), not
the implementation layer (`reckon-db`).

The reason: an adapter that doesn't run the storage backend (e.g.
`reckon-evoq`) needs to validate ids without dragging the storage
backend in as a dep. A gateway client (e.g. `reckon-lazy`, or any future
write-only sender) needs to mint ids without depending on the storage.
Both are wrong if the format definition lives in the storage layer.

**Symptom of getting this wrong:** an upstream type module imports a
downstream storage module to do basic shape checks. If you see
`reckon_db_*` referenced from `reckon_evoq_*`'s code, the cut is in the
wrong place — the type moved out of layer.

**Worked example:** the user-stream-id regex
`^[a-z]{1,32}-[a-f0-9]{32}$` and its `validate/1` + `new/1` helpers
lived in `reckon_db_stream_id` (inside the storage backend). Anyone
wanting to validate or mint stream ids without running reckon-db
couldn't. Relocated to `reckon_gater_stream_id` in reckon-gater 2.2.0;
`reckon-db` 3.0.0 calls into it. Both storage and the adapter (and any
future client) now reach the same module without coupling to a specific
implementation.

## The contract

Every Layer-2 service:

1. Lives at `github.com/macula-services/mcl-<name>`
2. Implements the `mcl_om_service` behaviour (six callbacks:
   `info/0`, `start/1`, `stop/1`, `health/0`, `capabilities/0`,
   `identity_spec/0`)
3. Ships as an OCI container to `ghcr.io/macula-services/mcl-<name>`
4. Declares a Quadlet unit in `quadlet/` for system-wide
   systemd-managed Podman
5. Carries a `manifest.json` with `tenancy: realm`,
   `runs_on: infrastructure_node`, and the advertised capability list
6. Receives a realm-signed service-principal credential at install
   time, mounted at `/etc/mcl/secrets/service-cert.pem`
7. Connects to the local `macula-station` and advertises every
   capability via `macula:advertise/5`
8. Exposes `/health` on loopback (port 8470) for Podman's
   HEALTHCHECK; no externally-routable ports

The substrate library [`mcl-om`](https://github.com/macula-services/mcl-om)
provides 1, 7, and 8 for free. Services just implement the
behaviour and wire their `_mesh_rpc.erl` dispatch table.

## Offline operation via reckon-db

Layer-2 services are not assumed to be online all the time. The
mesh has connectivity gaps (relay restarts, fleet bounces, network
partitions, intermittent ISPs, sites that come online only when a
ship enters port). A service whose ingest path blocks on mesh
reachability is brittle.

The canonical pattern: **every L2 service that ingests external
data owns a reckon-db store**. Inbound data becomes a command →
domain event → local stream. A separate emitter slice drains the
stream to the mesh asynchronously, retrying forever. The ingest
path never observes mesh state.

```
external source ──► subscriber slice ──► command
                                            │
                                            ▼
                                  reckon-db (local stream)
                                            │
                                ┌───────────┴────────────┐
                                ▼                        ▼
                       on_event_to_mesh         other projections /
                       (emitter, async,         process managers
                        drains when station
                        is mesh-reachable)
                                │
                                ▼
                        macula:publish/4
```

The substrate already supports this directly. `mcl_om_service`
declares two optional callbacks:

```erlang
-callback store_id() -> atom().     %% the service's reckon-db store id
-callback data_dir() -> string().   %% on-disk root for the store
```

When both are exported, `mcl_om:boot/1` starts a `single`-mode
reckon-db store at `<data_dir>/<store_id>/` and an evoq subscription
**before** the service's own `start/1` fires. Producer-only services
(no event store) omit both callbacks and pay nothing.

**Consequences:**

- Boat goes offline two weeks → events accumulate locally → station
  reaches marina wifi → emitter drains backlog → realm subscribers
  catch up. Same code, no special branch.
- Restarting the service replays from the reckon-db stream. No data
  loss across restarts, container migrations, or host moves.
- Naive buffering / `try ... catch macula:publish` retries in handler
  code are an **antipattern**. The store IS the buffer.
- Ingestion adapters (Cut criteria item above) should ship with
  these callbacks declared from v0.1, not v0.2.

## Identity model

Services are **institutions** of the realm, not user-bound. Each
has its own keypair and a realm-signed credential. The metaphor:

> Citizens of a town carry citizen IDs. The town's library, post
> office, and water utility carry institutional badges — same
> issuer (the town clerk), narrower scope. The library doesn't
> borrow Alice's citizen ID to lend her a book.

In Macula terms:

- **Citizens** (humans, via whichever of the four channels in
  [AUTH_MODEL.md](AUTH_MODEL.md) they're using) carry
  realm-membership certs.
- **Institutions** (macula-services/*) carry service-principal
  certs, also signed by the realm, but with narrower `actions`
  and `resources`.
- A user logging out doesn't take services with them. Services
  outlive sessions.

v1 implementation: long-lived service-principal certs provisioned
by a realm-admin script. v2 (when policy + UCAN delegation land):
short-lived UCANs auto-rotated against a `macula-realm` HTTP
endpoint. The swap-in lives entirely behind `mcl_om_identity`;
consumers don't notice.

See `mcl-om/guides/identity_model.md` for the full
town/library walkthrough and the v1 / v2 trigger.

## Anti-patterns

Three things this model explicitly forbids:

1. **No user-bound services.** A `mcl-rag` that exists "for
   Alice", starts when Alice logs in and answers with Alice's
   citizen cert is wrong. The fault is the binding, not the box.
   That same service on that same laptop, running under a
   lingering unit with its own service-principal credential and
   serving whoever the realm says may reach it, is correct. Fix
   the binding first; relocate the workload only if the box
   genuinely cannot carry it.
2. **No anonymity / self-rooted leaves.** Every service principal
   chains to a realm root. No Pubky-style ungoverned identities.
   (See `memory/feedback_no_anonymity_only_sovereignty`.)
3. **No "central" anything across services.** Each Layer-2
   service supervises its own state. There is no shared service
   bus, no central registry, no horizontal layer of "service
   plumbing". The realm coordinates through Macula RPC, not a
   service framework.
4. **No bridging L2-shaped work through a session-tier HTTP API.**
   An L2 service uses the Macula SDK directly against its local
   `macula-station` — no HTTP middleman, no per-user session
   dependency, correct identity. See
   `skills/antipatterns/integration.md` Demon 50.

## Placement rules

Where a Layer-2 service is hosted is an operational decision, and the
answer is frequently user-owned hardware. An ingestion adapter has to
live where the thing it ingests is. A service that represents its
operator to the rest of the realm is correctly hosted by that operator,
on their laptop, and being hosted there is the entire point of it. None
of this is an exception to anything.

Four conditions hold wherever a Layer-2 service runs, and **all** of
them are about identity and lifecycle rather than hardware:

1. The service has its own **service-principal credential**, not
   borrowed from the user's citizen cert. Even a household realm
   of one issues a separate badge for the service.
2. The service is **not user-session-keyed.** It runs whenever the
   host is up, not "when the user is logged in". `systemd --user`
   with linger-enabled, a Quadlet under root, or a Venus-OS runit
   slot all qualify; "starts when I open my laptop" does not.
3. The service principal still **chains to a realm root** — no
   self-rooted leaves, anywhere. The realm may be small (one
   household, one boat); it must exist.
4. The manifest **records the placement**, so an operator who
   inherits the service knows whether it is deliberate.
   `deployment: lone` (or operational equivalent) marks the case
   that should migrate onto shared realm infrastructure once a
   cooperative node exists.

The judgement that remains is about **who the service serves**, not
about whose machine it is on. A capability the realm offers its members
(the shared RAG, the shared LLM, DNS) belongs on a node the stewards
keep up, because its availability is a promise made to other people and
a laptop lid is not a promise. A service that serves its own operator,
or that speaks for its operator to others, belongs with that operator.
A shared service parked on a member's machine because nothing else
exists yet is the lone phase of a future cooperative, and condition 4
is how you remember to move it.

Availability is the real variable, and it is worth being honest that
it is bought rather than decreed. A service on a lingering unit on a
box that stays up is more available than one on a laptop that closes at
night. Where that matters, either put it somewhere that stays up or
design the protocol so the offline case degrades into something
useful.

## How callers reach services

A caller — a terminal, a coding agent, an operator website, a mobile
app — reaches a Layer-2 service via Macula RPC:

```erlang
%% Unary
{ok, Result} = macula:call(
    LocalPool, Realm,
    <<"mcl-rag.answer_query">>,
    #{query => Q, top_k => 5},
    Timeout
).

%% Streaming
{ok, Stream} = macula:call_stream(
    LocalPool, Realm,
    <<"mcl-llm.stream_chat">>,
    #{model => Model, messages => Msgs},
    #{}
).
```

The local `macula-station` routes the call to wherever the service is
running, which the caller neither knows nor needs to. No HTTP, no DNS
lookup, no API keys in the caller. The service answers as itself with its
own credential; the realm verifies both sides.

## Naming

| Prefix | Means | Examples |
|--------|-------|----------|
| `macula-` | Realm-agnostic infrastructure (Layer 0–1) | `macula-station`, `macula-realm`, `macula-rag` (federation protocol — uses SDK), `macula-mcp` |
| `mcl-` | Realm-aware service (Layer 2) | `mcl-om`, `mcl-rag`, `mcl-git`, `mcl-search`, `mcl-dns`, `mcl-llm`, … |

The `macula-X` prefix means *"depends on the Macula SDK"*, not
*"runs inside macula-station"*. `macula-rag` (the federation
library) runs in Layer 2 service consumers as a dep, alongside
`mcl-rag` itself.

## What lives in `macula-services/`

| Repo | Role |
|------|------|
| `mcl-om` | Substrate library — `mcl_om_service` behaviour, identity loader, capability advertiser, `/health` handler, container + Quadlet templates |
| `mcl-rag` | Retrieval-augmented generation over the realm's corpora |
| `mcl-dns` | DNS-over-mesh name resolution |
| `mcl-git` | Git-over-mesh repository server (companion to `git-remote-mesh`) |
| `mcl-llm` | LLM gateway (Anthropic / OpenAI / Google / Ollama) |

Future watchlist (not yet built):
- `mcl-blob` — content-addressed blob store
- `mcl-cron` — scheduled task runner
- `mcl-runner` — CI / build runner
- `mcl-faber` — federated neuroevolution
- `mcl-tools` — agent tool surfaces (web_fetch, web_search,
  synthesize_speech, transcribe_audio, …) — the bits split out of
  `mcl-llm`'s extract
- `mcl-victron` — Victron Venus OS ingestion adapter
  (dbus-flashmq MQTT → mesh facts; reckon-db offline-first)
- `mcl-openems` — OpenEMS Edge ingestion adapter
  (JSON-RPC over WS → mesh facts; reckon-db offline-first)
- `mcl-shelly` — Shelly Pro local-MQTT ingestion adapter

## Reading order for a new contributor

1. This file — overall shape
2. `mcl-om/README.md` — the substrate
3. `mcl-om/guides/service_anatomy.md` — what every service looks like
4. `mcl-om/guides/identity_model.md` — town / library metaphor + v1/v2
5. `mcl-om/guides/container_deployment.md` — how a service lands on a node
6. Pick one shipped service (`mcl-rag` is the most fleshed-out)
   and read it end-to-end

Memory reference for context:
- `[[feedback_stations_route_daemons_publish]]` — why Layer 0 is
  realm-agnostic
