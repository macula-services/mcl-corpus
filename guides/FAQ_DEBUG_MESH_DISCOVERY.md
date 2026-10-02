---
title: "FAQ: Debugging Mesh Discovery and unknown_next_peer"
layer: guide
audience: [agent, human]
stage: stable
---

# FAQ: How Do I Debug a Service That Won't Show Up in Mesh Discovery, or Gets `unknown_next_peer`?

[Back to FAQ index](FAQ.md) · [Back to corpus index](../INDEX.md)

Several existing FAQs mention pieces of this individually — the
advertise-gossip propagation lag noted in
[FAQ: How do I run macula-cli?](FAQ_MACULA_CLI.md)'s worked example, the
demo fleet's short `station_endpoint` DHT TTL noted in the leaf-client
SDK FAQs, `mcl_om`'s periodic re-advertisement noted in
[FAQ: Developing Edge Services in BEAM Languages](FAQ_DEVELOP_EDGE_SERVICES_BEAM.md).
This page consolidates them into one troubleshooting reference.

---

## 1. Read the actual error, not just "it failed"

`macula-cli`'s own [`guides/HOWTO.md`](https://github.com/macula-io/macula-cli/blob/master/guides/HOWTO.md)
§10 has the real BOLT#4 error table:

| Name | What it means | What to check |
|---|---|---|
| `unknown_next_peer` | Nobody's advertised this procedure anywhere the station's routing table knows about | Is the provider actually running, and did it `Advertise` *before* you called? Right `--realm`? |
| `temporary_relay_failure` | A relay hop hit a transient problem | Retryable — try again; if it persists, `stream probe` between the same two stations to see if it reproduces |
| `target_realm_refused` | Target station doesn't serve the realm you asked for | Double-check `--realm`'s hex against what the provider actually advertised under |
| `unauthorized` | A UCAN capability check failed on a gated procedure | Mint a token covering what the procedure requires — see [FAQ: How do I authorize a procedure or topic with UCAN?](FAQ_AUTHORIZE_WITH_UCAN.md) |

**Retry semantics differ by error**, per `macula`'s
`docs/guides/rpc/RPC_PROTOCOL.md` (backed by `macula_bolt4.erl`'s real
code/retry map): `unknown_next_peer` (`0x01`) means retry a **different
path**, not the same one again; `temporary_relay_failure` (`0x02`) means
retry the *same* path after a backoff; `node_not_found_at_target_relay`
(`0x04`) means re-resolve and recompute the path. Retrying
`unknown_next_peer` against the same station/path repeatedly is retrying
the wrong axis.

## 2. Advertisement timing is real and bounded, not instant

`mcl_om_capabilities` (macula-services/mcl-om) republishes every
**30 seconds ± up to 3 seconds jitter**, with a TTL of **4× that interval
= 2 minutes**. Concretely: a freshly-booted `mcl_om_service` can take
up to ~33s for its *first* advertisement to land somewhere a caller can
see it, and a service that crashed or was stopped without a clean
unadvertise naturally disappears from discovery within 2 minutes, not
instantly. If you just started (or just killed) something, that window
alone can explain a transient `unknown_next_peer`.

## 3. Ordinary advertise/call depends on gossip having already propagated — direct-dial doesn't

`macula-go`'s own README states this plainly: ordinary `Advertise`/`Call`
"depend on inter-station routing gossip having already propagated a
route... on a large or freshly-changed mesh, that isn't always true yet."
`macula-rust`'s README makes the same point in its own words ("reaches a
service without depending on advertise-gossip having propagated a
route") — same root cause, independently worded, not a shared quote.
**Direct-dial is the real fix for this class of problem, not a
sleep-and-retry loop**: `macula_direct_dial` (Erlang — `call/5,6`,
`call_stream/5,6`), Go's `directdial` package (`Resolve`/`Call`),
`direct_dial::{resolve,call}` (Rust), `.NET`'s `Dht.DirectDial`, and
PHP's `getDirect`/`putDirect` equivalents all resolve the provider's own
signed DHT record and dial it directly in one hop — reaching the
provider "regardless of whether ordinary gossip ever reached the
caller's own station." Reach for this when you know the provider's
identity/address and gossip lag is the actual problem, rather than
working around it with waits.

(A `time.Sleep(500ms)` "settle wait" after `Advertise` and before calling
back exists in `macula-go`'s own live test suite — but it's not
documented anywhere as general guidance, just an internal test-timing
detail. Don't treat it as a recommended pattern; direct-dial is the real
answer for production code.)

## 4. Confirm what's actually advertised right now

```bash
macula-cli dht find-records-by-type station-de-frankfurt.macula.io:4433 procedure_advertisement
```

The realm is embedded in each record's own `procedure_uri`, not a
separate flag — you don't need to already know the realm to find this.
Every record's signature is checked and reported (`verified`/
`verify_error`). This is the ground truth for "is my thing actually
advertised right now," independent of any specific caller's ability to
route to it.

**Even this can come back empty for something that genuinely is
advertised** — `macula-station`'s own `docs/DHT_FIND_FLAKE_ATTEMPT.md`
documents that cross-station DHT find historically flaked at roughly
**60%** on a fully-converged 9-station mesh. A real fix
(`macula_station_dht_dialer` + a multi-round walk) shipped and improved
this substantially, but the doc says outright it is "not 100%... still
probabilistic." If `find-records-by-type` comes back empty for something
you're confident is running and advertised, that can be real, documented,
still-current fleet behavior — retry, or use direct-dial to sidestep
DHT-find flakiness entirely, rather than assuming your service is
broken.

## 5. A scary-looking log line that's deliberately suppressed by default

`macula-station`'s `docs/PUBSUB_RESIGN_LOOP_LESSON.md` documents
`[peer_observer] pubsub frame verify failed: signature_invalid` during
cross-station pubsub as deliberate loop prevention, not a signature bug.
**You won't actually see it today** — a logger filter
(`macula_station_log_filters.erl`) ships specifically to suppress this
exact warning, and the doc reports zero occurrences across all 9 fleet
stations' full container lifetime since. Mentioned here in case you've
disabled the default log filter, or dig through debug-level logs and
find it: it's expected behavior, not something to chase as your own
mistake. This is specific to pubsub relay, distinct from the RPC
discovery issues above.

## See also

- [FAQ: How do I run macula-cli?](FAQ_MACULA_CLI.md) — `dht find-record(s)/find-records-by-type`, the worked example that first surfaced the `unknown_next_peer` retry question
- [FAQ: How do I authorize a procedure or topic with UCAN?](FAQ_AUTHORIZE_WITH_UCAN.md) — for `unauthorized` specifically
- [FAQ: Developing Edge Services in Go](FAQ_DEVELOP_EDGE_SERVICES_GO.md) / [Rust](FAQ_DEVELOP_EDGE_SERVICES_RUST.md) / [C#/F# (.NET)](FAQ_DEVELOP_EDGE_SERVICES_DOTNET.md) / [PHP](FAQ_DEVELOP_EDGE_SERVICES_PHP.md) — each SDK's direct-dial API
- [FAQ: How do I run a local station for dev/testing?](FAQ_RUN_A_LOCAL_STATION.md) — sidesteps most of this by avoiding shared-fleet gossip entirely
