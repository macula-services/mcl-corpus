---
title: The Dependency Model
layer: philosophy
audience: [agent, human]
stage: stable
---

# The Dependency Model

*This exists so an agent about to bump, pin or release a library knows the ecosystem's dependency rules before it breaks one.*

This page holds the model only. Which repository depends on which, at which
version, is generated rather than written down: see the dependency register,
[macula-ecosystem#5](https://github.com/macula-io/macula-ecosystem/issues/5).
Do not copy its data here; a hand-kept table drifts from the code
([Demon 74](../skills/antipatterns/documentation.md)).

---

## 1. Layers, and dependencies point down

| Layer | What lives there |
|-------|------------------|
| SDK | `macula` |
| Infrastructure | `macula-station`, `macula-realm` |
| Service base | `mcl_om` |
| Services and clients | `mcl-*` services, CLIs, apps, sites |

A repository depends only on layers below its own: infrastructure never
depends on the service base, and the SDK depends on nothing above it.

The reckon stack (`reckon_gater`, `reckon_db`, `evoq`, `reckon_evoq`) is a
graph of its own, with its own order. Its map lives in
[reckon-ecosystem](https://github.com/reckon-db-org/reckon-ecosystem).

## 2. Change order

1. The BEAM SDK (`macula`).
2. The SDKs in other languages, against the same wire.
3. Infrastructure and the service base.
4. Services and clients.

An SDK release is not finished when it is tagged. Everything downstream is
rebuilt against it, and a consumer that does not rebuild is still running the
old SDK, whatever its constraint allows.

## 3. Released versions only

Every tagged or deployed binary builds against versions released to a
registry (hex, crates, npm, PyPI, NuGet, Go modules). No git branch, commit or
path dependency, in any language, with the one exception below. A local override for development
(`_checkouts`, a path dep) stays out of the commit, and a build that still
links one is not evidence about the released code.

If a fix is needed downstream, release it upstream first.

A registry is for libraries in its own language. Two other kinds of input
have no release there: a contract written in another language (a `.proto`
set), and a build-time tool such as a code-generation plugin. When one feeds
only a single image's build, it may be pinned by the full commit of a release
tag, never by a branch or tag name (reckon-gateway#4). Libraries stay
registry-only.

## 4. Pinning: `~> MAJOR.MINOR`

Libraries float on `~> MAJOR.MINOR`, so a compatible release reaches every
consumer at its next build without a commit per consumer. Exact pins block
coordinated releases.

Below 1.0.0 the operator reaches further than it looks:

| Constraint | Accepts |
|------------|---------|
| `~> 0.34` | `>= 0.34.0 and < 1.0.0`: it floats to 0.35, 0.36, ... |
| `~> 0.34.0` | `>= 0.34.0 and < 0.35.0` |
| `~> 1.2` | `>= 1.2.0 and < 2.0.0` |

So in 0.x a minor release is a breaking release for every two-part floater.
Before tagging a breaking 0.x minor, count the consumers that float on it and
decide whether they move with you or need a three-part pin first.

## 5. Consumers, not definitions

Before changing a contract (a function, a record, a wire field, a procedure
name), grep every consumer, in every language, not only the module that
declares it. The declaration tells you what you meant; the consumers tell you
what you will break. The register lists who consumes what; the grep shows how.

## 6. One version per release

The tag, the application vsn (`.app.src`, `mix.exs`, `Cargo.toml`, ...) and
the release name (relx) agree. `v1.4.0` ships an application that reports
1.4.0, in a release called by that version. The release guard in CI
(macula-ci-images#5, #6) refuses a tag where they differ; bump all of them
in the release commit, before the tag
([Demon 30](../skills/antipatterns/release.md)).

---

## When in doubt

- Which way does this dependency point? Down, or it is wrong.
- Is everything it builds against released? If not, release first.
- Who else floats on the version I am about to tag? Count them.
- Did I grep the consumers, or only read the definition?
