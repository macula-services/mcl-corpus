---
title: "FAQ: Calling Event Sourcing from a Non-BEAM App via reckon-gateway"
layer: guide
audience: [agent, human]
stage: stable
---

# FAQ: How Do I Call Event Sourcing from a Non-BEAM App?

[Back to FAQ index](FAQ.md) · [Back to corpus index](../INDEX.md)

[FAQ: How do I add event sourcing to a new mcl-* service?](FAQ_ADD_EVENT_SOURCING.md)
covers the in-process BEAM path (evoq + reckon-db). This page is the
equivalent for a caller that isn't on the BEAM at all: `reckon-gateway`
exposes ReckonDB's event-store API over gRPC and plain HTTP/JSON.

**A language-set mismatch worth stating up front**: the per-language
pages below cover Go/Rust/C#+F#/PHP to match the language split used for
the mesh SDK FAQs
([Go](FAQ_DEVELOP_EDGE_SERVICES_GO.md)/[Rust](FAQ_DEVELOP_EDGE_SERVICES_RUST.md)/
[.NET](FAQ_DEVELOP_EDGE_SERVICES_DOTNET.md)/[PHP](FAQ_DEVELOP_EDGE_SERVICES_PHP.md)).
`reckon-gateway`'s own real polyglot client set is actually
**Go/.NET/Rust/Python** — dedicated client packages exist today only for
Go and .NET; Python has one too but isn't covered here. There is **no
dedicated Rust or PHP package anywhere in this workspace** — Rust is
covered via the standard (but unverified-in-this-workspace) raw gRPC
codegen path, and PHP has zero prior art at all and is written as an
explicitly unverified draft, same honesty register as
[FAQ: Connecting Blazor to the Mesh](FAQ_CONNECT_BLAZOR.md).

---

## The shared contract: reckon-proto + reckon-gateway

`reckon-proto` (current version **0.8.0**) is the wire contract:
`StreamService` (`AppendEvents`/`ReadStreamForward`/`ReadStreamBackward`/etc.)
and `DcbService` (`AppendIfNoTagMatches`/`ReadDcbContext`, the
Dynamic-Consistency-Boundary primitives) are both real. `AppendEvents`
takes `{store_id, stream_id, expected_version, events}` and returns
`{version, position, count}`; expected-version sentinels are
`NO_STREAM=-1`, `ANY_VERSION=-2`, `STREAM_EXISTS=-4`. DCB's
`AppendIfNoTagMatchesRequest` takes a `TagFilter` (`oneof`:
`match_any`/`match_all`/`conjunction`/`disjunction`/`event_type_match`)
plus a `seq_cutoff` (the highest seq the caller observed; `-1` if
nothing) and returns a `oneof { Committed | Conflict }` — **the conflict
case is a structured response, not a gRPC error.**

`reckon-gateway`'s real current version is **`v0.27.0`** (git tag) — its
own README still pins `0.17.1` in several places, so trust the git tag
(and the `ghcr.io` tag list, which goes up to `0.27.0`), not the README
prose, if you need a specific number.

```bash
podman run -d --name reckon-gw -p 50051:50051 -p 8080:8080 \
  -v reckon-data:/data \
  -e RECKON_GATEWAY_STORE_ENABLED=true \
  -e RECKON_GATEWAY_STORE_ID=my_store \
  -e RECKON_GATEWAY_LOCAL_CLUSTER_ID=local \
  -e RECKON_GATEWAY_DIST_HIDDEN_FLAG=-hidden \
  ghcr.io/reckon-db-org/reckon-gateway:0.27.0
```

`50051` is gRPC, `8080` serves REST + a browser admin UI at `/admin` +
live event stream over SSE. **No protobuf needed at all** for simple
cases — the REST alternative is a real, documented curl round trip:

```bash
curl -sX POST localhost:8080/v1/stores/my_store/streams/user-7c4b9/events \
  -H 'content-type: application/json' \
  -d '{"expected_version":"any","events":[{"event_type":"user_registered_v1","data":{"name":"Alice"}}]}'
# → {"version":0,"count":1}

curl -s "localhost:8080/v1/stores/my_store/streams/user-7c4b9/events?from=0&limit=100"
```

## Worked examples, one per language

- [Go](FAQ_CALL_RECKON_GATEWAY_GO.md) — verified against a real example
- [C# / F# (.NET)](FAQ_CALL_RECKON_GATEWAY_DOTNET.md) — verified against a real example (C#-only, no F# examples exist for this client)
- [Rust](FAQ_CALL_RECKON_GATEWAY_RUST.md) — real protocol, but no working example anywhere in this workspace
- [PHP](FAQ_CALL_RECKON_GATEWAY_PHP.md) — zero prior art, draft only

## Sanity-checking your connection

`reckon-lazy` (`lazyreckon` binary) is a real terminal UI for browsing a
running gateway's stores/streams/subscriptions/snapshots —
`lazyreckon --endpoint host:port`. Useful the same way
`macula-mcp-doctor` is for the mesh side: confirm the gateway is actually
reachable and has the data you expect before debugging your own client
code.

## See also

- [FAQ: How do I add event sourcing to a new mcl-* service?](FAQ_ADD_EVENT_SOURCING.md) — the in-process BEAM/evoq side this gRPC path is an alternative to
