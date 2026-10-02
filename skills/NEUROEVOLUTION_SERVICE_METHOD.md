# Method: from a problem to an island

**This exists so that a stranger's problem can be turned into a running mesh
service that breeds controllers for it, or REFUSED with a reason, without
rediscovering from scratch what a since-removed service already paid for.**

Draft, 2026-08-09. Classification: **BUILD**. It asserts nothing about the world.
It is a procedure and a set of invariants, and it gets tests and a commit, not a
pre-registration.

⚠ One section is different and is marked: section 8 contains a **hypothesis about
a market**, which is a claim, and it is labelled as one rather than smuggled in
beside the engineering.

---

## 1. What already exists, with versions, so nothing is re-derived

| layer | thing | version | what it actually gives |
|---|---|---|---|
| substrate | `macula` SDK | 10.17.0 | realm-scoped pub/sub, unary RPC, streaming RPC, signed DHT records, content blobs, OTP dist over the mesh |
| substrate | `macula-station` | `:main` image (no version tag published yet), 7-station fleet | routing, SWIM, Kademlia, bloom-filter fan-out, single advertiser per `(realm, procedure)` |
| substrate | `macula-portal` | 0.4.0 | realm authority, certs, membership endorsement |
| scaffold | `mcl_om` | 0.23.0 | one behaviour, one `boot/1`, identity, capabilities, `/health`, reckon-db store wiring, `rebar3 new mcl_service` |
| engine | `faber_tweann` | 2.4.0 | `network_evaluator` (the useful part), `sep_cma_es`, `mu_lambda_es`, CfC, plasticity, Rust NIFs, `network_onnx` |
| store | reckon-db + evoq + reckon-evoq | 5.11 / 1.23 / 2.7 | per-service local event store, streams, snapshots |
| worked example | `a since-removed service` | paused fleet-wide (it starved the resident minds sharing its boxes); code intact | the whole method, as run |
| exhibit | `beam-campus-net` | live | read models, `/research/workbench/dronex` |

**Two corrections to what people believe about this stack, both load-bearing.**

**`faber_tweann` is two stacks that are not connected, and the disconnection is
the thing to understand.** An earlier draft of this document said "topology does
not evolve", which is false about the library and hid the real problem.

**Topology evolution works.** `genome_mutator` dispatches nine topological
operators (`add_neuron` by connection split, `outsplice`, `add_inlink`,
`add_outlink`, `add_bias`, `add_sensor`, `add_actuator`, `add_sensorlink`,
`add_actuatorlink`), four LTC mutations and three parametric ones, over a real
genotype graph, with crossover, innovation numbering, three selection algorithms,
Pareto ranking and parsimony pressure. `test/integration/xor_evolves_tests.erl`
solves XOR through the full process-per-neuron path in 12 to 22 generations, and
pole balancing, LTC and recurrent evolution have equivalent tests.

⚠ **What it cannot do is leave the machine.** `genotype` exports no
serialisation at all: no `to_binary`, no `to_json`, no export. Storage is ETS, in
memory, gone on VM exit, and ROADMAP item 3 records that the Mnesia persistence
the docs assume was never implemented. `network_onnx:to_onnx/1` is typed
`-spec to_onnx(network_evaluator:network())` and cannot take a genotype. So an
evolved topology cannot be persisted, cannot go on a wire, and cannot be exported.

⚠⚠ **And the one function that looks like a bridge silently discards the
weights.** `network_evaluator:from_genotype/1` goes one way (there is no
`to_genotype`). Its public `@doc` claims it reads the structure *and weights*
"from Mnesia". The private function it calls counts the neurons, invents a layer
shape (`N < 10 -> [N]`, else two layers of `N div 2`) and fills it with **random
weights**, under its own note *"Create network with random weights (topology
approximation only)"*. It then returns `{ok, Network}`. An evolved champion
handed to it comes back the right size and brain-dead, with no error. **This is a
defect in a repo we own** and CLAUDE.md rule 1 applies to it.

**Consequence for this method, stated as a constraint rather than as a fact about
neural networks:** a service that must persist its population, ship genomes
across the mesh, or export a champion has to use `network_evaluator` plus a
vector optimiser, so **its topology is fixed and what evolves is a flat float
vector**, plus per-neuron `tau` and plasticity coefficients if wanted. Say this
out loud in any charter, and say *why*, because the reason is a missing
serialiser rather than a missing capability, and a missing serialiser can be
fixed.

