#!/bin/sh
# arm, check or disarm the corpus guard in the clone this runs in.
#
#   install.sh            arm: a commit in this clone is refused by name
#   install.sh --check    one ok/FAIL shared-clone-commit line per property; exit 1 on a FAIL
#   install.sh --off      disarm
#
# The guard is the tracked pre-commit hook next to this script, armed by two local config
# keys. A fresh clone, a fork and CI stay unarmed until someone runs this. The hook refuses
# only a commit made in the clone's own checkout; a linked worktree of the same clone is
# allowed by design, and --check says so.

set -u

GUARD_DIR=tools/corpus-guard
GUARD_NAME=shared-clone-commit

top=$(git rev-parse --show-toplevel 2>/dev/null) || {
  printf 'FAIL %s: not inside a git checkout\n' "$GUARD_NAME" >&2
  exit 1
}
git_dir=$(git rev-parse --absolute-git-dir)
in_worktree=0
[ -f "$git_dir/commondir" ] && in_worktree=1

# The hook git will run is what core.hooksPath resolves to. A relative hooksPath is resolved
# against the working tree's top level, because that is the directory git runs hooks from.
hook_in_play() {
  hooks_path=$(git config --local --get core.hooksPath 2>/dev/null) || return 1
  [ -n "$hooks_path" ] || return 1
  case $hooks_path in
    /*) printf '%s/pre-commit\n' "$hooks_path" ;;
    *) printf '%s/%s/pre-commit\n' "$top" "$hooks_path" ;;
  esac
}

armed() { [ "$(git config --local --get corpus.shared-clone 2>/dev/null)" = "true" ]; }

check() {
  failed=0
  fail() { printf 'FAIL %s: %s\n' "$GUARD_NAME" "$1" >&2; failed=1; }
  ok() { printf 'ok %s: %s\n' "$GUARD_NAME" "$1"; }

  if [ "$in_worktree" -eq 1 ]; then
    # Linked worktrees share the clone's config, so the declaration is readable from here.
    if armed; then
      ok 'linked worktree, which the guard allows by design, in a clone that declares itself shared'
    else
      fail 'the clone that owns this worktree does not declare itself shared: run tools/corpus-guard/install.sh once in the clone'
    fi
    [ "$failed" -eq 0 ] || exit 1
    return 0
  fi

  if armed; then
    ok 'the clone declares itself shared (corpus.shared-clone=true)'
  else
    fail 'the clone does not declare itself shared (corpus.shared-clone is not true), so a commit here is allowed'
  fi

  hook=$(hook_in_play) || hook=
  if [ -n "$hook" ]; then
    if [ -x "$hook" ]; then
      ok "core.hooksPath resolves to an executable hook ($hook)"
    else
      fail "core.hooksPath names $hook, which is missing or not executable"
    fi
    if cmp -s "$hook" "$top/$GUARD_DIR/pre-commit"; then
      ok "the hook git will run is the tracked $GUARD_DIR/pre-commit"
    else
      fail "the hook git will run is not the tracked $GUARD_DIR/pre-commit: run $GUARD_DIR/install.sh"
    fi
  else
    fail 'core.hooksPath is not set, so no hook runs at all: run tools/corpus-guard/install.sh'
  fi

  if armed && [ -n "$hook" ] && [ -x "$hook" ]; then
    if "$hook" >/dev/null 2>&1; then
      fail 'the hook allowed a commit in the shared clone: it fails open and needs a fix'
    else
      ok 'the hook refuses a commit in this clone'
    fi
  fi

  [ "$failed" -eq 0 ] || exit 1
}

case ${1:-install} in
  install)
    git config --local corpus.shared-clone true
    git config --local core.hooksPath "$GUARD_DIR"
    printf 'armed corpus.shared-clone=true and core.hooksPath=%s in %s\n' "$GUARD_DIR" "$top"
    check
    ;;
  --check | check)
    check
    ;;
  --off | off)
    git config --local --unset corpus.shared-clone 2>/dev/null || true
    git config --local --unset core.hooksPath 2>/dev/null || true
    printf 'disarmed: a commit in %s is allowed again\n' "$top"
    ;;
  *)
    printf 'usage: %s [install|--check|--off]\n' "$0" >&2
    exit 2
    ;;
esac
