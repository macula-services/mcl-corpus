---
title: "FAQ: Deploying Your Own Macula Service"
layer: guide
audience: [agent, human]
stage: stable
---

# FAQ: How Do I Deploy My Own Macula Service?

[Back to FAQ index](FAQ.md) · [Back to corpus index](../INDEX.md)

This is the path from "my new service passes `rebar3 eunit` locally" to
"it's running and answering mesh calls." It assumes you've already built
the service — see
[FAQ: Developing Edge Services in BEAM Languages](FAQ_DEVELOP_EDGE_SERVICES_BEAM.md)
for that part.

---

## 1. Scaffold

```bash
rebar3 new mcl_service repo=mcl-foo name=mcl_foo desc="Does X over the mesh" health_port=8484
```

This is the real, currently-used template (`macula-services/mcl-om`'s
`priv/templates/mcl_service*`, installed into
`~/.config/rebar3/templates/` by that repo's own
`scripts/install-templates.sh`).

Key variables: `repo` (kebab-case — becomes the image name and mesh
identity), `name` (snake_case — the OTP app), `desc`, `org` (default
`macula-services`), `registry` (default `ghcr.io`), `health_port`
(default 8484 — **pick one actually free across every fleet node you'll
deploy to**; a collision is a silent host-network bind failure, not an
error you'll see immediately), `store` (opt-in reckon-db backing —
must be exactly one character, a real limitation of the template's own
mustache string-iteration).

Generated: `rebar.config`, the OTP app (including
`<name>_service.erl` implementing `mcl_om_service` —
see the BEAM FAQ), `sys.config.src`, `vm.args.src`, a `Containerfile`,
`.github/workflows/{build-push,lint}.yml`, `deploy/docker-compose.yml`,
`scripts/health.sh`, and the usual README/CHANGELOG/LICENSE.

## 2. Write it, test it, push it

`rebar3 eunit` green locally, then push to GitHub. The generated
`build-push.yml` triggers on push to `main` and on `v*` tags, builds via
`docker/build-push-action@v6`, and pushes to
`ghcr.io/<org>/<repo>` as `:latest` (every `main` push) and as the
matching semver tag (on a `v*` tag push) — the ":latest for
watchtower/auto-update, semver for rollback" convention this workspace
uses everywhere.

## 3. Declare it on a target node — beam00-03 (Docker + watchtower)

The fleet's real GitOps source of truth is
[`macula-io/macula-demo`](https://github.com/macula-io/macula-demo)'s
`infrastructure/` directory. A currently-live example
(`mcl-turn-credentials`, added 2026-08-28) shows the exact shape:

**`infrastructure/scripts/docker-compose.<name>.yml`** — despite living
in a directory literally called `scripts`, this is a real compose file.
Required env vars use `:?` so a missing one fails loudly rather than
silently deploying with an empty value:
```yaml
services:
  mcl-turn-credentials:
    image: ghcr.io/macula-services/mcl-turn-credentials:latest
    network_mode: host
    labels:
      - "com.centurylinklabs.watchtower.enable=true"
    environment:
      - MCL_REALM=${MCL_REALM:?set MCL_REALM}
      - TURN_SHARED_SECRET=${TURN_SHARED_SECRET:?set TURN_SHARED_SECRET}
      - MACULA_STATION_SEEDS=${MACULA_STATION_SEEDS:-https://station-de-frankfurt.macula.io:4433,https://station-de-nuremberg.macula.io:4433,https://station-de-falkenstein.macula.io:4433}
      - MCL_HEALTH_PORT=${MCL_HEALTH_PORT:-8494}
```
⚠ Always run this with an explicit project name
(`docker compose -p mcl-turn-credentials -f ...`) — otherwise Compose
adopts the containing directory's name (`scripts`) as the project name,
and later commands won't find the running container.

**`infrastructure/<node>.lab/<name>-config.env`** — committed,
**non-secret** config only (station seeds, etc.) plus a comment on why
this node was chosen.

**`infrastructure/<node>.lab/reconcile.manifest`** — one line per
deployed service, whitespace-separated:
```
<project>  <compose-file-relative>  <config-env-relative-or-->  <secret-filename-or-->  <prep-script-relative-or-->
```
Example, the real live line: `mcl-turn-credentials
scripts/docker-compose.mcl-turn-credentials.yml
beam00.lab/mcl-turn-credentials-config.env
mcl-turn-credentials.env  -`

**Adding a new service is exactly this**: add one manifest line (plus the
compose file and config-env file if new), commit, push. The node's
`mcl-reconcile.timer` polls every 2 minutes
(`OnBootSec=1min`, `OnUnitActiveSec=2min` — confirmed from the real
systemd timer unit, not "a few minutes" as looser docs sometimes say),
`git pull --ff-only`s the infrastructure repo, and applies every
manifest line via `docker compose -p <project> -f <compose>
[--env-file <config-env>] [--env-file secrets/<secret>] up -d --remove-orphans`.
Idempotent — re-running with nothing changed is a no-op.

**Secrets** (if any) are seeded once, out-of-band, at
`~/.mcl/secrets/<name>.env` on the target node, mode `0600` — never
through git, on either deployment path. The reconciler/timer never
automates this step itself; some services have a one-off `scripts/enroll-<name>-secret.sh`
helper a human runs by hand once per node (`mcl-turn-credentials`'s
real one pulls its shared secret from `turn.macula.io` over SSH+sudo,
stages it through a shredded temp file, writes the target's `.env` — read
it directly before assuming yours needs the same shape), others just get
the file written by hand with no script at all. Either way, nothing
resembling this runs automatically on a schedule.

## 4. Declare it on a target node — msi00.lab (Podman + Quadlet)

msi00.lab is separate from the beam00-03 fleet and uses Podman Quadlet
instead of Docker Compose — **never put watchtower here**, it fights
Quadlet/systemd for control of the same container. A real, current
example (trimmed — the actual unit also has a `[Unit]` section, a
`ContainerName`, several more `Environment=` lines, and restart/resource
limits), `mcl-whiteboard.container`:

```ini
[Container]
Image=ghcr.io/macula-services/mcl-whiteboard:latest
AutoUpdate=registry
EnvironmentFile=%h/.mcl/secrets/mcl-whiteboard.env
Network=host
Volume=%h/.mcl/mcl-whiteboard:/data

[Service]
Restart=always

[Install]
WantedBy=default.target
```

`AutoUpdate=registry` is Podman's own native mechanism (driven by
`podman-auto-update.timer`) — no watchtower needed or wanted.

