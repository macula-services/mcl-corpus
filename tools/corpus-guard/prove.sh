#!/bin/sh
# prove the corpus guard: build a planted world, then require each behaviour.
#
#   an armed clone refuses a commit, and the refusal names itself and the staged path
#   a linked worktree of that clone commits
#   a clone with the same hook but no declaration commits (only the marker differs)
#   --check fails by name on an unarmed clone and passes on an armed one
#   --off disarms
#   a hook with its worktree test removed refuses the worktree, so the worktree case pins it
#
# Nothing here touches the real repository, the operator's git config or the network: the
# world is a scratch directory, removed on exit, and every git command runs with no global
# config and an identity that exists only inside it.

set -u

here=$(cd "$(dirname "$0")" && pwd -P)

root=$(mktemp -d "${TMPDIR:-/tmp}/corpus-guard-prove.XXXXXX")
trap 'rm -rf "$root"' EXIT HUP INT TERM

export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null
export GIT_AUTHOR_NAME=prove GIT_AUTHOR_EMAIL=prove@localhost
export GIT_COMMITTER_NAME=prove GIT_COMMITTER_EMAIL=prove@localhost

fails=0
ok()   { printf 'ok    %s\n' "$*"; }
fail() { printf 'FAIL  %s\n' "$*"; fails=$((fails + 1)); }
said() { head -2 "$1" 2>/dev/null | tr '\n' ' '; }

new_clone() { # new_clone <dir>: a clone on main carrying the guard and two lesson files
  git init -q --initial-branch=main "$1"
  mkdir -p "$1/tools/corpus-guard" "$1/skills"
  cp "$here/pre-commit" "$here/install.sh" "$1/tools/corpus-guard/"
  chmod +x "$1/tools/corpus-guard/pre-commit" "$1/tools/corpus-guard/install.sh"
  printf 'seed\n' > "$1/skills/REVIEW.md"
  printf 'seed\n' > "$1/skills/SHELL.md"
  ( cd "$1" && git add -A && git commit -qm seed )
}

try_commit() { # try_commit <dir> <path> <message>: stage one path and commit; stderr in $root/err
  ( cd "$1" && printf 'a lesson\n' >> "$2" && git add -- "$2" && git commit -qm "$3" ) 2> "$root/err"
}

GUARD=tools/corpus-guard/install.sh

# --- an armed clone refuses a commit --------------------------------------
armed=$root/armed
new_clone "$armed"
if ( cd "$armed" && ./$GUARD ) > "$root/install.out" 2>&1; then
  ok 'install.sh arms a clone'
else
  fail "install.sh failed in a planted clone: $(said "$root/install.out")"
fi

if try_commit "$armed" skills/REVIEW.md 'a lesson'; then
  fail 'an armed clone committed: the guard did not run'
elif grep -q 'FAIL shared-clone-commit' "$root/err" && grep -q 'skills/REVIEW.md' "$root/err"; then
  ok 'an armed clone refuses the commit, naming itself and the staged path'
else
  fail "the refusal does not name itself and the staged path: $(said "$root/err")"
fi
# The refusal leaves the index alone, so clear only the path it names.
( cd "$armed" && git restore --staged -- skills/REVIEW.md && git checkout -- skills/REVIEW.md ) >/dev/null 2>&1 ||
  fail 'could not put back down the staged path the refusal named'

# --- a worktree of that clone commits -------------------------------------
wt=$root/armed-worktree
if ( cd "$armed" && git worktree add -q "$wt" -b a-member/lesson main ) 2> "$root/err"; then
  if try_commit "$wt" skills/SHELL.md 'a lesson from a worktree'; then
    ok 'a linked worktree of the armed clone commits'
  else
    fail "a linked worktree was refused as well: $(said "$root/err")"
  fi
else
  fail "could not create a worktree of the planted clone: $(said "$root/err")"
fi

# --- the same hook, with the declaration off, allows ----------------------
undeclared=$root/undeclared
new_clone "$undeclared"
( cd "$undeclared" && git config --local core.hooksPath "$(dirname "$GUARD")" ) ||
  fail 'could not set core.hooksPath in the planted clone'
if try_commit "$undeclared" skills/REVIEW.md 'a lesson in a clone that never declared itself shared'; then
  ok 'a clone with the hook but no declaration commits: only the marker decides'
else
  fail "a clone that never declared itself shared was refused: $(said "$root/err")"
fi

# --- --check names what is wrong ------------------------------------------
if ( cd "$undeclared" && ./$GUARD --check ) > "$root/check-unarmed.out" 2>&1; then
  fail '--check passed in an unarmed clone'
elif grep -q 'FAIL shared-clone-commit' "$root/check-unarmed.out"; then
  ok '--check fails by name in an unarmed clone'
else
  fail "--check failed without naming itself: $(said "$root/check-unarmed.out")"
fi

if ( cd "$armed" && ./$GUARD --check ) > "$root/check-armed.out" 2>&1; then
  ok '--check passes in an armed clone'
else
  fail "--check failed in an armed clone: $(grep '^FAIL' "$root/check-armed.out" | head -2 | tr '\n' ' ')"
fi

# --- --off disarms --------------------------------------------------------
( cd "$armed" && ./$GUARD --off ) >/dev/null 2>&1 || fail '--off failed'
if try_commit "$armed" skills/SHELL.md 'a lesson after --off'; then
  ok '--off disarms the clone'
else
  fail '--off left the guard armed'
fi

# --- the mutant: the worktree test is what the worktree case pins ---------
mutant=$root/mutant
new_clone "$mutant"
sed '/commondir/d' "$here/pre-commit" > "$mutant/tools/corpus-guard/pre-commit"
chmod +x "$mutant/tools/corpus-guard/pre-commit"
( cd "$mutant" && git add -A && git commit -qm 'plant a hook without its worktree test' ) >/dev/null 2>&1 ||
  fail 'could not commit the planted hook in the mutant clone'
( cd "$mutant" && ./$GUARD ) >/dev/null 2>&1 || fail 'install.sh failed in the mutant clone'
mwt=$root/mutant-worktree
( cd "$mutant" && git worktree add -q "$mwt" -b a-member/mutant main ) 2> "$root/err" ||
  fail "could not create the mutant worktree: $(said "$root/err")"
if try_commit "$mwt" skills/REVIEW.md 'a lesson'; then
  fail 'a hook with its worktree test removed still allowed the worktree: the worktree case pins nothing'
else
  ok 'a hook with its worktree test removed refuses the worktree, so that case pins the test'
fi

echo
if [ "$fails" -eq 0 ]; then
  echo 'ALL PROVED: the shared clone refuses, a worktree commits, --check names a fault, --off disarms'
  exit 0
fi
echo "REFUSED: $fails check(s) failed" >&2
exit 1
