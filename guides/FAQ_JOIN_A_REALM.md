---
title: "FAQ: Joining a Realm — Getting Your Service an Identity and Certificate"
layer: guide
audience: [agent, human]
stage: stable
---

# FAQ: How Do I Join a Realm and Get My Service an Identity/Certificate?

[Back to FAQ index](FAQ.md) · [Back to corpus index](../INDEX.md)

[FAQ: How do I join the Mesh?](FAQ_JOIN_THE_MESH.md) covers running a
**station** — realm-agnostic routing infrastructure that never joins a
realm itself. This page is the other half: how a **service** actually
gets a realm-signed identity so it can be authorized to do something on
the mesh.

This is a genuinely three-layer situation and this page keeps the
layers separate rather than blending them: how a **human** actually
joins today, a real working cert-issuance flow for **services** you can
use today, and a broader identity/authorization model that is an
active, dated design-in-progress — not yet built.

---

## 0. How a human joins today: macula-realm's join-session flow

This is the section this page's title has always promised and, until
now, never actually delivered — sections 1-3 below are all about
**service** identity, not a person joining. Verified live 2026-09-05
against production `realm.macula.io`, a real join producing a genuine
`201`.

**`realm.macula.io` owns this — not `macula-portal`, and not the bare
`macula.io` domain.** The two split 2026-08-30 (`macula-realm` for
mesh-membership/join, `macula-portal` for org/app management and
licensing); the join flow lived briefly on `macula.io` itself before
that, which is why older material may point there or at
`macula-portal`. Both are stale — if you land here from `macula-mcp`'s
own `MACULA_MCP_PORTAL_URL`, that variable no longer controls this flow
at all; the correct one is `MACULA_MCP_REALM_URL`, default
`https://realm.macula.io`.

**If you're an agent using `macula-mcp`**, the tool is `mesh_join_realm`
and you don't need anything below this paragraph — call it, hand the
person the link/QR it returns, then call it again with `wait_seconds`
once they've had a chance to confirm. The rest of this section is the
wire-level detail underneath that tool, for anyone building a different
client against the same endpoint.

**The flow** (RFC 8628 device-authorization shape):

```
POST /api/v1/join/sessions
Content-Type: application/json

{
  "node_id":          "base64-or-hex-encoded-ed25519-public-key",
  "timestamp":        1757000000000,
  "proof_signature":  "base64-encoded-signature"
}
```

`proof_signature` is a signature, by the same key named in `node_id`,
over the exact byte layout `node_id (32 raw bytes) ++ timestamp (8
bytes, big-endian) ++ "macula_realm.join_session" (raw UTF-8, no
delimiters)` — proof that whoever is requesting the session actually
holds the private key, not just claiming a public one. The procedure
string is part of the signed bytes, not a label: it has to match
`macula-realm`'s own `join_session_controller.ex`/`joining.ex`
`@join_procedure` exactly, or a perfectly valid signature verifies
against the wrong message and is rejected.

→ `201`, a ten-minute session: an approval URL (usable directly as a
link, or rendered as a QR code) for the person to open. They sign in
with Hanko, see which agent on which machine is asking, and confirm.

```
GET /api/v1/join/sessions/:id
```

polls for the outcome. Once confirmed, it hands back the org identity
(`mri:org:io.macula/<handle>`), a refresh token for the realm's own
API, and a realm-CA-signed certificate for the requesting key — the
same shape §1 below describes for a service, but for a human-vouched
identity instead of an operator-provisioned one.

Two-step by nature: the link has to physically reach the person before
anything can be confirmed, so any client built on this should return
the link/QR immediately and poll separately for the outcome, rather
than blocking on one call.

---

## 1. The real, working flow today: service-principal certs from `macula-portal`

**`macula-portal` owns PKI/cert issuance. `macula-realm` (a separate,
more recently extracted repo) owns mesh membership/gossip/topology
only** — its own README describes "realm lifecycle, realm-member
admission, station links," with no cert-issuance code in it. Don't
confuse the two despite the similar names; this page is entirely about
`macula-portal`.

