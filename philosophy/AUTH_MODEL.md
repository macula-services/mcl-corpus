---
title: Macula Auth Model — Four Channels, One Delegation Chain
layer: philosophy
audience: [agent, human]
stage: draft
---

# Macula Auth Model — Four Channels, One Delegation Chain

*This exists so a human, an agent, or a phone can reach an mcl-* service
and the service can trust who's asking, without four different auth
systems.*

**Status: draft.** The identity primitives it builds on
(`mcl_om_identity`, `macula-realm`, `macula-cli`'s local keypair,
`mcl_om`'s `ucan_token`/`verify => true` RPC option) are real and
already shipping. The parts specific to this doc — a human-membership-
rooted delegation chain, the pairing flow generalized beyond
`macula-console`, a separate agent identity for `macula-mcp` — are a
proposal, not yet built. See "What's open" at the end.

---

## The one root primitive

Realm membership (`macula-realm`) is the root of trust for humans, the
same way a service's realm-signed cert (`mcl_om_identity`) is the
root of trust for services. **UCAN is the one delegation currency for
everything downstream of either root**: a chain of scope-narrowing
tokens, each signed by the previous holder, verified back to a trust
anchor. `mcl_om` already verifies exactly this shape for
service-to-service calls — `mcl_om:call_capability/4,5`'s
`verify => true` walks a realm → org → server delegation chain and
drops any provider whose chain doesn't resolve.

This doc is mostly about pointing that same verifier at chains rooted
in a **human's realm-membership record**, not inventing a second
verification system:

```
realm CA (macula-realm)
  │
  ├─▶ org CA ──▶ service leaf cert           (existing: service-to-service)
  │              "I am mcl-tube, org Acme"
  │
  └─▶ realm_membership_admitted_v1 record    (this doc: human-to-service)
         │
         ├─▶ macula-cli's local keypair       — channel (a), full scope
         ├─▶ macula-mcp's agent keypair        — channel (b), narrowed scope
         ├─▶ a browser's session-lifetime UCAN — channel (c), session scope
         └─▶ a phone's device keypair          — channel (d), device scope
```

Every arrow is the same primitive: a UCAN, narrower than its parent,
expiring sooner than its parent. A capability call carries the token at
the bottom of whichever chain issued it; a gated service verifies the
whole chain back to the realm CA and checks the requested action against
the narrowest scope in the chain, not just the caller's immediate token.

---

## The four channels

| Channel | Entry point | Identity | Delegation |
|---|---|---|---|
| (a) Terminal | `macula-cli` | Local puzzle-hardened Ed25519 keypair (`~/.config/macula-cli/identity.seed`), generated once, reused forever | UCAN minted from the human's realm-membership record, cached locally, refreshed before expiry |
| (b) Coding agent | `macula-mcp`, which spawns `macula-cli` per tool call | A **separate** keypair from (a) (`macula-cli --identity ~/.config/macula-cli/agent-identity.seed`) | A narrower UCAN, delegated by the human specifically to "agent acting on my behalf" — independently revocable |
| (c) Operator website | The edge service serves its own UI directly (Cowboy/Phoenix — same pattern as `mcl-whiteboard`/`mcl-tube` today) | Either none (open mode) or a session-lifetime UCAN obtained via pairing | See "Two modes" below |
| (d) Mobile app / public site | `macula-portal` (enrollment) + the app's own local keypair | Device generates its own long-lived keypair on first launch (same self-healing generate-if-missing pattern `mcl_om_identity` and `macula-cli` already use) | A UCAN delegated from the human's membership at pairing time; every privileged action then rides a short-lived, action-scoped credential minted per-use — not the device's own long-lived key |

### (a) Terminal — `macula-cli`

The identity layer already exists: first run mints a puzzle-hardened
Ed25519 keypair, persisted and reused (`internal/identitystore`,
mirroring `mcl_om_identity:keypair/0`'s own
generate-if-missing-and-persist pattern). What's proposed here: when a
command hits a gated capability, `macula-cli` holds a UCAN delegated
from the human's realm-membership record — minted once via a
`macula-realm` mesh-RPC call (alongside its existing
`get_member_public_keys`), cached, refreshed before expiry, attached as
`ucan_token` on calls that need it. Open capabilities need nothing extra
— most of the mesh stays reachable with just the bare peering keypair,
exactly as today.

### (b) Coding agent — `macula-mcp` via `macula-cli`

`macula-mcp`'s own README is explicit: it "does not speak QUIC, DHT, or
Macula RPC itself... shells out to `macula-cli`... for every mesh
operation" and carries no mesh logic of its own. Today that means an
agent session spawned with no `--identity` override acts under the
human's own root identity — full authority, no separate audit trail, no
way to revoke "the agent" without rotating the human's own key too.

**Proposal:** always spawn `macula-cli` for agent-originated calls with
a distinct `--identity` pointing at its own keypair, delegated a
narrower UCAN from the human. A misbehaving or compromised agent session
is then revocable on its own, and every mesh-visible action an agent
took is attributable to the agent's own identity, not folded into the
human's.

### (c) Operator website — the edge service serves its own UI

Two legitimate modes — this is a fork, not a gap to close:

**Open.** `mcl-whiteboard` today: no `verify => true` anywhere,
visiting browsers get an ephemeral per-tab identity for presence only
(`track_presence`'s ETS roster). This is a fine, complete answer for a
public demo board or any service whose whole point is "anyone can use
this" — it needs nothing from this doc.

**Gated.** For a service managing something realm-scoped: reuse
`macula-portal`'s existing pairing-code flow. ⚠ Verified 2026-09-05:
no such route currently exists — `macula-portal`'s real API surface has
`/api/v1/console/heartbeat`, `/api/v1/console/sync`, and
`/api/v1/join-tokens` (join tokens for unattended nodes), none of which
is a pairing-code flow. There is no route named `/api/console/pair` or
similar. This paragraph's "existing" is aspirational, not current —
building the flow described below is itself part of what this doc
proposes, not a reuse of something already there.

The design: the website shows a pairing code; the
human's already-authenticated `macula-cli` (or, later, a push-approval
from a paired phone) approves it; `macula-realm` mints a
session-lifetime UCAN; the edge service verifies it per-request through
the same `ucan_token`/`verify => true` mechanism a Layer-2 RPC caller
already uses. "Log into a website" and "pair a device" become the same
mechanism at two different token lifetimes — not two systems.

### (d) Mobile app / public website

**`macula-portal`** is the front door for people who aren't realm
members yet: conventional email/OAuth signup, then a bridge into
`macula-realm`'s `admit_realm_member` — the same code path that already
provisions app certs for paired consoles, just re-pointed at mobile
apps instead of the dead desktop console.

**`cam2me` / `passport`**: the device mints its own long-lived keypair
on first launch, then pairs via `macula-portal` to receive a UCAN
delegated from the human's membership. The scoping principle isn't
hypothetical here — it's already shipping: `mcl-turn-credentials`
exists specifically so `cam2me`'s own long-lived key is never asked to
do more than identify the device. Every privileged operation (TURN
relay access) rides a short-lived credential minted per-use, and the
coturn master secret never leaves the service that mints it. That's the
template for every future mobile capability: the device identity
answers "who's asking," a short-lived UCAN answers "is this specific
action allowed," and the two are never the same token.

---

## What's open

- **`macula-cli ucan mint`/`ucan inspect`/`call -ucan` already exist**
  (verified against source, not assumed) — a human can mint a delegated
  UCAN and attach it to a call today, by hand. What's missing is
  integration, not the primitive.
- **`mcl_om_capabilities:call_capability/5,7`'s `verify => true` verifies
  the *provider's* org-rooted service-cert chain** (`keep_chain_verified`
  → `macula_record:verify_advertisement_cert_chain/3`), not a caller's
  UCAN. It forwards a `ucan_token` opaquely to the provider it dials —
  whether any gated mcl-* service actually verifies an incoming
  `ucan_token` resolves back to a human's realm membership is genuinely
  unconfirmed, not just undecided. Real, unscoped investigation, not a
  known code change.
- **The pairing UX itself is undecided** — QR code, numeric code, and
  push-approval-from-a-paired-phone are all consistent with the design
  above; none is chosen yet.

None of the four channels needs its own bespoke auth system to close
these gaps — each is a delegation off the same root, at a different
scope and a different lifetime.
