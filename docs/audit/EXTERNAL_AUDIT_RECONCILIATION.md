# External audit reconciliation

An independent audit of this repository returned a verdict of NOT SAFE with 17 findings. Source: `MIZAN_CODEX_REPO_AUDIT_REPORT.md`.

The audit was run against a commit earlier than the current HEAD, so some findings are already closed. Others are live and one is the most serious integrity defect found in this project. This document separates them, by execution rather than by reading, so that remediation is aimed at what is actually true now.

The rule applied throughout: a finding is marked closed only where a command demonstrates it closed. An audit finding dismissed on the basis that someone believes it was fixed is not dismissed.

## 1. Live findings, verified true at HEAD

### L1. CRITICAL. Adjudication metadata is not bound to the evidence hash

The hash covers the `payload` column. The `score`, `passed`, `control_id` and `suite_id` columns are not covered by it, and those columns are what the certificate is computed from. A row can therefore carry a valid hash while its columns contradict its own payload.

Demonstrated against a copy of the built database. `UPDATE` was correctly blocked by the trigger, so the attack used the insert route instead:

```
Attack: flip the metadata columns only, leaving payload and its hash untouched.
  UPDATE blocked: evidence is append-only: UPDATE is prohibited by charter
  INSERT succeeded: payload says passed=False, columns say passed=1, hash is valid.

verify_evidence.py:
  Hash mismatches        : 0
  Chain breaks           : 0
  Status : CLEAN
```

This breaks the product's central promise. A certificate can assert a pass while the probe a judge clicks into records a failure, and every integrity check reports clean. Earlier internal tamper testing missed it because it only ever altered the payload, which is the half the hash protects.

### L2. CRITICAL on the pitch path. `make demo` and `make prove` do not run anything

Both print a not-implemented message and exit zero. `README.md` lists `make prove` in its verification table as the command that runs the measured proof, and the definition of done requires `make demo` to perform the pitch flow. An exit code of zero from a target that ran nothing is the exact failure this project polices elsewhere.

### L3. MAJOR. Offline dataset verification accepts a changed cache

The audit reports that offline mode accepts a deliberately altered but internally consistent cache file, prints `OFFLINE_OK`, and never compares against the manifest hash, while its closing message states that all live fetches match. Live fetch comparison works; the offline path is the gap.

### L4. MAJOR. Documented setup cannot run the tests

`uv sync` does not install the `dev` extra, so `make test` fails on a clean machine. The continuous integration workflow was corrected, the documentation was not.

### L5. MAJOR. The reduction figure depends on an unstated unit

The proof headlines 83.2 percent measured in evidence rows acted on. Measured in endpoint calls the same run gives 59.4 percent, because the bias suite pre-calls all its responses on the first arm pull. Neither number is wrong; presenting one without naming the unit is. The charter sentence carrying the figure is also hardcoded in the script rather than derived from the run.

### L6. MAJOR. A certified verdict with an undecided control

A one-query passing run ended `certified` while its only control remained undecided, carrying no decision basis and a lower bound of 0.03 against a 0.95 requirement. Certification must never be reachable while a mandatory control is undecided.

### L7. MAJOR. Arabic provenance of the demonstration probe is mislabelled in our own claims

`lca-008`, the religious-ruling probe used as the demonstration's turning point, carries `provenance: harness-scaffold` and `rashid_review_required: true`. It is scaffold content pending native review, not Arabic-native content. The Arabic corpus does contain 67 genuinely native items; this specific probe is not one of them, and it has been described internally as native. That description was wrong and is corrected here.

### L8. Known and recorded, not new

The Postgres `append_evidence` path raises `NotImplementedError`, the live OpenAI-compatible adapter raises `NotImplementedError`, and the strategy-search layer performs no rollouts and only sorts historical mean rewards into a warm start. All three are real limitations. All three are already recorded in `docs/DECISIONS.md` or `docs/FLOW.md` as dormant or deferred. They need honest presentation, not concealment, and the strategy-search layer in particular must not be described as Monte Carlo search while it performs none.

## 2. Findings closed since the audit ran

Each verified closed by execution, not assumed.

| Audit finding | Evidence it is closed |
|---|---|
| WebSocket emits three hardcoded events without invoking the engine | `websocket_route.py` constructs `BatchSuiteRunner` and `BanditEngine` and streams real arm pulls |
| The interface is a loading shell with no journey | Landing, submit, evaluate, certificate, evidence and remediation views are present and build |
| Documented setup produced 175 tests | 246 pass at HEAD |

## 3. What the audit got right about method

The audit cloned cleanly, ran the documented setup rather than the intended one, attacked the integrity claims rather than reading them, and separated what executes from what is staged. That is the correct method and it found a defect that internal review had missed for a full day. Its stale findings are a consequence of auditing a moving repository, not of poor work.