Closing the gap, cheapest first: (1) make `from_genotype/1` carry the weights when
the topology is layerable and return `{error, not_layerable}` when it is not;
(2) give `genotype` a canonical `to_binary`/`from_binary`, following
`robo_genome`'s discipline of hand-rolled packing, validate-rather-than-clamp and
a content address, which alone unblocks persistence and the wire; (3) ONNX from
an arbitrary DAG, which is real work, though `tweann_nif:compile_network/3`
already evaluates arbitrary DAG and recurrent topologies exactly, so what is
missing is serialisation on either side of a runtime that exists.

`macula` gives **no coordination primitive of any kind**. No election, no lock,
no barrier, no compare-and-swap, no queue, no durable log, no ordered delivery
across publishers, no wildcard subscription, no mesh-wide enumeration, and no
authorization enforcement. A realm is a 32-byte namespace tag, not a capability.
Cross-station DHT find is documented by its own repo at about 60% single-shot.
Everything in section 6 follows from that.

---

## 2. The intake gate: admit or refuse, before anything is built

Seven questions, and they are **not seven gates**. An earlier draft claimed six of
them refuse the problem; that was wrong on three of the six and the adversary
caught it. What they actually are:

- **Four hard bits, answerable at intake, and any one of them refuses:**
  1 consequence, 2 gradient-hostility, 4 throughput, 7 two parties (which
  refuses the mesh rather than the problem).
- **Two commitments, checkable only after the first population exists:**
  3 a graded held-out reference, 5 capacity. These are promises made at intake
  and audited later, and a charter that does not name when it will audit them
  has not made them.
- **One configuration decision, which refuses nothing:** 6 memory. Failing it
  means drop CfC and plasticity, not walk away.

**Answer all seven in writing, in the charter, before a line of world code.**

| # | kind | question | refuse if | where this was paid for |
|---|---|---|---|---|
| 1 | **hard bit** | **Consequence.** Is there a model where the agent's own state feeds the next observation? | No. A tape is not an environment. Without it you are doing supervised learning in a costume and a gradient model beats you with a thousandth of the compute | `EXPLORATION_REAL_WORLD_STREAMS` s0, and the adversary's reduction of that document's three classes to **one bit** |
| 2 | **hard bit** | **Hostility to gradients.** Is the objective discrete, thresholded, asymmetric, defined over a whole trajectory, or demonstrably deceptive? | No. Name the gradient-RL arm you will be compared against and expect to lose to it | trap 3 as amended: the load-bearing comparator is PPO and kin on the *same* consequence model under shared seeds. Deception is 051 |
| 3 | **commitment** | **A graded held-out reference.** Can one be built before the first run, and when will it be audited? | It cannot be built at all. A benchmark cannot be retrofitted, and a weak one saturates and goes silently blind | 054, and dronex `I.22` |
| 4 | **hard bit** | **Throughput.** Can one episode run in well under a millisecond, and can you afford 10^6 to 10^8 of them? | No. Evolution is sample-hungry by construction. A euro or a second per episode kills it | measured, not assumed: dronex rounds are deliberately 4 opponents x 4 starts |
| 5 | **commitment** | **Capacity.** Can the policy be expressed by a fixed-shape net of the size this engine actually evolves, roughly [2,6,4] to [16,24,8]? | Nobody will name the audit. A bridge that fails for want of capacity will be misread as a statement about the problem | the adversary's "axis nobody wrote down". Nothing in the corpus establishes capacity for an industrial policy |
| 6 | **configuration** | **Memory.** Is there partial observability that within-episode memory can pay for? | Nothing. A no means drop CfC and plasticity, because they cost throughput and buy nothing, and their presence will be mistaken for a result | P3 closed on exactly this shape: lifetime learning is a shallow interaction window |
| 7 | **hard bit (mesh only)** | **Two parties.** Are there at least two independently owned nodes that each hold something the other cannot compute, and that cannot share the underlying data? | No. Then build it, but build it local. A single-party island is a mesh service with no reason to be one | see section 6 on what the exchange is actually for |

⚠ **Question 3 has a cheap and general answer that dronex found and that
generalises: a scripted ladder.** A held-out set of hand-written opponents or
scenarios, each adding exactly one competence, never trained against, separation
enforced by a test that fails if the two sets ever merge. It does not need the
customer to publish a forecast. It does need to be **graded**, which means a
random controller must not sweep the bottom rungs and a competent one must not
sweep the top, and grading needs trained controllers, so it is audited after the
first population exists and re-audited whenever the physics change.

