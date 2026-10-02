# Side Effects Must Follow Facts, Not Hopes

*An architectural pattern for client-service communication.*

## The Principle

> **Any client (operator website, mobile app, terminal, coding agent) is an external system. Side effects (UI updates, state transitions, user feedback) must be driven by received FACTS (events materialized into read models), never by command acknowledgments.**

A command sent to an event-sourced `mcl-*` service is a **HOPE** -- "I hope you'll do this." The response (an HTTP reply, or a mesh call's reply) means "I received your hope and it looks valid." It does NOT mean the intent succeeded. Only the resulting **event** (fact), materialized into a read model by a projection, confirms that.

This principle applies universally:
- an operator website or mobile app sending commands over HTTP
- a terminal (`macula-cli`) calling mesh procedures
- a coding agent (`macula-mcp`) calling `mcl-*` procedures over the mesh
- any future client

## The Anti-Pattern

```
Client                           Service
──────                           ───────
POST /vision/refine  ──────→    receive hope
                                process command
                                store event (maybe)
← 200 OK  ←───────────────     "received"
update UI  ← WRONG!            side effect based on hope
```

What can go wrong between "received" and "event stored":
- Aggregate rejects the command (business rule violation)
- Event store write fails (disk full, replication error)
- Process crashes between accept and store
- Command is queued for async processing

The client updated its UI based on a **hope acknowledgment**, not a **fact**.

## The Correct Pattern: Read Model as Source of Truth

The service owns the truth. Events flow through projections into SQLite read models. Clients read from those read models to determine current state.

### HTTP clients (operator website, mobile app)

```
Client                          Service
────────                        ───────
POST /vision/refine  ──────→    receive hope
← 202 Accepted  ←─────────     "hope received"
                                process command
                                vision_refined_v1 stored
                                projection updates SQLite

GET /query/visions/{id}  ──→    read from SQLite
← 200 OK + updated state ←     FACT confirmed
update UI                       side effect based on FACT
```

The client:
1. Sends the command (HOPE)
2. Receives 202 Accepted -- meaning "received, processing"
3. Polls the read model for updated state (or subscribes via WebSocket in the future)
4. The projection has materialized the event into SQLite
5. Client fetches the updated read model and updates UI based on FACT

### Coding agents (macula-mcp)

```
Agent (macula-mcp)               Service
──────────────────               ───────
mesh_call submit_move  ──────→   receive hope
← reply (ok / refusal)  ←────    "hope received"
                                 command processed
                                 move_played_v1 stored
                                 projection updates SQLite

mesh_call get_game_v1  ──────→   read from read model
← state with the move  ←────    FACT confirmed
act on it                        side effect based on FACT
```

An agent's `mesh_call` reply is the hope acknowledgment, exactly like a
202 — the responder answered before any projection ran. The agent acts
on the *query* that returns the materialized fact (or on the
`move_played_v1` fact watched on the mesh), never on the call's own
reply.

### Terminal

The terminal can afford to wait synchronously: run the command, wait for
the projection to complete, query the read model, and only then print a
result. It never assumes success before the fact.

## Listener Architecture

### Service Side: Events Flow Through Established Channels

Events produced by command processing flow through the existing emitter infrastructure:

```
{event}_to_mesh.erl     -- external (WAN, across services)
```

Projections subscribe to events via evoq and update SQLite read models. These read models are the single source of truth for all client queries.

```
Command processed
    |
    v
Event stored in ReckonDB
    |
    +---> emit_{event}_to_mesh.erl  (publish to mesh for other services)
    +---> Projection                (update SQLite read model)
```

### Client Side: Read Models Are the Interface

Clients do not subscribe to raw events. Clients read from projections (SQLite read models) via query endpoints or query procedures.

| Client | Access Method | Pattern |
|--------|--------------|---------|
| Operator website / mobile app | HTTP (Cowboy handlers in desk directories) | Poll query endpoints |
| Terminal (`macula-cli`) | Mesh call | Synchronous request/response |
| Coding agent (`macula-mcp`) | Mesh call (`get_*_v1` procedures) or mesh_watch on facts | Query or fact-driven |
| Future | WebSocket | Push-based subscription |

The query endpoints are served by QRY department apps (e.g., `query_visions`, `query_ventures`). These read directly from the SQLite read models that projections maintain.

## Response Codes

Commands return **202 Accepted**, not 200 OK:

| Code | Meaning | Use |
|------|---------|-----|
| **200 OK** | "Here is your data" | Queries (GET) |
| **202 Accepted** | "Hope received, processing" | Commands (POST) |
| **400 Bad Request** | "Hope malformed" | Validation errors |
| **409 Conflict** | "Hope contradicts current state" | Business rule violations |

The distinction matters: 200 implies completion, 202 implies the work is still happening. On the mesh the same split is a reply's shape: a refusal (`{error, Reason}`) is the validation failure, an `ok` is the hope acknowledgment — never the fact.

## Transport

There is one live integration boundary. Clients live outside it.

| Boundary | Transport | Scope | Purpose |
|----------|-----------|-------|---------|
| **External** | `mesh` (Macula QUIC) | WAN | Cross-service fact publication |

Clients reach a service through its HTTP handlers (Cowboy, in desk directories) or its mesh procedures (`mcl-<svc>/<name>_v1`) — never through raw events. They read the results of the integrations above via query endpoints or query procedures backed by SQLite read models.

## Implementation Order

1. **Service:** Return 202 (or `{ok, …}` on the mesh) for all command endpoints
2. **Service:** Ensure projections update SQLite read models from events
3. **Service:** Ensure QRY apps expose query endpoints / `get_*_v1` procedures for read models
4. **Client:** Send commands, receive 202/ok, then poll query endpoints (or watch facts) for updated state
5. **Future:** Add WebSocket support for push-based read model updates

## Relationship to Other Patterns

- **HOPE/FACT vocabulary** -- from the Macula mesh protocol, applied universally to all client-service communication
- **Projections** -- client reads ARE reads from projections; SQLite read models are the interface between service truth and client display
- **Event sourcing** -- commands produce events, events update read models via projections, clients read from read models
- **CQRS** -- commands and queries are strictly separated; 202 for writes, 200 for reads
- **Vertical slicing** -- each division owns its projections and query endpoints; there is no central "client bridge" or "notification service"

