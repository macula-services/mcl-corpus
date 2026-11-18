---
title: "FAQ: Authorizing with UCAN in Go"
layer: guide
audience: [agent, human]
stage: stable
---

# FAQ: How Do I Authorize a Procedure with UCAN in Go?

[Back to FAQ: Authorizing with UCAN](FAQ_AUTHORIZE_WITH_UCAN.md) ·
[Back to FAQ index](FAQ.md) · [Back to corpus index](../INDEX.md)

Full runnable example: `macula-go/examples/ucan/main.go` —
`go run ./examples/ucan`.

```go
// providerID doubles as the token issuer here -- the policy requires a
// token signed by whichever key the provider decides to trust.
token, _ := ucan.Create("did:macula:example-issuer", "did:macula:example-audience", nil, providerID, ucan.CreateOpts{})

realm := make([]byte, 32)
provider.Advertise(frame.NewAdvertiseSpec(realm, procedure, providerID.NodeID()), providerID)

// Gate the procedure: only a caller presenting a token signed by
// providerID's own key is let through to lookup/dispatch.
policy := func(_ []byte, _ string) ucan.Policy { return ucan.Required(providerID.NodeID()) }
go provider.ServeOneCallGated(lookup, policy, providerID, 15*time.Second)

// No token: refused with the Unauthorized error before the handler ever runs.
resp, _ := caller.Call(procedure, realm, cbor.Null(), deadlineMs, callerID, 10*time.Second)

// A valid token: reaches the handler for real.
resp, _ = caller.CallWithUCAN(procedure, realm, cbor.Null(), deadlineMs, callerID, 10*time.Second, token)
```

Real API (`macula-go/ucan/policy.go`): `type Policy struct { Gated bool; RequiredIssuer []byte }`,
`var Open = Policy{}` (default), `func Required(issuerPublicKey []byte) Policy`.
Mirrors the Erlang reference's own shape exactly: `open | {ucan_required, Issuer}`.

## See also

- [FAQ: Authorizing with UCAN](FAQ_AUTHORIZE_WITH_UCAN.md) — the shared model, token format, and `macula-cli` mint/inspect
- [FAQ: Developing Edge Services in Go](FAQ_DEVELOP_EDGE_SERVICES_GO.md) — the base Go SDK this builds on
- [FAQ: Authorizing with UCAN in Rust](FAQ_AUTHORIZE_WITH_UCAN_RUST.md) / [C#/F# (.NET)](FAQ_AUTHORIZE_WITH_UCAN_DOTNET.md) / [PHP](FAQ_AUTHORIZE_WITH_UCAN_PHP.md) / [Erlang/Elixir/Gleam](FAQ_AUTHORIZE_WITH_UCAN_BEAM.md)
