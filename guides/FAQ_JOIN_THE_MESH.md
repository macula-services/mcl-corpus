---
title: "FAQ: How Do I Join the Mesh?"
layer: guide
audience: [agent, human]
stage: stable
---

# FAQ: How Do I Join the Mesh?

[Back to FAQ index](FAQ.md) · [Back to corpus index](../INDEX.md)

This answers "how do I run my own station" — the relay/routing infrastructure
peers dial to reach each other. If you instead want your *own service* to
connect to the mesh as a client (no relay of your own), you don't need any of
this: see [macula-cli](FAQ_MACULA_CLI.md) or the SDK guides for
[BEAM](FAQ_DEVELOP_EDGE_SERVICES_BEAM.md),
[Go](FAQ_DEVELOP_EDGE_SERVICES_GO.md),
[Rust](FAQ_DEVELOP_EDGE_SERVICES_RUST.md),
[.NET](FAQ_DEVELOP_EDGE_SERVICES_DOTNET.md), or
[PHP](FAQ_DEVELOP_EDGE_SERVICES_PHP.md) instead, and
connect to a public station like `station-de-frankfurt.macula.io`.

Everything below is sourced from `macula-io/macula-station`'s own
`docs/DEPLOYMENT_GUIDE.md` and `Dockerfile` — read those directly for the full
depth (a real production incident writeup, the fleet roster, more edge cases)
this FAQ entry condenses. **Only §1–4 below (the container, config, and the
certificate gotcha) are exercised by this org's own live fleet.** Docker +
watchtower is the org's actual, only station deployment mechanism today;
Podman/Quadlet and Kubernetes are documented as correct starting points for
an operator who wants them, not as patterns this org runs itself — said
plainly rather than implied.

---

## 1. What a station is

One container = one station = one Ed25519 keypair. A station is
**realm-agnostic infrastructure** — it never joins a realm itself, it routes
for daemons (SDK clients) that do. Stations peer with each other outbound to
form the mesh; nothing about a station's own boot sequence requires DNS, a
load balancer, or inbound firewall exceptions beyond the one QUIC port.

Two network endpoints:

| Port | Protocol | Purpose |
|---|---|---|
| `4433` | UDP (QUIC) | The mesh wire protocol. Daemons and peer stations dial this. |
| `8443` | TCP | Admin/health HTTP. `/wire` is the liveness probe (unauthenticated); `/admin/*` needs bearer auth. |

**A station needs a real, public, routable address.** Its entire job is
accepting inbound QUIC from clients and other stations anywhere on the
internet — it cannot do that from behind NAT or a private network with no
public address of its own. `network_mode: host` / `hostNetwork: true` (below)
only helps if the host itself already has one.

---

## 2. The container image

Multi-stage build: an `erlang:28.1-slim` builder (with a Rust toolchain,
since the SDK's QUIC transport is a Rust NIF built from source rather than
fetched precompiled — a prebuilt release NIF once hung every connect and took
a real realm dark), producing an `rebar3 as prod release`; then a slim
`debian:bookworm` runtime stage.

```bash
docker build -t ghcr.io/macula-io/macula-station:latest .
```

**Published tags:**

| Trigger | Tags pushed | Platforms |
|---|---|---|
| Push to `main` | `:main`, `:<git-sha>` | `linux/amd64` only |
| Push a `v*` tag (e.g. `v0.4.2`) | `:0.4.2`, `:0.4`, `:latest` | `linux/amd64` + `linux/arm64` |

**The published tags drop the `v` prefix** — CI's `manifest` job strips it
(`VERSION="${GITHUB_REF#refs/tags/v}"`) before pushing, so a `v0.4.2` tag
push publishes `ghcr.io/macula-io/macula-station:0.4.2`, not `:v0.4.2`.
Pulling the `v`-prefixed form fails with "not found" — pin the bare
version instead. `:latest` only moves on a version tag, not on every
`main` push — a watchtower-tracked box does not roll on ordinary commits,
only on an actual release. Every `:<git-sha>` and version tag stays in the
registry permanently as a pinnable rollback target.

