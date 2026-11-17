---
title: Writing
layer: skill
audience: [agent, human]
stage: stable
---

# WRITING.md: Writing

*Plain words, no filler, and a name that says what the thing is.*

---

## Write plain

### No em dashes anywhere

Write in plain, direct human style, with no em dashes, in everything: chat, issues and pull requests, drafted external messages, docs, commit messages, changelogs and comments. Prefer a period, a comma, or a parenthetical. The character is the violation, not the dash: a double hyphen is fine in code and commit prose.

**Why:** the rule already holds for chat and generalizes to everything the team produces; a stray em dash reads as filler and stands out in history.

### State the point, drop the justification clause

Avoid self-justifying signposts: "worth listing because", "now the part where I", "which brings me to", "I will keep this short because". State the point and drop the justification. Join the clauses with a connective instead of chopping into short punchy sentences. A plain causal "because" in an argument is fine.

**Why:** these constructions read as filler, and the fix is not chopping into short sentences, which reads the same way.

### Plain words over jargon

Write so a person with no background understands. No unexplained terms, no bombast, one idea per sentence, a concrete example over an abstraction. Blunt still means true: name the thing as it is rather than wrapping it in lyrical phrasing. In private messages shorthand is tolerated; plain words are still preferred.

**Why:** jargon and grand phrasing read as filler and lose the reader, and a phrase that confuses one reader confuses more.

### No bare citations

Never cite a finding by number alone. Lead with what it says in plain words, then put the number in brackets at the end for traceability. The reader should follow the whole argument without opening a file. Build a word-name for a recurring idea and use it throughout.

**Why:** a bare number is a lookup the reader must perform, and asking them to agree with a citation instead of an argument is the worst shape for a decision.

### A light edit, not a rewrite

When reworking someone's writing, start from their sentences and change the minimum. Keep their length and their words; plain words from the first draft. Offer additions as a short list they can pick from, never folded in.

**Why:** over-building a simple edit costs rounds and trust, and reads as a sign of how the rest of the work will go.

## Name by what it is

### A catchy name is a hook, not a structure

When a name is chosen for a well-known concept, the name is a hook. Do not derive structure or vocabulary from it; use the words the corpus already has. Before coining a term, check the glossary for the existing word. If a new one seems needed, put the word itself in front of the owner in one line before building on it.

**Why:** a name chosen because it is familiar is not an invitation to build a metaphor on it, and a coined term can collide with a word that already means something else.

### Name work in words, not numbers

Every item in a status or menu leads with what it is and what it changes for a person, in a few plain words, then the number as a reference. Order by importance. Never a line of bare numbers.

**Why:** the reader watches many things across many places; a number forces a lookup, so they cannot judge what matters.

## The doc and the commit

### No changelog narration at the top of a how-to

A how-to's opening should orient the reader on how to use the thing now, not narrate its version history. Put "verified live" receipts and history inline in the section about that specific behavior, never as a growing changelog block above the fold. A real changelog is a separate file.

**Why:** the history is already stated where it belongs, so a top block is pure duplication standing between the reader and what they opened the doc for.

### No backticks in an inline commit message

Never type a commit message with backticks, a dollar sign, or a bang straight into an inline flag: the shell runs the backticked words as commands and silently deletes them. Write the message to a file with a quoted heredoc and commit with the file.

**Why:** the shell mangles the markup, and the habit is the inline form itself, so go to the file form as the first draft, not as a repair.
