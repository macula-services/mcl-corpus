---
title: Erlang Umbrella Project Layout
layer: codegen
audience: [codegen]
stage: stable
---

# CODEGEN_ERLANG_UMBRELLA.md — Erlang Umbrella Project Layout

_Correct directory structure for Erlang/OTP umbrella applications._

**Target:** Erlang/OTP with rebar3

**Related files:**
- [CODEGEN_ERLANG_CHECKLISTS.md](CODEGEN_ERLANG_CHECKLISTS.md) — Generation checklists
- [CODEGEN_ERLANG_TEMPLATES.md](CODEGEN_ERLANG_TEMPLATES.md) — Code templates
- [CODEGEN_ERLANG_NAMING.md](CODEGEN_ERLANG_NAMING.md) — Naming conventions

---

## The Rule

In a rebar3 umbrella, the **root project IS the shell application**. It has its own `src/` at the root level. Domain apps live under `apps/`.

**The root application is NOT nested under `apps/`.**

---

## Correct Layout

```
mcl_<svc>/
├── rebar.config              # Umbrella: deps, relx listing all apps
├── config/
│   ├── sys.config
│   └── vm.args
├── src/                      # ROOT APP (shell) — lives at project root
│   ├── mcl_<svc>.app.src
│   ├── mcl_<svc>_app.erl     # Starts cowboy, ensures paths
│   ├── mcl_<svc>_sup.erl     # Supervises plugin infra only
│   ├── mcl_<svc>_paths.erl   # Path resolution
│   └── mcl_<svc>_*.erl       # HTTP infra (health, manifest, api_utils)
├── apps/                     # DOMAIN APPS — only CMD/QRY/PRJ here
│   ├── run_something/        # CMD app
│   │   ├── src/
│   │   ├── include/
│   │   └── test/
│   └── query_something/      # QRY app
│       └── src/
├── priv/
└── test/                     # Root app tests (if any)
```

## Wrong Layout

```
mcl_<svc>/
├── rebar.config
├── apps/
│   ├── mcl_<svc>/            # WRONG — root app nested under apps/
│   │   └── src/
│   ├── run_something/
│   └── query_something/
```

**Why this is wrong:** The root project in a rebar3 umbrella already IS an OTP application. Nesting it under `apps/` creates a redundant wrapper — rebar3 treats both the root and everything under `apps/` as apps. The root app should use its natural `src/` directory.

---

## What Goes Where

### Root App (`src/`)

The shell application. Owns infrastructure that spans all domain apps:

| Module | Purpose |
|--------|---------|
| `*_app.erl` | Application callback — starts cowboy, ensures directory layout |
| `*_sup.erl` | Supervises shell-level workers only |
| `*_paths.erl` | Path resolution (base_dir, sqlite_dir, socket_dir, etc.) |
| `*_api_utils.erl` | Shared HTTP response helpers (json_response, json_error) |
| `*_health_api.erl` | `GET /health` endpoint |
| `*_manifest_api.erl` | `GET /manifest` endpoint |

The root app's cowboy routes reference handler modules from ALL apps (root + domain apps). This is fine — modules are globally visible within a release.

**The root app does NOT supervise domain workers.** Each domain app owns its own supervisor tree.

### CMD App (`apps/run_*/` or `apps/{verb}_{noun}/`)

Owns the write side — commands, events, handlers, process managers, game engines, etc.

- Has its own `_app.erl`, `_sup.erl`, `.app.src`
- Supervises its own workers (e.g. `duel_proc_sup`)
- Starts any infrastructure it needs (pg scope, ReckonDB store)
- Tests live in `apps/run_*/test/`

### QRY App (`apps/query_*/`)

Owns the read side — SQLite store, query handlers, projections.

- Has its own `_app.erl`, `_sup.erl`, `.app.src`
- Supervises its own workers (e.g. `query_*_store`)
- Owns `esqlite` as a dependency in its `.app.src`

---

## `.app.src` Dependencies

```
Root app:
  applications: [kernel, stdlib, crypto, cowboy, run_something, query_something]
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                 External deps                    Domain apps (started first)

CMD app:
  applications: [kernel, stdlib, crypto, query_something]
                                         ^^^^^^^^^^^^^^^^
                                         CMD depends on QRY (records results)

QRY app:
  applications: [kernel, stdlib, esqlite]
                                 ^^^^^^^
                                 Owns the SQLite dependency
```

---

## `rebar.config`

The root `rebar.config` declares ALL external dependencies and lists ALL apps in the release:

```erlang
%% Loose constraints on purpose -- exact pins block coordinated library
%% updates. hex.pm is the authority for the newest line.
{deps, [
    {cowboy,      "~> 2.18"},
    {reckon_db,   "~> 5.11"},
    {evoq,        "~> 1.23"},
    {reckon_evoq, "~> 2.7"},
    {esqlite,     "~> 0.9"}
]}.

{relx, [
    {release, {mcl_<svc>, "0.1.0"}, [
        mcl_<svc>,              %% Root/shell app
        run_something,          %% CMD domain app
        query_something,        %% QRY domain app
        reckon_db, evoq, reckon_evoq,
        sasl
    ]},
    ...
]}.
```

**No `src_dirs` needed** — rebar3 automatically discovers `src/` at root and all apps under `apps/`. Sub-directories within `src/` (desk directories like `start_duel/`, `get_leaderboard/`) are discovered automatically by rebar3 in umbrella apps.

---

## Reference Implementations

| Service | Repo | Root App | Domain Apps |
|--------|------|----------|-------------|
| a division service | `macula-services/mcl-<svc>` | `mcl_<svc>` | `{verb}_{aggregates}` (CMD), `project_<models>` (PRJ), `query_<models>` (QRY) — e.g. `mcl-chess`: `play_games`, `project_games`, `query_games` |

---

_The root project is the shell. Domain apps live under apps/. Never nest the shell under apps/._