**What the registry actually holds today:** no `v*` tag has ever been pushed
on `macula-station`, so `ghcr.io/macula-io/macula-station` carries only
`:main` and `:<git-sha>` tags — there is no `:latest` and no `X.Y.Z` tag to
pull. The fleet's own compose files run
`image: ghcr.io/macula-io/macula-station:${STATION_VERSION:-main}`. Until a
first version tag is published, use `:main` (or pin a `:<git-sha>`) wherever
the examples below would otherwise say `:latest` or `X.Y.Z`; the table above
is what CI will do once a version tag exists.

---

## 3. Config file

One JSON file, mounted read-only, pointed to by `MACULA_STATION_CONFIG`
(default `/etc/macula-station/config.json`):

```json
{
  "data_dir":     "/var/lib/macula/station",
  "identity_file": "/var/lib/macula/station/identity.erl.bin",
  "bind":         "2600:3c1a:e001:19::be:01",
  "port":         4433,
  "certfile":     "/certs/station.crt",
  "keyfile":      "/certs/station.key",
  "capabilities": 0,

  "outbound_peers": [
    { "host": "station-de-frankfurt.macula.io", "port": 4433 }
  ],

  "cache": {
    "path": "/var/lib/macula/station/cache",
    "flush_period_ms": 30000
  },

  "rebootstrap": {
    "min_viable_peers": 8,
    "check_period_ms": 5000,
    "partition_window_ms": 60000
  },

  "peering_redundancy": {
    "min_station_peers": 3,
    "check_period_ms": 60000,
    "cooldown_ms": 300000,
    "candidate_pool": 32
  },

  "admin": { "bind": "127.0.0.1", "port": 8443 },

  "geo": {
    "hostname": "station-be-brussels.macula.io",
    "city":     "Brussels",
    "country":  "BE",
    "lat":      50.8503,
    "lng":      4.3517,
    "power_m":  1200
  },

  "bootstrap": {
    "discoverers": [],
    "cascade_opts": {}
  },

  "puzzle_enforcement": "off"
}
```

**Required:** `data_dir`, `bind`, `port`, `certfile`, `keyfile`. Everything
else has a default and can be omitted.

- **`geo.hostname` is optional and deliberately so.** A station with no DNS
  entry still boots, peers, and routes fine — `geo.hostname` only feeds a
  topology dashboard's display, not connectivity. This is a supported,
  tested configuration, not an edge case merely tolerated.
- **`outbound_peers` is how a station finds the rest of the mesh** — it
  dials these on boot and stays connected. A station with an empty list
  boots successfully but is an island until either a peer dials *it*, or you
  add at least one entry. Pointing at one well-known public station (as
  above) is enough to join the existing mesh; the DHT/gossip layer takes it
  from there.
- **`puzzle_enforcement` gates whether identity proof-of-work puzzles are
  actually checked** — `"off"` (default), `"log_only"` (violations
  logged, connection still accepted), or `"enforce"` (a connecting
  identity that fails the puzzle check is rejected). Verified directly
  against `macula_station_config.erl`'s own parser — it's a real, live
  option (`decode_puzzle_enforcement/1`, rejects anything but these three
  exact strings rather than silently defaulting a typo to `off`), but
  it's absent from both this org's own `DEPLOYMENT_GUIDE.md` and that
  module's own top-of-file doc comment. Worth knowing this exists even
  though nothing else documents it yet.

---

## 4. The certificate gotcha that will bite you once

**The certificate at `certfile`/`keyfile` must be self-signed from the
station's own Ed25519 identity — an ordinary CA-issued or ad-hoc
`openssl req` certificate will NOT work.**

A station's peers validate its connection two ways — `Trust::WebPki`
(ordinary CA-chain validation, needs a real DNS name and CA-issued cert) or
`Trust::Pinned{node_id}` (pins the station's raw Ed25519 public key straight
from the cert's SPKI — no CA, no DNS required, and what makes a no-DNS
station reachable at all). Pinned trust only works if the certificate's key
**is** the station's identity key; a generic self-signed cert with a
different keypair gets rejected outright.

**The fix — a two-phase boot, because the identity doesn't exist until the
station has booted once:**

