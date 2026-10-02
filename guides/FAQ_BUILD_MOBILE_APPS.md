---
title: "FAQ: Building Mobile Applications for the Mesh"
layer: guide
audience: [agent, human]
stage: stable
---

# FAQ: How Do I Build Mobile Applications for the Mesh?

[Back to FAQ index](FAQ.md) · [Back to corpus index](../INDEX.md)

Two real apps in this workspace answer this: `macula-apps/macula-cam2me`
(built, both platforms) and `macula-apps/macula-passport` (the domain
core and FFI bindings are built and tested — **no mobile app consumes
them yet**, per its own README status line). Both share the same
architecture: two separate **native** codebases (Kotlin/Android,
Swift/iOS) — deliberately not Flutter, not Kotlin Multiplatform — around
a shared Rust core exposed via [`macula-rust`](https://github.com/macula-io/macula-rust)'s
UniFFI bindings, the same pattern the project compares to `iroh-ffi`'s
example apps.

---

## Structure

```
macula-cam2me/
├── rust/macula-rust-sdk/   # git submodule -> macula-io/macula-rust
├── android/                # Kotlin, Gradle, generated bindings via JNA
├── ios/                    # Swift, XcodeGen, generated bindings via XCFramework
└── scripts/                # cross-compile the Rust core + regenerate bindings, every build
```

Neither app commits FFI-generated code — `scripts/build-rust-{android,ios}.sh`
regenerates the Kotlin/Swift bindings fresh from the pinned Rust submodule
commit on every build. (Note: the submodule/repo was renamed from
`macula-rust-sdk` to `macula-rust` — the rename is done at the repo/git
level, but a few app-facing strings and comments still say the old name;
don't be thrown by that.)

## Build

**Android:**
```bash
rustup target add aarch64-linux-android armv7-linux-androideabi x86_64-linux-android
cargo install cargo-ndk   # NDK r27c
./scripts/build-rust-android.sh
cd android && ./gradlew build   # Java 21, Gradle 9.7.1
```

**iOS:**
```bash
rustup target add aarch64-apple-ios aarch64-apple-ios-sim x86_64-apple-ios
./scripts/build-rust-ios.sh
brew install xcodegen
cd ios && xcodegen generate
open MaculaCam2Me.xcodeproj   # or: xcodebuild ... -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO
```

**Neither side has been verified by a local build on this workspace** —
the repo was scaffolded from a Linux box with no Android SDK/NDK and no
macOS/Xcode available locally. Android follows a standard, trusted Gradle
shape; iOS deliberately goes through XcodeGen's `project.yml` rather than
a hand-authored `.xcodeproj`, specifically because getting that right
blind would be too fragile. Both are verified by CI, not by anyone
running them locally — **check the Actions tab before assuming either
one actually builds.**

## Identity persistence: solved on Android, not yet on iOS

This is the one part of "mobile" that's genuinely different from a
desktop/server SDK consumer: an identity generated fresh every launch
means every restart looks like a new node to the rest of the mesh.

**Android — real, Keystore-backed, with a migration path.** The full file
is 79 lines, not just the `loadOrCreate` function — it also defines the
`KEYSTORE_SERVICE`/`KEYSTORE_ACCOUNT` constants `loadOrCreate` reads, and
the private `migrateFromLegacyDataStore` helper that does the one-time
recovery
(`android/app/src/main/kotlin/io/macula/cam2me/reachability/NodeKeyPair.kt`):

```kotlin
private const val KEYSTORE_SERVICE = "io.macula.cam2me"
private const val KEYSTORE_ACCOUNT = "node_key_pair"

object NodeKeyPair {
    suspend fun loadOrCreate(context: Context): FfiKeyPair {
        try {
            return FfiKeyPair.loadFromKeystore(KEYSTORE_SERVICE, KEYSTORE_ACCOUNT)
        } catch (_: FfiException.KeystoreNotFound) {
            // Nothing in the keystore yet -- either a fresh install, or
            // an install from before this migration that still has its
            // seed in the old plain DataStore.
        }
        val migrated = migrateFromLegacyDataStore(context)
        if (migrated != null) {
            migrated.saveToKeystore(KEYSTORE_SERVICE, KEYSTORE_ACCOUNT)
            return migrated
        }
        val keyPair = FfiKeyPair.generate()
        keyPair.saveToKeystore(KEYSTORE_SERVICE, KEYSTORE_ACCOUNT)
        return keyPair
    }

    // One-time recovery of a seed persisted the old way (plain,
    // unencrypted DataStore) before the keystore migration existed.
    // Returns null once already migrated -- the DataStore value is
    // cleared on migration, so this path is only ever taken once.
    private suspend fun migrateFromLegacyDataStore(context: Context): FfiKeyPair? {
        val seedB64 = context.nodeKeyPairDataStore.data.first()[SEED_KEY] ?: return null
        val keyPair = FfiKeyPair.fromSeedBytes(Base64.decode(seedB64, Base64.NO_WRAP))
        context.nodeKeyPairDataStore.edit { it.remove(SEED_KEY) }
        return keyPair
    }
}
```

`saveToKeystore`/`loadFromKeystore` live on `FfiKeyPair` itself (i.e.
implemented once in the shared Rust/UniFFI layer, Android Keystore-backed
underneath), not hand-rolled per-app crypto. This shipped as a real
migration (`c6fe563`, "Migrate node identity from plain DataStore to
Android Keystore") with a one-time recovery path so pre-migration
installs' node IDs — and their contacts' knowledge of them — survive the
upgrade.

**iOS — still generates a fresh identity every launch.** The entire iOS
source is two files, 43 lines total, and its own doc comment says so
plainly (`ios/MaculaCam2Me/ContentView.swift`):

```swift
/// Skeleton entry point. Proves the FFI wiring end to end -- generating a
/// puzzle-hardened Ed25519 identity via `FfiKeyPair` and rendering its
/// node_id -- without yet touching the mesh (no connect/advertise/stream
/// here). Camera capture and a real mesh session are the next feature
/// pass, not this one. Mirrors the Android skeleton's MainActivity
/// exactly in scope.
struct ContentView: View {
    private let nodeIdHex: String
    init() {
        let identity = FfiKeyPair.generate()
        nodeIdHex = identity.nodeId().map { String(format: "%02x", $0) }.joined()
    }
}
```

No `Keychain` import anywhere in the file, no persistence call at all —
every launch mints a brand new identity via `FfiKeyPair.generate()`. If
you're building the
iOS side of a real mesh-connected app, this is the first gap to close —
mirror the Android pattern above using iOS Keychain instead of Android
Keystore (`FfiKeyPair` already has the save/load methods; iOS just isn't
calling them yet).

## What actually touches the mesh, beyond identity

Android's `StationDiscovery.kt`/`MeshSessionPool.kt` auto-connects to the
3 nearest stations via `mcl_stations.list_stations` — real, live code,
larger than the identity snippet above; read it directly in the repo for
the full pattern rather than a partial quote here.

## Gotchas — mostly undocumented, one real one visible in the code

Nothing in this project's README or source discusses App Store/Play
Store review implications, background-mode entitlements, or battery
impact for a P2P mesh connection. That's not an oversight this FAQ can
paper over — it's genuinely unaddressed.

One concrete fact **is** visible in the code, not just absent from docs:
every mesh session and the presence heartbeat are launched via
`activity.lifecycleScope` (`MainActivity.kt`, several call sites) — tied
to the Activity's lifecycle, not a foreground `Service` or `WorkManager`
job. **Mesh connectivity is foreground-only today.** There is currently
no mechanism to keep a session or presence heartbeat alive once the app
leaves the foreground on either platform. If your app needs
background/backgrounded mesh presence, that's real work still to do, not
a flag to flip.

## See also

- [FAQ: Developing Edge Services in Rust](FAQ_DEVELOP_EDGE_SERVICES_RUST.md) — `macula-rust`'s own (non-mobile) API, what the FFI bindings wrap
- [FAQ: Connecting Blazor to the Mesh](FAQ_CONNECT_BLAZOR.md) — the same sandboxed-runtime constraint shows up again for Blazor WebAssembly, for the same underlying reason