⚠⚠ **And the worked example is in the failed state of exactly that audit right
now, which is why Q3 is a commitment and not a gate.** dronex `D.18`: after the
2026-08-09 physics change and fleet wipe, a null and five random controllers win
0 of 48 on **every** rung of **both** ladders, so both rung orders are unknown
rather than wrong, and cannot be re-graded until a bred population can tell rungs
apart. `I.22` is the failure of building the exam wrong. `D.18` is the failure of
being unable to check it. A method that cited only `I.22` would have implied the
second was solved.

---

## 3. The method, stage by stage

Each stage names what dronex did, because the point is that this has been run
once end to end rather than designed once on paper.

⚠ **Two of these stages are dronex choices, not invariants, and are marked
`[DEFAULT]`.** A stage marked `[DEFAULT]` has a recorded reason and a domain may
overturn it; the rest are `[INVARIANT]` and overturning one is how the failures in
section 4 happen again. Stage 8 (steady-state, not generational) and stage 11 (do
not event-source the world) are the two defaults. A dispatch or energy problem
with a regulatory audit obligation may want the opposite of stage 11, and should
say so in its charter rather than quietly diverge.

**Stage 0. Classify, out loud, in the charter: BUILD or CLAIM.** A simulator, a
protocol, an exhibit and a service are BUILDs. They get tests and a commit and no
gate. A statement about the world gets a pre-registration, a DESIGN gate before
the runner exists, and a CLAIM gate before signing. Most of what you will build
is a BUILD. Claims are rarer than they look.

**Stage 1. The charter, one line first.** "This exists so that ..." in a single
sentence, at the top. If you cannot write it, do not start. Then two lists that
matter more than anything else in the document: **what is GIVEN** (the physics,
the channels, the economy, the geometry, the fact that exchange happens at all)
and **what must EMERGE** (every tactic, whether a channel is used at all,
specialisation). Then the **instruments, named before the mechanisms**, in a
table saying what each one answers.

**Stage 2. The world as a pure value.** Integer or fixed-point state, a `rand`
state threaded through every draw, no processes, no clock, no mesh. dronex's
`island.erl` is a value and `island_server.erl` is the only thing with a timer.
The payoff is that "did the roster shrink when a sortie left" is a test over two
terms rather than an orchestration.

⚠ Reproducibility is bounded and must be stated: `rand` and map iteration order
are not promised across OTP releases, so a seed identifies a run **within one
release**, and the Containerfile is part of the record.

**Stage 3. The perception boundary as a shape the compiler checks.** The
controller's `act/4` destructures down to exactly the fields it may see, so the
opponent's record is unreachable by construction. A comment does not survive
review; a shape does. And: **no input channel may name a tactic.** If you find
yourself adding an "am I flanking" channel, a tactic has arrived through the
implementation instead of through evolution.

**Stage 4. Declare the arities.** Export `inputs/0` and `outputs/0` from the task
module and assert them against the net's topology before the first evaluation.
`network_evaluator:set_weights/2` does not validate length, and faber's own
`robo_net` pads or truncates silently, so a shape mismatch produces a number that
means nothing rather than an error.

**Stage 5. Two ladders, disjoint, enforced.** `drone_drills` is the curriculum and
the trainer breeds against it. `drone_trials` is the exam and nothing may train
against it. A test fails if any exam rung appears in `trainer:opponents/1`. This
is not optional and it is the single most expensive lesson in the repository.

**Stage 6. Fitness is a scalar, the exam is a profile, and they are different
kinds of thing.** Selection has to order two candidates, so it needs one number.
The exam is a measurement, so it refuses to produce one number, because a
weighted total smuggles a judgement about which rung matters into an instrument.
If a leaderboard needs one number, the summing happens in the exhibit and is
stated where it happens.

**Stage 7. The genome leaves the machine, so give it a wire form.** Hand-rolled
canonical packing, not `term_to_binary/1`. Validate and reject rather than clamp,
because clamping changes the genome and then the published id no longer
identifies the thing that ran. Explicit limits as a denial-of-service defence.