1. **Phase 1**: start the container with a throwaway placeholder cert (any
   valid EC cert works — it only needs to let the process come up long
   enough to generate its identity). On first boot, the station
   generates/loads its Ed25519 identity at `identity_file`.
2. Derive the real cert from that identity, from inside the running
   container:

   ```bash
   docker exec <container> /opt/macula_station/bin/macula_station eval '
     {ok, Id} = macula_station_identity:load_or_generate(
                   macula_station_identity:path_for(<<"/var/lib/macula/station">>)),
     Pub  = macula_identity:public(Id),
     Priv = macula_identity:private(Id),
     {ok, {Cert, Key}} = macula_quic:generate_self_signed_cert(Pub, Priv, [<<"your.hostname.or.anything">>]),
     ok = file:write_file("/certs/station.crt", Cert),
     ok = file:write_file("/certs/station.key", Key).
   '
   ```

3. **Phase 2**: restart the container with the real, identity-derived cert
   in place. `Trust::Pinned` connections work from here on.

This whole sequence is scripted end to end in
`macula-demo/infrastructure/stations-linode-toronto/deploy.sh` — copy that
pattern rather than re-deriving it.

**A station does not need a realm cert or service-principal cert of its own**
— per §1, it's realm-agnostic; only the daemons/clients that dial through it
carry realm membership.

---

## 5. Docker + watchtower (this org's real fleet pattern — the one section that's actually load-bearing)

```yaml
services:
  station:
    image: ghcr.io/macula-io/macula-station:main   # the only moving tag published so far, see §2
    restart: unless-stopped
    network_mode: host
    environment:
      MACULA_STATION_CONFIG: /etc/macula-station/config.json
      MACULA_NODE_NAME: macula_station
    volumes:
      - ./config.json:/etc/macula-station/config.json:ro
      - ./certs:/certs:ro
      - station_data:/var/lib/macula/station
    labels:
      - "com.centurylinklabs.watchtower.enable=true"

  watchtower:
    image: containrrr/watchtower
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --interval 60 --label-enable

volumes:
  station_data:
```

`network_mode: host` — the station needs to bind a real routable
IPv4/IPv6 address for QUIC, not a container-bridge address peers can't
reach; that's why there's no `ports:` section. Watchtower polls ghcr for a
new digest at the currently-running tag and recreates the container in
place — no redeploy step beyond a push that moves the tracked tag. It does
not touch config files or volumes.

⚠ The fleet tracks `:main` today, the only moving tag that exists (§2), so a
watchtower box rolls on every commit to `main` — code or not; put
`paths-ignore` on the image build for docs-only changes. Once version tags
are published, point production boxes at `:latest` (or a pinned `X.Y.Z`,
no `v` prefix) and keep `:main`/`:<sha>` for staging.

---

## 6. Podman + Quadlet (a correct starting point, not an org-run pattern)

Podman is genuinely different infrastructure from Docker/watchtower — it
uses systemd-native Quadlet units plus `podman auto-update` instead of
watchtower. **Don't run watchtower alongside Podman-managed containers** —
watchtower recreates containers directly and fights with systemd for
ownership of the same unit.

`~/.config/containers/systemd/macula-station.container`:

```ini
[Unit]
Description=Macula Station

[Container]
Image=ghcr.io/macula-io/macula-station:main
Network=host
Volume=%h/macula-station/config.json:/etc/macula-station/config.json:ro
Volume=%h/macula-station/certs:/certs:ro
Volume=macula-station-data.volume:/var/lib/macula/station
Label=io.containers.autoupdate=registry

[Service]
Restart=always

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user start macula-station
```

`podman-auto-update.timer` pulls a changed digest at the tracked tag and
restarts the unit — a config or volume *content* edit still needs a manual
`daemon-reload && restart`, the timer only reacts to image digest changes.

---

## 7. Kubernetes (a correct starting point, not an org-run pattern)

