---
title: Issues
layer: skill
audience: [agent, human]
stage: stable
---

# ISSUES.md: Issues

*Every piece of work and every decision lives on an issue that names its purpose; close it by hand once the purpose is proven.*

---

## The purpose line

### Every issue opens with a purpose

An issue opens its body with one line: `Purpose (<kind>): <outcome>`. The kind is one of security, usability, capability, reliability or upkeep. The outcome says what a person, operator or attacker can or cannot do afterwards, never the task restated: "a realm keeps serving its members when a peer refuses a shuffle" is a purpose, "fix the dispatcher crash" is not. If nobody can write the line, do not file the issue.

**Why:** a purpose makes ranking, closing and "are we moving forward?" answerable from the issues.

### A decision is quoted, never paraphrased

An issue opened to carry out a decision quotes the decision's own words in its purpose line, and adds its own terms only below the quote.

**Why:** a paraphrase narrows the decision; the next reader reads the paraphrase instead of the decision and cuts scope to match.

### Close by hand once the purpose is proven

Never write a closing keyword in a commit or pull request when the purpose can be shown met only after a deploy and a live check. The platform closes the issue the moment the commit reaches the default branch, before anything is proven. Write a reference instead, and close by hand with the evidence.

**Why:** the keyword closes the issue before the purpose is met, and the purpose check becomes an afterthought.

## Where the work lives

### Plans and decisions live on the issue, not in local files

Plans, work packages and backlog go in issues in the repo where the work lands, not in local plan files. When a decision is made, put it on the issue in the same step, not parked in a local draft.

**Why:** a local file is a single copy on one machine that nobody else reads, and it drifts.

## File and search

### Search open issues including their comments

Before filing an issue for a failing test or a defect, search open issues for the term across titles, bodies and comments. When a match exists, append the new instance as a comment there instead of filing a duplicate.

**Why:** instances of a known failure are often appended as comments, so a search over titles and bodies alone misses them.

### Check the issue is still worth doing

Before building an issue, read it against the current default branch and what is live. If it is stale, superseded or already done, close it with evidence instead of building it.

**Why:** an issue can already be fixed by a change that landed inside another pull request while the issue stayed open; building it again is wasted work.

### File what you find, including the systemic snag

A bug, gap or stale doc met during work becomes its own issue, not a silent part of the package. A snag in how the work itself is done, one that fails the same way for everyone, is filed the same turn too, asking for a check that fails next time.

**Why:** a workaround unblocks today but the snag recurs; filing it turns a one-off into a fix for everyone.