**How a unit gets installed on msi00.lab:** `mcl-reconciler.service`
(a `systemd --user` unit) watches `~/.mcl/gitops/apps/` and symlinks
each `.container` file it finds into `~/.config/containers/systemd/`.
`mcl-whiteboard` and `mcl-graph` are installed
that way; `mcl-embedder` is a plain file dropped into the systemd
directory by hand. Either way the unit ends up in the same directory and
`systemctl --user daemon-reload && systemctl --user start <name>` brings
it up.

**How fast a new image lands:** `podman-auto-update.timer` fires every
five minutes, not the package default of daily. A drop-in at
`~/.config/systemd/user/podman-auto-update.timer.d/cadence.conf` resets
`OnCalendar=` and then sets `OnCalendar=*:0/5` — the empty reset line is
load-bearing, since systemd accumulates timer settings across drop-ins
rather than replacing them. `systemctl --user list-timers
podman-auto-update.timer` on the box shows the five-minute cadence.

## 5. Verify it's actually running and healthy

The scaffold's own `scripts/health.sh` is the standard check:
```bash
MCL_HEALTH_PORT=<port> scripts/health.sh <remote-host>
```

Beyond HTTP health: `docker logs <name>` (beam00-03) or
`podman logs <name>` (msi00.lab) for the container itself;
`journalctl --user -u mcl-reconcile.service` on a beam node for
reconcile-level problems (a stale/untracked file blocking `git pull`
used to silently stall reconciliation for *every* stack on that node —
fixed 2026-08-31 to actually surface why, but worth knowing the failure
mode existed). Once healthy, confirm the mesh side too — the service
should show up in `mesh_find_records_by_type` (`procedure_advertisement`)
for whatever capability it declared; see
[FAQ: How do I run macula-cli?](FAQ_MACULA_CLI.md)'s `dht
find-records-by-type` command, or
[FAQ: How do I run macula-mcp?](FAQ_MACULA_MCP.md)'s `mesh_find_records_by_type`
tool.

## See also

- [FAQ: Developing Edge Services in BEAM Languages](FAQ_DEVELOP_EDGE_SERVICES_BEAM.md)
- [FAQ: How do I add event sourcing to a new mcl-* service?](FAQ_ADD_EVENT_SOURCING.md) — what the scaffold's `store=1` option actually turns on
- [FAQ: How do I join the Mesh?](FAQ_JOIN_THE_MESH.md) — running a station, not a service
- [FAQ: How do I join a realm and get my service an identity/certificate?](FAQ_JOIN_A_REALM.md) — where the cert this page mounts into the container actually comes from
