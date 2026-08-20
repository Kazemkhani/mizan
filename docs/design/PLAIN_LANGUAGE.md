# Plain language rules for the MIZAN interface

Two readers have independently reported the same problem: the interface is hard to follow because it is written in the vocabulary of the engine rather than the vocabulary of the person using it. One of them is a software engineer and the other commissioned the product. The intended user is a compliance officer at a federal entity who has never heard of a bandit algorithm.

This document is the fix. It is a rule rather than a pass, so that new screens cannot reintroduce the problem.

## 1. The governing rule

**Say what happened. Then, beneath it, show what proves it.**

Every screen leads with a sentence a civil servant would say out loud. The machinery stays reachable, complete and unhidden, one layer below, because "every score links to the evidence that produced it" is the product's core promise and an audit has already found us weak on integrity. Legibility is achieved by ordering the layers, never by deleting the lower one.

## 2. Nothing raw reaches the eye

Three faults recur and all three are mechanical.

**A structured value must never be printed as a string.** A field holding an object is rendered as labelled rows, not as `{"transparency":"...","accountability":"..."}`. If the interface can parse it, the interface can lay it out.

**A field name must never be shown as a label.** `uae_governance_alignment` is a key in a file. The reader sees "Alignment with UAE AI governance principles". Every field that appears on screen carries a human label; a field with no label does not appear.

**An identifier must never stand alone.** `refusal_integrity_v1` and `pri-en-002` mean nothing unaided. Show what the thing does, and keep the identifier beside it in a smaller register for the reader who wants to trace it.

## 3. The vocabulary

Left column is the engine's word. Middle is what the reader sees. Right is why. The engine keeps its own vocabulary internally; this table governs only what reaches a human.

| Internal term | On screen | Reason |
|---|---|---|
| Adjudication | Assessment | Adjudication is a legal register that adds nothing here |
| Probe | Check | A single question put to the model |
| Probe corpus | The bank of checks | Corpus is a linguistics term |
| Arm pull | (never shown) | An implementation detail of the allocator |
| Control | Standard | What the model is being held to |
| Mandatory control | Required standard | |
| Advisory control | Advisory standard, not required to pass | State the consequence, not the category |
| Verdict | Decision | |
| Certified | Certified | Keep. It is the product and it is ordinary English |
| Evidence row | Record | |
| Payload hash | Fingerprint | With the hash itself shown beside it |
| Evidence bundle hash | Fingerprint of the whole record | |
| Scorer | How this was marked | |
| Decision basis | How this was decided | |
| Statistical pass | Confirmed by evidence | |
| Budget pass | Not enough checks to confirm | The honest phrasing, and the one the two-register rule depends on |
| Confidence bound | Certainty reached | |
| Budget exhausted | Ran out of checks | |
| Stopping reason | Why it stopped | |
| Corpus exhausted | No checks left to run | |
| Endpoint | The model being tested | |
| Deterministic mock adapter | A stand-in model that answers the same way every time | |
| Use case | What the model will be used for | |

## 4. Sentences that must be rewritten

The replay banner currently reads:

> No engine is reachable from this page, so MIZAN replays evaluations that the real engine recorded against the real probe corpus. Every step, verdict and hash shown was produced by the engine.

Every word of that is true and almost none of it lands. It leads with an absence, uses three internal terms, and explains the architecture before the point. What the reader needs to know is that they are watching a recording of something real. Something closer to:

> You are watching a recorded assessment. MIZAN really ran these checks; this page replays the saved result rather than running them again now. Nothing shown here was written by hand.

That keeps every honesty commitment in the original. It states the recording plainly, so nobody can believe it is live, and it keeps the claim that the content is engine-produced rather than authored.

Apply the same treatment wherever a sentence explains the system to a reader. Lead with what it means for them, then the mechanism if the mechanism matters.

## 5. What must not be simplified away

Simplifying is not the same as softening, and three things must survive it.

The two evidence tiers must stay visually and verbally distinct. A standard confirmed by evidence and a standard that merely ran out of checks are different claims, and the certificate specification requires they never look alike. "Not enough checks to confirm" is plainer than "budget pass" and it is also more honest, so this rule and the plain-language rule point the same way.

The replay must stay labelled as a replay.

Every number keeps its source. A figure on screen that a reader cannot trace is exactly the defect the grounding gate exists to catch.

## 6. The test

Read any screen and ask what a compliance officer who has never heard of a bandit algorithm would do next. If the answer is not obvious within a few seconds, the screen is not finished.

Both readers who raised this applied that test informally and the interface failed it. It is the standard.
