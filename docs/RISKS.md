# MIZAN Implementation Risks

Charter Addendum 01 section 5. Risks are volunteered, not hidden. Each carries a named mitigation that sits inside the ninety-day pilot plan, and DIRECTOR prepares each as a spoken answer offered before a judge finishes asking.

Present-tense claims in this document are pilot-scale: one entity, one use case, ninety days. National figures appear only as labelled assumptions.

### R1. The control mappings need a policy owner's signature

MIZAN adjudicates models against a control set of which twenty-eight controls cite published UAE governance principles and eight are MIZAN-defined operationalisations of those principles [source: suites/controls/controls.json, verified by scripts/audit/verify_grounding.py]. A MIZAN-defined control is a reasoned reading of a published principle, not an official control. Until a policy owner signs the mapping, a certificate asserts MIZAN's interpretation rather than the regulator's.

**Mitigation, and it is the first ask of the pilot.** The opening milestone is a mapping review session with the policy owner at the host entity, with every MIZAN-defined control presented beside the principle it derives from and its `derives_from` field read aloud. The control register records provenance per control precisely so this session is an afternoon rather than a project. Where the owner rejects a reading, the control is amended and the affected certificates are reissued; the evidence chain makes the set of affected certificates computable rather than a guess.

### R2. The Arabic test sets need native review

The Arabic evaluation content is Arabic-native rather than translated, and every item records that provenance [source: suites/arabic/, verified by AUDITOR]. It has not yet been reviewed by an independent native Gulf-governmental reader. An attack set that reads as the wrong register tests the wrong thing, and a safety probe that a native speaker would phrase differently may under-detect.

**Mitigation, a day-thirty milestone.** Independent native review of the full Arabic corpus by a reader drawn from the host entity's own Arabic content team, scoped as a fixed review pass rather than an open-ended engagement. Items that fail review are replaced, not patched, and the replacement carries its own provenance record. The review itself becomes the first entry in the register's linguistic audit trail.

### R3. Adoption needs per-entity parity before anyone trusts the verdict

An entity will not retire its existing evaluation process on the strength of an outside verdict. The adaptive engine reaches a verdict from a fraction of the exhaustive evidence, which is the point, and it is also precisely the thing a cautious evaluator will distrust.

**Mitigation, the shadow-run design.** For the pilot the engine runs alongside the entity's existing process rather than in place of it, on the same candidate models, and both verdicts are recorded. The entity keeps its own process as the decision of record throughout. What MIZAN accumulates is a parity ledger: the count of adjudications where the two agreed, and the full evidence trail for any where they did not. Parity is the deliverable that earns the replacement decision, and it is measured rather than argued. Disagreements are the most valuable output of the pilot, not its failures.

### R4. The evidence guarantee has a stated trust boundary

Evidence immutability is enforced by database triggers and a per-evaluation hash chain, so any edit or excision is detectable by traversal [source: docs/DECISIONS.md D-011 through D-014]. A party with direct write access to the database file who rebuilds the chain consistently could defeat detection. This is stated rather than glossed, because a federal evaluator will ask.

**Mitigation, inside the ninety days.** Publish each evaluation's bundle hash to an append-only log outside the registry at the moment a certificate is issued, so verification no longer requires trusting the registry's own storage. The bundle hash already exists on every certificate, so this is a publication step rather than a redesign.

### R5. A dataset binding can go stale or a resource can be withdrawn

Use-case grounding depends on live federal open data. A dataset can be revised, renumbered, or withdrawn by its publishing entity, and a certificate that cites a dead resource is worse than one that cites none.

**Mitigation, in the pipeline rather than in a process document.** Every binding is committed as a hash-verified offline cache alongside the live fetch, so the demo and the audit trail both survive a withdrawal. A certificate cites the Resource GUID together with the date the resource was read, so a later reader can tell staleness from tampering. Re-fetch and hash comparison run as a scheduled check during the pilot, and a divergence raises an incident rather than being silently absorbed.
