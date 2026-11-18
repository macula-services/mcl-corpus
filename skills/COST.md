---
title: Cost
layer: skill
audience: [agent, human]
stage: stable
---

# COST.md: Cost

*The binding cost is model usage, and every owner act is spend.*

---

## What the budget binds

### The binding cost is model usage, not local compute

The cost constraint is runtime model use: token spend and agent calls. A long local run, an experiment sweep, a build on your own machine costs nothing. Economize on model churn, not on local CPU.

**Why:** it is easy to misframe a long local experiment as expensive compute and checkpoint to avoid it, when the only spend that matters is the model.

### An idle session is free; reading and planning are not

Do not read repos, explore or pre-plan to "be ready" for work you have not been assigned. While held or unassigned, stay genuinely idle. A session with no context debt is an asset, because it is cheap to point at anything.

**Why:** when budget is the binding constraint, warming up context on a repo before being pointed at it is pure spend on work whose direction may change before it is used.

## Estimates and burn

### Report by state, not by predicted dates

Do not attach calendar dates or day-counts to work. Report what is done, what it is waiting on and what is next. Sequence and dependency are fine; a predicted finish is not, and it erodes trust the moment it slips.

**Why:** unreviewed code keeps revealing more work, so a date is obsolete within hours, and the reader reads progress from what is actually done and what blocks it.

### Phases are dependency order, not time boxes

A plan's phases express dependency order and release units, not human sprints. Drop day and week labels and replace them with the surfaces shipped and the dependencies satisfied.

**Why:** a day-count projects human pace onto work that moves much faster once the design is clear.

### A usage gauge is a measurement, not an order

When the owner reports a budget gauge, treat it as data for measuring burn, not an instruction to slow down or park anyone. Answer with what the spend bought; change the pace only on the owner's word.

**Why:** a gauge reading can be misread as a quiet order, and an explicit imperative is the only thing that means "change the pace".

### No action changes the bill without a priced yes

Nothing that changes what you pay, a plan resize, a new box, a paid service, an extra address or volume, happens without the owner's explicit yes to a question that states the cost. The default answer is no. Solve a capacity or reliability problem within what you already pay for first.

**Why:** an approval that does not put the price in front of the owner is not consent to spend.

## Where to spend

### Route the bulk to the cheaper model, the judgement to the expensive one

Do the bulk of the building on the cheaper model and reserve the more expensive one for review, design decisions and judgement. The expensive model reviews everything; it does not write the code.

**Why:** the expensive model's budget is best spent where its judgement is the point, and a cheaper model that sits idle while the expensive one builds is a routing miss.

### Efficiency ranks above convenience, and public UX is never convenience

When you decide order or scope, a change that saves tokens, context, review rounds or the owner's attention goes ahead of one that only makes things nicer to use, except public-facing UX. A surface a non-developer meets is never ranked as convenience.

**Why:** efficiency keeps the budget from starving the product's public face, which the owner holds to a high bar.

## Counting owner acts

### Count the whole job before batching owner acts

Before splitting a job into batches that each cost the owner an act, a merge or a yes, count the whole job and state the total number of acts up front. If it is more than a handful, offer a few large batches or one, not many small ones.

**Why:** small batches multiply the owner's acts, and the surprise is discovered only after several batches have already been spent.
