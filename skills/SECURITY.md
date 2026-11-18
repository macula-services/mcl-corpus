---
title: Security
layer: skill
audience: [agent, human]
stage: stable
---

# SECURITY.md: Security

*Keep secrets out of the transcript, and security changes out of the live box.*

---

## Secrets stay out of the transcript

### Never echo a secret value

When a command's output contains a credential, redact it. Name the location and the shape (a token, a key), never the value. When searching for a leak, use paths and counts and generic prefixes, never the value itself as the match string. The transcript is itself a place a secret can leak. When a credential is found, say where it is and what it protects, and flag the blast radius before urging rotation.

**Why:** the leak is the echo, not the file; a token printed into a conversation has already left the machine, and the owner may not know everything that depends on it.

### Grep names, not matching lines

When the question is "which variable is set," ask for the names only. A pattern that matches whole lines prints the value too. Strip values before they can appear: cut the line at the first separator, or match the name shape only.

**Why:** a command shaped to answer a metadata question is also built to print the payload, and the payload is the secret.

### Never dump a full environment

Never list a host's or container's full environment, even filtered with a pattern. The filter is a pattern, and a pattern lets a value through. Read one named key at a time. To learn whether a secret is set, test for its presence, never print it.

**Why:** a full environment is full of secrets, and a filter only narrows; it does not redact.

### Never run a command whose output can carry a credential unmasked

Commands such as listing remote URLs, printing the environment, or reading config and secret files can carry a live credential in their output. Prefer the safe variant (names only), and pipe anything else through a redactor. A token embedded in a remote URL is an antipattern; use a credential helper instead.

**Why:** unmasked credential output leaks into the transcript and its local logs, and a token that leaks has already reached places rotation cannot recall.

### Never delete the user's credential file after using it

"Use this token" is not "delete this token when you are done." Using a secret someone pointed you at grants exactly that: use it, do not print or log the value, and do not remove, rotate, or otherwise mutate the credential or its storage afterward. Clean up only files you created yourself for the task; a file the user already had is theirs.

**Why:** the instruction was scoped to not disclosing the value, and deleting it can lock the owner out with no recovery.

## Security before code

### A security feature starts with a written threat model

A security feature (integrity, sealing, auth, anything an attacker targets) starts with a short written threat model: what an actor with stated access can and cannot do afterward, and the named residuals. It is reviewed once. Only then does code follow, and the review rounds test the code against that model. A design that cannot pass in two rounds is questioned, not patched a third time.

**Why:** designing by being attacked costs round after round; the model names the actor and the residuals up front.

### Write security findings in defensive terms

Write findings, ratings and fix designs as the invariant that must hold, the limit, the fix, and the regression test. One line each for capability, precondition, exposure and severity. Keep step-by-step attack mechanics and payload recipes out; where a test input is needed, describe the shape the code must refuse, not how to build it.

**Why:** dense attack narration is read as an attack, and it is the one thing that can block a defensive review; the invariant is what the reader actually needs.

### Security must never cause downtime

A service whose credential expires and stops being advertised is a bug in the renewal path, not an operations chore. Treat any expiry-driven outage as a source bug: fix it with automatic renewal well before expiry and an early warning, and no human act in the normal path.

**Why:** security that takes the system down reads as downtime, and a manual renewal makes a recurring human act out of a bug.

## Where the agent's hand stops

### No direct edits on a production box

All infrastructure changes flow through git, then CI, then deploy. The box is read-only output, never an input; even a one-line tweak goes through the repo. Diagnose by reading, never edit a config or stack in place. If a box is found with uncommitted state, capture the diff back to git first, and check that the box is actually covered by whatever applies the change.

**Why:** an edit made on the box is unreproducible from git, and an untracked or uncovered box is where correct history silently diverges from what is running.

### A refused credential probe has no gentler form

A task that enumerates secret files and then authenticates with each one is refused on the action itself, and no command shape makes it not that. Do not reshape it and do not hand it to a peer; put the prepared command in front of the owner to run themselves. When a block is on the shape instead (a script that names a secret, a script that pushes, a bundled command), run the narrow command openly so the check sees what runs; if that is stopped too, it goes to the owner; never reshape to hide what runs.

**Why:** a block on the action cannot be cleared by re-wording, and asking another session to run what yours refused is laundering the refusal.
