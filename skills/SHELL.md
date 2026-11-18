---
title: Shell
layer: skill
audience: [agent, human]
stage: stable
---

# SHELL.md: Shell

*The shell mangles what you hand it in ways that read as a clean result.*

---

## Quoting and word-splitting

### An unquoted variable stays one word

This shell does not word-split an unquoted variable the way other shells do, so a variable holding several paths arrives as one path. A comparison over a list then compares nothing and reads every branch as identical.

**Why:** the command exits clean, and "all identical" is the cheapest false result to accept, so treat it as suspect until a planted difference reads non-identical.

### Brace a variable next to a colon

A variable immediately before a colon followed by a letter can be read as a history modifier, silently rewriting the argument. Brace it: `${var}:rest`. The same trap bites a push refspec, where the mangled target reads as a missing branch rather than a quoting fault.

**Why:** the wrong expansion runs against the wrong object and often produces no obvious error.

## Aliases and shims

### A core utility may be aliased; check and use the real one

The shell may alias common tools: a grep that skips ignored files, a cut that is a different program, a listing that decorates each entry. Before relying on one in a script or a background loop, check what the name resolves to, and use the real binary or an explicit path.

**Why:** a search over a dependency tree that skips ignored files reports absence where the real tool finds the file, and the wrong result carries no warning.

### A broken wrapper looks like "no match"

A tool may be a shell function that calls a wrapper binary. When that wrapper is broken, every call returns nothing and exits as if the string is absent, indistinguishable from a genuine no-match. Confirm with the real binary before concluding a file lacks a string or a log lacks a line.

**Why:** a wait loop grepping for a summary line then never matches and looks like a hung suite, when the real grep would have matched.

### Never build a path from a listing command's output

A decorated listing prefixes each entry with a glyph even inside command substitution, so a path built from it is wrong and every command using it fails. Build paths from known names, a glob or find.

**Why:** the failure appears as a "no such file" on a path that looks right, and it is the listing, not the path, that is wrong.

## Exit codes and pipes

### Measure an exit code unpiped

An exit code read after a pipe is the last command's, not the one you meant. Run the command to a file, then read the status.

**Why:** a command that actually fails can be recorded as passing, and the false claim ships a gate that goes red on the next real run.

### Under pipefail, do not pipe a producer into a truncator

When a script aborts on a failed pipeline, piping a streaming producer into a reader that closes early, such as a head with a byte count, sends the producer a broken pipe and aborts the script. Capture the full output first, then truncate.

**Why:** the truncator closing early kills the producer, so the pipeline fails for a reason that has nothing to do with the data.

## stdin in heredocs

### Give every stdin reader its own input

In a script fed to the shell on stdin, any command that reads stdin without its own input consumes the rest of the script as data. The later commands land in a file and never run, and the call completes with no output.

**Why:** the failure is silent; a planned write, commit or check simply does not happen.

### A remote script piped over ssh with -n runs empty

An ssh that redirects stdin from the null device, combined with a remote shell that reads the script from stdin, runs an empty script and exits clean. A remote check that returns clean but silent is a stdin problem before it is a box problem.

**Why:** the clean exit and no output read as "the check passed" rather than "the check never ran".

## Matching processes

### Match the executable, not the full command line

A process match on the full command line can match the shell running the match itself, so a wait loop sees itself and never fires, and a busy check refuses on its own text. Match the executable path, or a sentinel the waiter cannot contain.

**Why:** the same pattern gives opposite symptoms in two places, both from matching the thing doing the matching.

## Rendering and environment

### Check raw bytes before trusting a diagnostic dump

A diagnostic dump can mangle multi-byte characters in its own rendering, showing escape-looking sequences where the file holds normal bytes. Before concluding a file is corrupted, check the raw bytes directly.

**Why:** the file was never wrong, and the dump's rendering costs real debugging time the way a real corruption would.

### A version-manager shim rewrites PATH

A version manager's shim prepends its own directory to the path, so a program launched through it resolves different binaries than the shell that launched it. In any probe that depends on path order, launch through the real interpreter, not the shim, and keep the path short and explicit.

**Why:** the shell finds one binary and the program another, so a version drift never prints and the guide looks wrong.

## Messages and runners

### Do not type markup into an inline commit message

The shell runs backticks, dollar signs and exclamation marks in an inline message as substitution, silently deleting the words. Write any message with markup to a file and commit from the file, with the heredoc quoted.

**Why:** the words vanish from the message and the command-not-found noise is buried in the output, leaving a nonsense line.

### Never hand a possibly-empty argument list to a test runner

A test runner given an empty argument may treat it as a pattern and run every test file it can find. Build the flag list in a real script with a guard, echo the full argument list and confirm it names exactly what you mean before the run.

**Why:** a runner aimed at one file becomes a machine-wide run, and an empty array is the cause, invisible in the command line.