⚠ `term_to_binary/1` is **not canonical for maps**: a map over 32 keys serialises
in atom-table order, which differs per node. dronex lost days to this (`I.12`):
two identical images computed different engine fingerprints, each island filtered
the other out as incompatible, no raid was ever attempted, and nothing was logged
anywhere. Use `term_to_binary(T, [deterministic])` at minimum. A local property
test cannot catch it, because it needs two atom tables.

**Stage 8 `[DEFAULT]`. A steady-state trainer inside a service that must keep
answering.**
Not generational. One round is small, bounded and resumable, and the island calls
it when it has time, because the service also has to publish, sit its exam and
answer RPCs. And the challenger and the incumbent sit the **same** exam in the
same round, because a stored fitness is a score from a test nobody is sitting any
more.

**Stage 9. Ship the instrument in the commit that ships the mechanism.** dronex's
comms channel and its three-way ablation landed together. Without the ablation,
"they coordinate" and "they were cued" are one impression. An instrument added
later cannot see the history it was added after.

**Stage 10. The mesh protocol, split by nature.** See section 6.

**Stage 11 `[DEFAULT]`. The store holds what was FOUND, not what happened.** dronex persists
the roster, coalesced (a snapshot is full state), through a writer that is TOLD
rather than asked, because a stats call would reintroduce a block one level out.
It does **not** event-source the world. The world is a `gen_server`; the roster is
the durable artifact.

**Stage 12. The export.** `network_onnx:to_onnx/1` takes the same record the
controller is, so a champion runs under onnxruntime off the BEAM. This is what
makes "the controller can leave the simulator" a file rather than an aspiration,
and it is a test rather than a claim.

⚠ Bit-identical replay across runtimes is **not** available and dronex decided
not to chase it. `network_evaluator:apply_activation/2` is private with a closed
clause list and a catch-all of `math:tanh(X)`, so an unknown activation atom
silently becomes libm tanh rather than erroring. Keeping the evaluator means
keeping libm. The arena stays exact, divergence is confined to one function, and
the fleet runs one image.

---

## 4. The invariants, which are the transferable part

These were each paid for by a specific failure. They are the reason this document
is worth more than the code it describes.

1. The exam is disjoint from the curriculum, and a **test** fails if they merge.
2. The instrument ships in the commit that ships the mechanism.
3. **Publish the exercise count beside every null.** An island that published
   nothing and an island whose every publish failed look identical in a log.
4. **A guard compares two sides of a boundary.** A field computed and never put
   on a wire is the failure mode that costs the most and shows the least.
5. Anything read off a wire gets a test that pushes the **real message through
   the real handler**. A four-tuple match against a five-element SDK message
   discarded every fact for an hour, with 226 published and 0 failed at the far
   end.
6. **A constant is chosen on viability, never on outcome**, and the whole sweep is
   published including the arms that killed everything.
7. Real quantities in real units, because leaving the simulator is the point.
8. No input channel may name a tactic.
9. Nothing is deleted to make room. A superseded line is marked, not removed.
10. Every register entry carries an ELI5 written in the same commit by whoever
    wrote the entry. An explanation written afterwards is a translation, and
    translations drift.
11. **A textual guard and a behavioural guard cover different holes.** dronex
    injected the regression to find out which caught it, and the grep did while
    the behavioural test did not. Keep both and state which hole each covers.
    ⚠ This generalises from **one** injected regression. Keeping both guards is
    right; the confidence behind "which one catches what" is n=1.
12. Two registers, not one: **findings about the world** and **findings about the
    work**. The second is where the method improves.

---

## 5. What the neuroevolution actually has to be good at, and what it does not

The original framing was "problems where the environment is dynamic or chaotic,
which would trouble stochastic or deterministic solutions". That is not the
discriminator and it will not survive contact with a customer who has a control
engineer.

**Chaos is not what makes evolution win.** A chaotic environment is usually
*worse* for evolution, because fitness becomes high-variance and the search
spends its budget on noise. What actually selects for this method:

- the objective is **non-differentiable**: deadbands, thresholds, discrete
  actions, integer counts, "number of hours the constraint was violated"
- the objective is **defined over a whole trajectory** rather than per step
- the landscape is **deceptive**, so that climbing the objective moves away from
  the solution. This is the corpus's cleanest positive result: 051 replicated
  Lehman and Stanley, with novelty solving a constructed deceptive maze 34/40
  where objective-EA managed 1/40 and a strong CMA-ES managed 0/40
- **coverage rather than a peak** is what you want. 052: novelty buys 112 of ~112
  behaviour cells against an objective search's 79, at no detectable speed cost