Every mcl-* service running on realm infrastructure carries its own
realm-signed credential — an institution of the realm, not a user's
identity (`hecate-corpus/philosophy/TIER_MODEL.md`'s
citizens-vs-institutions framing). The real endpoint
(`macula-portal`'s `ServicePrincipalIssuanceController`):

```
POST /api/v1/services/provision
Authorization: Bearer mrt_…
Content-Type: application/json

{
  "public_key":   "base64-encoded-ed25519-public-key",
  "service_name": "mcl-rag",
  "node_name":    "beam00"
}
```

→ `201`:

```json
{
  "org_identity":  "mri:org:io.macula/rgfaber",
  "service_mri":   "mri:app:io.macula/rgfaber/_service-mcl-rag-beam00",
  "service_name":  "mcl-rag",
  "node_name":     "beam00",
  "cert_pem":      "-----BEGIN CERTIFICATE-----…",
  "org_ca_pem":    "-----BEGIN CERTIFICATE-----…",
  "ca_chain_pem":  "-----BEGIN CERTIFICATE-----…"
}
```

**The flow** (operator, or a gitops reconciler, does this at install
time — not automated by anything running on a schedule):

1. Generate a fresh Ed25519 keypair for the service.
2. POST the pubkey + `service_name` + `node_name` to the endpoint above,
   presenting a refresh token as bearer auth. `service_name` must match
   `^mcl-[a-z][a-z0-9-]{0,55}$`.
3. Write the response's `cert_pem`/private key to
   `/etc/mcl/secrets/<service-name>/service-cert.pem` (+
   `service-key.pem`) on the target node.
4. The Quadlet/compose unit mounts that directory read-only into the
   container at `/etc/mcl/secrets/service-cert.pem`, which
   `mcl_om_identity` (macula-services/mcl-om) reads at boot.

`cert_pem` is the leaf; `org_ca_pem` is the intermediate org CA that
issued it; `ca_chain_pem` is the realm CA (the trust anchor) — a service
embeds `cert_pem ++ org_ca_pem` in its `procedure_advertisement` so a
direct-dial consumer can verify it to the realm CA offline. **The
response never includes the private key** — the service generates its
own keypair and keeps the private half; the realm only ever sees and
signs the public half.

This is explicitly labeled **v1** in `mcl_om_identity`'s own doc
comment: "long-lived realm-signed cert provisioned out-of-band by a
realm-admin script." A stated **v2** exists only on paper so far:
"short-lived UCAN auto-rotated from a realm HTTP endpoint" — the module
is written so that swap-in lands without touching consumers, but it
hasn't landed.

**Known v1 gap, from the controller's own doc comment:** no CRL beyond
cert TTL expiry (rotation happens by re-POST), and **no per-service
authorization policy yet — every refresh-token holder can provision any
service-principal.** Phase 2 is meant to add a `services` claim to the
refresh token plus an admin policy file; not built yet.

---

## 2. `identity_spec/0` is a declared manifest today, not (yet) enforcement

Every `mcl_om_service` implementation exports an `identity_spec/0`
callback (see
[FAQ: Developing Edge Services in BEAM Languages](FAQ_DEVELOP_EDGE_SERVICES_BEAM.md)) —
the scaffold's own template comment calls it "THE AUTHORITY THIS SERVICE
ASKS THE REALM FOR." It reads like a real authorization request. **It
currently is not one**, verified by reading `mcl_om:boot/2`
(macula-services/mcl-om) end to end: it calls a service's
`capabilities/0` and `start/1`, registers with `mcl_om_capabilities`
— and never calls `identity_spec/0` anywhere in the runtime boot path.

It's still real and required — a compile-time-enforced `-callback`, and
the scaffold's own generated test suite shape-checks it (added
specifically after an earlier template version shipped an
`identity_spec` claiming authority over resources the generated service
could not actually touch, with nothing checking it). But today it's a
**self-declared intent manifest**, not wired to any enforcement — don't
write one assuming a realm somewhere is reading and gating on it yet.

---

## 3. The bigger picture is an active, dated design — not shipped

`macula-io/macula-architecture/plans/PLAN_CITIZEN_IDENTITY_AUTHN_AUTHZ.md`
(Status: Draft v1.0, created **2026-09-01**) opens by naming the actual
state of things plainly: "Three pieces of this were already designed,
separately, and never reconciled" — a Hanko-based identity layer cake
that scoped authorization out as future work, a provisional-realm trust
ladder for zero-human bootstrap, and the UCAN capability-token guide
above (real and implemented, but opt-in per procedure, never used as a
general policy). A fourth piece — `macula-realm`'s original
membership model, keyed on a device's mesh pubkey with no representation
of the human behind it — was designed, then explicitly paused
2026-08-28 as wrong on its own terms.

**Treat this plan document as exactly that: an active reconciliation
effort, not settled architecture.** The service-principal cert flow in
§1 is real and usable right now; the citizen/UCAN/realm-membership model
this plan is reconciling is not built yet. If you're integrating
identity/authorization into a new service, use §1's flow for what a
service concretely needs today, and check the plan doc directly for
anything beyond that rather than trusting a description of it here that
would go stale the moment the plan moves.

---

## See also

- [FAQ: macula-mcp](FAQ_MACULA_MCP.md) — the `mesh_join_realm` tool that wraps §0's flow for an agent
- [FAQ: How do I join the Mesh?](FAQ_JOIN_THE_MESH.md) — the realm-agnostic station layer this page's realm layer sits above
- [FAQ: How do I authorize a procedure or topic with UCAN?](FAQ_AUTHORIZE_WITH_UCAN.md) — the one authorization primitive that IS enforced by the SDK today
- [FAQ: Developing Edge Services in BEAM Languages](FAQ_DEVELOP_EDGE_SERVICES_BEAM.md) — `identity_spec/0` and the `mcl_om_service` behaviour
- [FAQ: How do I deploy my own mcl-* service?](FAQ_DEPLOY_SERVICES.md) — where the resulting cert actually gets mounted into a running container
