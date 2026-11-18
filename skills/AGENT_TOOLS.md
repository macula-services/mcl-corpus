---
title: Agent Tools
layer: skill
audience: [agent, human]
stage: stable
---

# AGENT_TOOLS.md: Agent tools and their host

*A session that lost its tools needs a fresh start, and the transcript says when it happened.*

---

An agent session's tools come from its host: configured when the process starts, read once, and withdrawn when the host's configuration changes underneath it. The rules below are how to tell whether a session still holds its tools, and what to do when it does not.

## When tools disappear mid-session

### Two extensions of the same kind displace each other

When two extensions register their tools the same way, a host that keeps one server per extension kind keeps one of them, and the other's tools vanish while the session carries on. Check the host's session record for the withdrawal, turn off whichever of the two the work does not need, and start a fresh session.

**Why:** the losing extension leaves the configuration rather than failing, so nothing reports an error. The tools are simply gone, and a dashboard or a workflow the session drives keeps running without them, drawing whatever it can from stale files.

### A host records the tools it withdrew in the session transcript

When tools are withdrawn or returned, the host writes a record into the session transcript naming the tools removed or added, the cause, and any server that failed or is still pending. Read that record from outside the session to decide whether a session still holds its tools.

**Why:** the one thing a session cannot check is its own hold on its tools, so its own account of them is the claim under test, not the evidence.

### A resumed session does not get its tools back

A session restored from its saved conversation, or refreshed in place, keeps the configuration its process read when it started. After a change to the host's configuration, start a new process: the tools are read at start, and a resume does not read them again.

**Why:** settings are read once per process, so a session that restored instead of starting fresh can hold the old tool set while every file on disk says otherwise, and an in-place refresh is not the fix a restart is.

## A message store the reader cannot open is not a delivery path

A handoff left in a message store the recipient's client cannot open — an oversized mailbox, a full disk, an index it refuses to load — is indistinguishable, from the sender's side, from one that was delivered. The sender waits on an answer nobody knows was asked for, and the dashboard shows a package waiting on a person who was never asked.

**Why:** the failure is silent and it is at the receiving end, so the sender's own record looks correct: the send succeeded, and only the reader's client knows the message was never readable. A round was lost this way for hours on a package whose work was finished and green.

**How to apply:** send anything that has to move work — a handoff, a verdict, a question — as a direct message to the recipient's session, and treat the store as a record of the exchange rather than the way the exchange happens. When the reply is what you are waiting on, say what you need back in the same message, and if nothing arrives after a plausible interval, re-send by the direct channel rather than assuming it was read. A recipient who reports the store unreadable is telling you the channel, not asking for a resend.