- the policy must be **small and cheap at inference**, and must run on hardware
  that will not host a GPU runtime
- you need **many different good answers**, not one

What it is not good at, and this must be said to the customer before they say it:
anything a gradient can climb; anything with a differentiable simulator, where
gradient RL or MPC will win on sample count by orders of magnitude; anything
needing a large policy; anything where episodes are expensive.

⚠ **And there is a negative in the corpus that constrains the pitch directly.**
P7 closed at insight 062 on this arc-level result: *every configuration tested was
either too decoupled to escalate or too coupled to survive, with no lever between
the two*. 057 refused reciprocal coupling twice, reproduced at n=80 and again on a
re-implemented engine: **a co-adapting opponent buys nothing that a diverse static
one does not.** So "our agents arms-race and improve without bound" is a sentence
this stack may not sell. What it may sell is what dronex is actually built on:
**exchange is how opponent diversity crosses the mesh, and selection stays local.**

---

## 6. What the mesh buys, and what it does not

**Buys:** independently owned nodes, no central coordinator, realm-scoped
isolation, identity per service, and the ability for a party to contribute
without exposing what it holds. That is the federated-AI workload class made
concrete, and it is the differentiator no extractive-ML competitor will build.

⚠ **What it buys is access to material that cannot be generated locally, not
better diversity.** 057 measured that a diverse frozen-random opponent set was
sufficient and that a co-adapting one added nothing, and random diversity is free
on one machine. So the mesh does not earn its place by supplying variety. It
earns it by supplying **the specific things other parties hold and you cannot
compute**: their failure modes, their adversaries, their site. Whether transported
material outperforms local diversity is `CHARTER_P5_SCALE_SUBSTRATE` question 2,
it is unrun, and it may not be asserted in a pitch or a charter.

**Does not buy:** anything that needs agreement. Design accordingly.

| need | do this | not this |
|---|---|---|
| who is available | a **lease**: re-announce on a timer, expire on a TTL. Self-healing, tolerates loss | a registration that must be revoked |
| admission control | **unary RPC**, because you need a serialisation point. Two attackers both see an island open, both muster, and only a synchronous accept turns one away before it commits | pub/sub with a convention |
| the outcome | pub/sub **fact that is a self-contained recording**, published once, played locally | a stream the consumer must assemble |
| audience separation | **two realms**: public for what a spectator watches, fleet for what nodes say to each other. A stranger sees every exchange and can start none | one realm and a filter |
| a lease's length | **long**, so OPEN is the resting state. A short lease makes CLOSED the resting state, nodes turtle, nothing crosses, and the exhibit still looks busy | short, "for freshness" |
| commitment | **both sides publish on acceptance**, so a paid cost leaves a trace even when the other side goes dark | trust the settlement |
| a DHT read | retry. One shot is ~60%, three retries ~97% | assume it worked |
| enumerating peers | a capability announce topic with expiry | `find_records_by_type`, which is local to one station |
| timeouts | **the caller's bound must exceed the callee's.** Otherwise a slow but living peer accepts and works on a request the caller has already abandoned | one number for both |

Two further traps from the substrate that a long-lived service will hit.
`unsubscribe/2` never sends UNSUBSCRIBE on the wire, and bloom filters are
monotone non-decreasing, so a service that creates and retires topics grows its
false-positive fan-out without bound. Prefer a small fixed topic set.
And `macula:call/5` can **exit** with a gen_server timeout rather than return
`{error, timeout}` when there are two or more seeds and the first link is slow.
Wrap it.

---

## 7. What reckon-db can underwrite, and what it cannot

The idea was: reckon-db provides a basis for proof of work, so participants can be
rewarded for their contributions. **This does not follow, and the gap is worth
being precise about, because it is a real design problem with a known name rather
than a missing feature.**

What exists: a **local, per-service** event store. Streams, snapshots, provenance,
and a durable record of what one node believes. Nothing more. There is no shared
ledger, no cross-node consensus, no attestation, and no signature on an island's
identity. dronex's own charter says both halves out loud: *an island identity is
128 bits nobody signs, so it defeats accident and not impersonation*, and *the
defender reports the outcome and is believed, so this is reporting rather than
proof*.

So today, a contribution claim is **unfalsifiable**. A node can claim any result
and nothing can check it.