QUIC needs a real routable address per station, and `hostNetwork` is the
direct equivalent of `network_mode: host` — a `ClusterIP`/`LoadBalancer`
Service in front of a UDP QUIC listener does not preserve the per-connection
5-tuple the way stations expect, so don't put one there. Each station pod
gets the node's own IP.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: macula-station
spec:
  serviceName: macula-station
  replicas: 1
  selector:
    matchLabels: { app: macula-station }
  template:
    metadata:
      labels: { app: macula-station }
    spec:
      hostNetwork: true
      dnsPolicy: ClusterFirstWithHostNet
      containers:
        - name: station
          image: ghcr.io/macula-io/macula-station:<git-sha>   # pin a tag that exists (see §2): a git sha today, X.Y.Z once published
          env:
            - { name: MACULA_STATION_CONFIG, value: /etc/macula-station/config.json }
          ports:
            - { containerPort: 4433, protocol: UDP }
            - { containerPort: 8443, protocol: TCP }
          volumeMounts:
            - { name: config, mountPath: /etc/macula-station, readOnly: true }
            - { name: certs,  mountPath: /certs, readOnly: true }
            - { name: data,   mountPath: /var/lib/macula/station }
          readinessProbe:
            httpGet: { path: /wire, port: 8443 }
            periodSeconds: 10
          livenessProbe:
            httpGet: { path: /wire, port: 8443 }
            periodSeconds: 30
            failureThreshold: 3
      volumes:
        - name: config
          configMap: { name: macula-station-config }
        - name: certs
          secret: { secretName: macula-station-certs }
  volumeClaimTemplates:
    - metadata: { name: data }
      spec:
        accessModes: [ReadWriteOnce]
        resources: { requests: { storage: 5Gi } }
```

Pin an explicit tag that exists (a `:<git-sha>` today, `X.Y.Z` with no `v`
prefix once version tags are published — see §2) rather than a moving tag —
nothing in a plain
Kubernetes Deployment/StatefulSet polls the registry the way watchtower or
`podman auto-update` do; `:latest` here just means "whatever was current the
first time this pod scheduled," silently. If you want auto-updates, put a
tool like Flux or Keel in front of it. Same certificate rule as §4 applies —
derive the `certs` Secret from the station's own identity after first boot.

---

## 8. Health and readiness

`GET /wire` on the admin port — **not** `/status`. `/status` is hardcoded
`200` regardless of actual health; a station receiving every packet sent to
it and dispatching none stayed green on `/status` for 30 hours in a real
incident before the healthcheck was fixed to use `/wire`, which returns
`503` specifically when the kernel is holding undispatched datagrams on the
station's own listener socket.

Going unhealthy is **not** sufficient on its own to recover a stuck
station — `restart: unless-stopped` (Docker) or a default pod restart policy
only reacts to the process actually exiting, not to a failing health check
while the process stays up. Kubernetes' `livenessProbe` with
`failureThreshold` (shown above) handles this correctly out of the box; the
Docker/Podman forms do not, and need an external watcher for the same
guarantee.

---

## See also

- [`macula-io/macula-station`'s own README](https://github.com/macula-io/macula-station) —
  architecture overview, what a station actually is
- [`macula-io/macula-station/docs/DEPLOYMENT_GUIDE.md`](https://github.com/macula-io/macula-station/blob/main/docs/DEPLOYMENT_GUIDE.md) —
  the full version of this document, with citations into the actual source
- [`macula-io/macula-station/docs/CASCADE_INVESTIGATION.md`](https://github.com/macula-io/macula-station/blob/main/docs/CASCADE_INVESTIGATION.md) —
  a real production incident and its fix
- [FAQ: How do I deploy my own mcl-* service?](FAQ_DEPLOY_SERVICES.md) —
  the equivalent walkthrough for a service, not a station
- [FAQ: How do I run macula-cli?](FAQ_MACULA_CLI.md) — connecting to a
  station as a client, without running one yourself
- [FAQ: How do I join a realm and get my service an identity/certificate?](FAQ_JOIN_A_REALM.md) —
  the identity layer above this page's realm-agnostic station
- [FAQ: How do I run a local station for dev/testing?](FAQ_RUN_A_LOCAL_STATION.md) —
  a lighter-weight alternative to this page's production cert dance
- [FAQ: How do I debug a service that won't show up on the mesh?](FAQ_DEBUG_MESH_DISCOVERY.md) —
  troubleshooting once a station and a service are both actually running
