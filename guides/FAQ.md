---
title: "FAQ — Running and Building on the Macula Mesh"
layer: guide
audience: [agent, human]
stage: stable
---

# FAQ — Running and Building on the Macula Mesh

[Back to corpus index](../INDEX.md)

Practical "how do I..." answers, as opposed to the philosophy and
architecture doctrine that makes up most of this corpus. Every answer here
is a summary that links to the real, authoritative source (a repo's own
README, HOWTO, or source code) rather than a copy that can drift out of
sync with it — when in doubt, follow the link.

| Question | Answer |
|---|---|
| How do I join the Mesh — run my own station? | [`FAQ_JOIN_THE_MESH.md`](FAQ_JOIN_THE_MESH.md) |
| How do I join a realm and get my service an identity/certificate? | [`FAQ_JOIN_A_REALM.md`](FAQ_JOIN_A_REALM.md) |
| How do I authorize a procedure or topic with UCAN? | [`FAQ_AUTHORIZE_WITH_UCAN.md`](FAQ_AUTHORIZE_WITH_UCAN.md) |
| How do I run `macula-cli`? | [`FAQ_MACULA_CLI.md`](FAQ_MACULA_CLI.md) |
| How do I run `macula-mcp`? | [`FAQ_MACULA_MCP.md`](FAQ_MACULA_MCP.md) |
| How do I share content (files/blobs) over the mesh? | [`FAQ_SHARE_CONTENT.md`](FAQ_SHARE_CONTENT.md) |
| How do I run a local station for dev/testing? | [`FAQ_RUN_A_LOCAL_STATION.md`](FAQ_RUN_A_LOCAL_STATION.md) — ⚠ draft, no prior art exists yet |
| How do I debug a service that won't show up on the mesh, or gets `unknown_next_peer`? | [`FAQ_DEBUG_MESH_DISCOVERY.md`](FAQ_DEBUG_MESH_DISCOVERY.md) |
| How do I develop an edge service in Erlang, Elixir, or Gleam? | [`FAQ_DEVELOP_EDGE_SERVICES_BEAM.md`](FAQ_DEVELOP_EDGE_SERVICES_BEAM.md) |
| How do I develop an edge service in Go? | [`FAQ_DEVELOP_EDGE_SERVICES_GO.md`](FAQ_DEVELOP_EDGE_SERVICES_GO.md) |
| How do I develop an edge service in Rust? | [`FAQ_DEVELOP_EDGE_SERVICES_RUST.md`](FAQ_DEVELOP_EDGE_SERVICES_RUST.md) |
| How do I develop an edge service in C# or F# (.NET)? | [`FAQ_DEVELOP_EDGE_SERVICES_DOTNET.md`](FAQ_DEVELOP_EDGE_SERVICES_DOTNET.md) |
| How do I develop an edge service in PHP? | [`FAQ_DEVELOP_EDGE_SERVICES_PHP.md`](FAQ_DEVELOP_EDGE_SERVICES_PHP.md) |
| How do I add event sourcing (reckon-db + evoq) to a new mcl-* service? | [`FAQ_ADD_EVENT_SOURCING.md`](FAQ_ADD_EVENT_SOURCING.md) |
| How do I query a read model (QRY+PRJ)? | [`FAQ_QUERY_READ_MODELS.md`](FAQ_QUERY_READ_MODELS.md) |
| How do I wire a Process Manager for cross-domain integration? | [`FAQ_WIRE_A_PROCESS_MANAGER.md`](FAQ_WIRE_A_PROCESS_MANAGER.md) |
| How do I call event sourcing from a non-BEAM app (Go/Rust/C#+F#/PHP)? | [`FAQ_CALL_RECKON_GATEWAY.md`](FAQ_CALL_RECKON_GATEWAY.md) |
| How do I deploy my own mcl-* service to the fleet? | [`FAQ_DEPLOY_SERVICES.md`](FAQ_DEPLOY_SERVICES.md) |
| How do I build a mobile app for the mesh? | [`FAQ_BUILD_MOBILE_APPS.md`](FAQ_BUILD_MOBILE_APPS.md) |
| How do I connect a Phoenix LiveView site to the mesh? | [`FAQ_CONNECT_PHOENIX_LIVEVIEW.md`](FAQ_CONNECT_PHOENIX_LIVEVIEW.md) |
| How do I connect a Blazor site to the mesh? | [`FAQ_CONNECT_BLAZOR.md`](FAQ_CONNECT_BLAZOR.md) — ⚠ draft, no prior art exists yet |

## The shape of the whole stack, in order

If you're starting from zero: what you connect *to* (a station), who you
are once connected (a realm identity, and the UCAN tokens that gate
individual procedures), what you connect *with* (the CLI, or an MCP
server built on it), the mesh's own data primitives (content sharing),
how to develop and debug against it, what you write your own peer in
(any of eight languages across two families), how that peer keeps state
(event sourcing, read models, cross-domain process managers — reachable
from non-BEAM code too, via a separate gRPC gateway), and where it
actually runs once written. The client-shape FAQs at the bottom are
consumption patterns for specific client shapes — mobile, and two web UI
frameworks — layered on top of the SDKs above rather than a new stage of
the pipeline.

```
FAQ_JOIN_THE_MESH           — the station you connect to
       │
       ├── FAQ_JOIN_A_REALM          — identity/cert for your service
       │        └── FAQ_AUTHORIZE_WITH_UCAN  — gate a procedure/topic
       │
       ├── FAQ_MACULA_CLI            — the reference client
       │        └── FAQ_MACULA_MCP   — an MCP server built on the CLI
       │
       ├── FAQ_SHARE_CONTENT         — files/blobs, content-addressed
       ├── FAQ_RUN_A_LOCAL_STATION   — dev/test without the public fleet
       ├── FAQ_DEBUG_MESH_DISCOVERY  — unknown_next_peer and friends
       │
       └── FAQ_DEVELOP_EDGE_SERVICES_{BEAM,GO,RUST,DOTNET,PHP}  — write your own peer
                │
                ├── FAQ_ADD_EVENT_SOURCING     — CMD: command → aggregate → event
                │        └── FAQ_QUERY_READ_MODELS  — QRY+PRJ: projections + queries
                ├── FAQ_WIRE_A_PROCESS_MANAGER — react to another domain's event
                ├── FAQ_CALL_RECKON_GATEWAY    — same event store, no BEAM required
                │
                ├── FAQ_DEPLOY_SERVICES         — ship it
                │
                └── client-shape patterns, all built on the SDKs above:
                      FAQ_BUILD_MOBILE_APPS            — Android/iOS via macula-rust's UniFFI
                      FAQ_CONNECT_PHOENIX_LIVEVIEW      — real prior art, Erlang/Elixir SDK
                      FAQ_CONNECT_BLAZOR                — no prior art, reasoned from macula-dotnet
```

Railroad terms used throughout, if unfamiliar: `macula` SDK = the
**track** (QUIC/HTTP-3 transport), `macula-station` = the **station**
(DHT/SWIM/routing), `macula-realm` = the **train company** (identity and
certs), a mcl-* service = a **passenger** (outbound-only,
connects out, never accepts inbound connections directly). See
[`GLOSSARY.md`](../GLOSSARY.md) for the full canonical vocabulary.