**The honest primitive that is nearly in reach is not proof of work. It is a
replayable claim under a pinned runtime.** Four steps, ranked by cost, and none
of them is research:

1. **Sign the identity.** `mcl_om` already holds a realm-signed service cert
   and does not use it for this. Signing island facts with it converts
   "defeats accident" into "defeats impersonation by anyone outside the realm".
   Cheap, and it is the one that unblocks everything else.
2. **Put the runtime in the fingerprint.** The engine fingerprint should name the
   OTP release, the libc and the image digest, not only the code. dronex owes
   this and knows it.
3. **Publish enough to recompute.** The seed, the genome ids, the start set and
   the opponent ids, so a third party with the same image can rerun the
   engagement and compare.
4. **Make the arena exact.** Then step 3 becomes verification rather than
   agreement. ⚠ This is the one with a real obstacle: keeping faber's evaluator
   means keeping libm tanh, so the brain is not exact and a replay agrees to
   about a unit in the last place rather than bit for bit. Steps 1 to 3 are worth
   doing regardless.

That gets you **verifiable contribution among parties who already agreed on an
image**, which is a consortium, not an open market. Rewarding strangers needs
either a trusted execution attestation or a redundant-execution scheme with
challenge, and both are a different project.

---

## 8. Problem categories, sorted by whether they pass section 2

⚠ **This section is a claim about a market, not an engineering statement.** It is
argued, not measured, and the way to test it is to ask two prospective customers,
not to build.

| category | example | gate result |
|---|---|---|
| **Adversarial scenario generation** | breed the cases that break a customer's existing controller; hand back a coverage map of where it fails | Passes 1, 2, 5, 7. **Q3 is not free and Q4 is the binding constraint**, and both are on the customer's side of the fence. See below. Still the strongest fit in the list |
| **Dispatch and rebalancing under stochastic demand** | bike-share van routing, yard and container moves, crew reassignment after disruption, ambulance posting | Passes 1 to 5. Fails 7 for a single operator, passes it for a sector body. The corpus's own top pick, and it is Raf's own field |
| **Local energy flexibility against a price or frequency signal** | battery, heat pump and EV dispatch against Belgian imbalance price; frequency containment | Passes 1 to 4 cleanly, and the capture is **already running** in the org's grid and archive work. ⚠ Fails 2 in spirit: droop control and MPC are mature and very strong here, so the honest arm is "beat the operator's own published forecast", which the exploration doc calls three rungs too high |
| **Water and pump network scheduling** | discrete pumps, tank levels as endogenous state, tariffs exogenous, hard level constraints | Passes 1 to 6 well. Quietly the best classical control fit, and utilities are public or cooperative, which suits the European anchor |
| **Contested airspace and perimeter** | counter-UAS, which is dronex's own second act | Passes all seven, including 7, because parties naturally hold different adversaries. ⚠ Dual-use, and the licence and export questions arrive before the engineering ones |
| **Process control with a thresholded quality constraint** | greenhouse climate, fermentation, kilns and drying | Passes 2 and 3. ⚠ Fails on simulation fidelity, which is the whole problem. The sim-to-real gap is the product, not a detail |
| **Direction prediction on a market** | any of it | **Refused at 1.** No consequence model on replay, no known ceiling, and a 52% directional accuracy on one split is noise |

### Why adversarial scenario generation is the one to test first

Selling "our evolved controller beats yours" requires beating a mature baseline,
requires capacity we cannot argue for, requires simulation fidelity we cannot
guarantee, and puts us on the losing side of every comparison a competent
engineer will run.

**Invert it.** The customer keeps their controller. We breed the scenarios that
break it. Fitness is "makes their controller fail". What that buys, and what it
does not:

- **gate 1 passes trivially**: their controller closes the loop
- **gate 2 passes by construction**: "did it fail" is a threshold
- **gate 5 stops mattering**: a scenario generator does not need to represent a
  good policy, only a bad situation. This is the real escape and it is genuine
- ⚠ **gate 3 does NOT pass for free.** Their system is the *fitness function*,
  which is not the same thing as a held-out reference. A generator whose only
  signal is "did it fail" finds one failure and mutates around it: fitness
  maxes, coverage is zero, and that is insight 054's saturation exactly, in the
  document that exists to prevent it. What Q3 costs here is a **behaviour
  descriptor over scenario space**, hand-chosen, and hand-choosing it is
  unpaid-for work on every new customer
