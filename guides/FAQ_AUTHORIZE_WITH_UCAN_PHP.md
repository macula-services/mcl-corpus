---
title: "FAQ: Authorizing with UCAN in PHP"
layer: guide
audience: [agent, human]
stage: stable
---

# FAQ: How Do I Authorize a Procedure with UCAN in PHP?

[Back to FAQ: Authorizing with UCAN](FAQ_AUTHORIZE_WITH_UCAN.md) ·
[Back to FAQ index](FAQ.md) · [Back to corpus index](../INDEX.md)

Two-process worked example (same pattern as this SDK's other
provider-role examples — see
[FAQ: Developing Edge Services in PHP](FAQ_DEVELOP_EDGE_SERVICES_PHP.md)):
`examples/09_ucan_gated_serve.php` (provider) +
`examples/09_ucan_gated_serve_call.php` (caller), orchestrated by
`examples/09_run_ucan_gated_serve.sh`. A separate, no-network,
no-live-station example — `examples/09_ucan.php` — covers the pure
mint/verify round trip.

```php
// Caller half. First call, no token: expects the Unauthorized error (0x10).
$unauthorized = $session->call($procedure, $realm, Value::int(21), 10000);
// $unauthorized->isError() === true, $unauthorized->code() === 0x10

$token = Ucan::create(
    issuer: 'did:macula:example-authority',
    audience: 'did:macula:example-caller',
    capabilities: [],
    identity: $authority,
    expiresAtUnixSec: time() + 60,
);

// Second call, with the token: reaches the handler for real.
$authorized = $session->callWithUcan($procedure, $realm, Value::int(21), $token, 10000);
```

`Ucan::create()`'s full signature (from the mint/verify example):
`issuer`, `audience`, `capabilities` (array of `['with' => ..., 'can' => ...]`),
`identity` (the signing `KeyPair`), optional `expiresAtUnixSec` /
`notBeforeUnixSec`. `Ucan::verify($token, $publicKey)` returns a decoded
payload object (`->issuer()`, `->audience()`, `->capabilities()`) and
throws on a bad signature or wrong issuer key; `Ucan::isExpired($token)`
checks expiry without a full verify.

## See also

- [FAQ: Authorizing with UCAN](FAQ_AUTHORIZE_WITH_UCAN.md) — the shared model, token format, and `macula-cli` mint/inspect
- [FAQ: Developing Edge Services in PHP](FAQ_DEVELOP_EDGE_SERVICES_PHP.md) — the base PHP SDK this builds on
- [FAQ: Authorizing with UCAN in Go](FAQ_AUTHORIZE_WITH_UCAN_GO.md) / [Rust](FAQ_AUTHORIZE_WITH_UCAN_RUST.md) / [C#/F# (.NET)](FAQ_AUTHORIZE_WITH_UCAN_DOTNET.md) / [Erlang/Elixir/Gleam](FAQ_AUTHORIZE_WITH_UCAN_BEAM.md)