- ⚠⚠ **gate 4 is the binding constraint, and it sits on the customer's stack.**
  The inner loop is their controller plus a simulator of their plant, 10^6 to
  10^8 times. An MPC solve or a PLC scan is milliseconds to seconds per step,
  which is three to six orders of magnitude too slow. **The first question to any
  prospect is therefore not "what breaks" but "can your controller be run
  headless, deterministically, ten million times".** Most cannot, and that is the
  refusal that will kill most of these conversations

052 supports the **direction** and no more. It says novelty bought 112 of ~112
behaviour cells against an objective search's 79 at no detectable speed cost, and
it scopes itself to that maze family and representation, with the coverage
magnitude bounded by the world's size. Read it as "coverage-seeking search is the
right family for this", not as a number that transfers.

The deliverable is a failure case, which the customer can check on their own
system in an afternoon. That is a very short sales cycle compared to "trust our
number", and it survives even when the coverage story is weak.

**And the federation argument is not the one an earlier draft made.** It is not
"exchanged genomes beat local diversity", because 057 measured the opposite
shape: a diverse **frozen-random** opponent set was sufficient, and random
diversity is free locally. Whether transported foreign material beats it is
precisely the P5 question, which has zero insights, so it may not be asserted.

The argument that does survive is narrower and better: **a real failure mode held
by another party is not samplable locally at any price.** Random scenario
diversity is free; another operator's actual near-miss is not, and no amount of
local compute produces it. A sector body, a regulator or a consortium each hold
failure modes the others have never seen and cannot legally share the underlying
data for. That is what the mesh moves, and it is why selection can stay local
while the exchange still pays.

---

## 9. What in all of this is a BUILD and what is a CLAIM

| thing | kind | consequence |
|---|---|---|
| this document, the scaffold, a new world, a mesh protocol, an exhibit | BUILD | tests and a commit. No gate |
| "chaos is why neuroevolution wins" | CLAIM, and **probably false**. Section 5 | do not put it in a pitch |
| "federated islands converge faster or better than one population" | CLAIM, **unrun**. This is `CHARTER_P5_SCALE_SUBSTRATE` central question 1 and 2, and P5 has no insights of its own | needs a pre-registration, a fixed benchmark and matched total evaluations before anyone says it |
| "the archipelago arms-raced" | CLAIM, and **refused in advance** by 057 and 062 | forbidden without a pre-registration, a graded benchmark and a master tournament |
| "customers will pay for bred adversarial scenarios" | CLAIM about a market. Section 8 | test by asking two, not by building, and lead with the Q4 question ("can your controller run headless and deterministically ten million times") because it is the one that refuses most conversations |
| "this document is a method rather than dronex with the nouns removed" | CLAIM about itself, **n=1, untested**. Its acceptance test is committed in 10.4 | the second service built under it decides |

⚠ Note what this table exposes. dronex is a five-node federated evolutionary
system that has been running for days, and **P5, the programme that owns the
federation question, still has zero insights.** The BUILD exists and the CLAIM has
never been made. That is the correct order, and it is also the cheapest available
result: the instrument is already deployed.

---

## 10. Open questions

1. Is the intake gate load-bearing, or would every real problem be decided by
   questions 1 and 4 alone, with 2, 3, 5, 6 as decoration?
2. Section 8 inverts the product from policy to scenario. Does that inversion
   survive the observation that a scenario generator still needs a simulator of
   the customer's world, which is the expensive part either way?
3. Is "replayable claim under a pinned runtime" (section 7) worth building, or is
   a consortium that already agreed on an image a group that did not need the
   verification?
4. dronex is one worked example. Is a method extracted from n=1 a method, or a
   description of dronex with the nouns removed?

   **This one is not left open, because a BUILD gets a test and the test of a
   procedure is its second use.** Committed now, before the second service
   exists, so it cannot be fitted afterwards:

   > The next service built under this document keeps a findings-about-the-work
   > register, per invariant 12. If that register accumulates entries in failure
   > categories invariants 1 to 12 claim were already paid for (curriculum and
   > exam merged, an uncanonical wire form, an instrument shipped after its
   > mechanism, a silent arity mismatch, a field computed and never put on a
   > wire), then **the method failed as a method** and this document is re-filed
   > as dronex documentation with the nouns put back.

   Until that second pass exists, the title sentence, "without rediscovering what
   a since-removed service already paid for", is **untested**. It is the document's central
   claim about itself and it currently has n=1.
