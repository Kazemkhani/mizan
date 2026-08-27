# MIZAN Product Hunt launch kit

## Submission fields

- **Name:** MIZAN
- **Tagline:** Evaluate public-service AI. Keep the evidence.
- **URL:** https://kazemkhani.github.io/mizan/
- **Pricing:** Free
- **Topics:** Open Source; AI Metrics and Evaluation; Developer Tools
- **Description:** An open-source AI assurance engine for public-service use cases. Map models to 36 controls, run adaptive bilingual evaluations, preserve hash-chained evidence, and issue an inspectable Arabic/English assurance record.
- **Maker:** Amir Hossein Kazemkhani
- **Repository:** https://github.com/Kazemkhani/mizan

## Gallery order

1. `product-hunt/gallery-01-hero.png`: promise and category wedge.
2. `product-hunt/gallery-02-live-product.png`: the deployed landing and live proof bar.
3. `product-hunt/gallery-03-evidence-loop.png`: submit → select → evaluate → verify.
4. `product-hunt/gallery-04-proof.png`: 36 controls, five use cases, bilingual output and tamper-evident evidence.
5. `product-hunt/gallery-05-boundaries.png`: explicit trust boundary: assurance record, not government approval or legal advice.

All gallery images are 1270×760. Use `product-hunt/thumbnail.png` as the square thumbnail.

## 55-second video storyboard

Seconds 0 to 5: landing page and the line “Evaluate AI for public service. Keep the evidence.”

Seconds 5 to 12: show the proof bar: 36 controls, five use cases, five publishers, Arabic and English.

Seconds 12 to 20: click **Run the replay** and load the prepared Arabic assistant.

Seconds 20 to 31: select a public-service use case and show the control set changing.

Seconds 31 to 42: run the recorded evaluation; focus on adaptive test selection, evidence hashes and the visible replay label.

Seconds 42 to 50: open the bilingual assurance record and trace one verdict back to its probe.

Seconds 50 to 55: end card: “Open source. Apache 2.0. Inspect the evidence.” plus the GitHub URL.

No voiceover claim should imply government endorsement, legal compliance or production certification.

## Maker comment outline: rewrite in Amir's own words

Product Hunt prohibits AI-generated comments. Do not paste this outline verbatim.

1. Personal trigger: what felt missing when looking at how AI systems are proposed for public-service use.
2. Concrete problem: model cards and aggregate benchmark scores do not preserve a control-by-control evidence trail.
3. What MIZAN actually does: use-case mapping, adaptive tests, append-only evidence and a signed bilingual record.
4. The hard design choice: Arabic is native, not a translation pass; the engine prints uncertainty and budget exhaustion.
5. Honest boundary: this is pilot-scale open-source assurance work, not a legal opinion or government approval.
6. Ask one real question: which public-service use case or control would the community add first?

## Questions the maker must be ready to answer

### Is this an official government certification?

No. MIZAN is an open-source assurance instrument. Its record shows conformance with the published MIZAN control set and exposes the evidence behind each verdict. It is not approval by a government entity and not legal advice.

### Why is this different from Langfuse, Evidently or generic eval frameworks?

Those tools are strong general-purpose evaluation or observability systems. MIZAN's wedge is use-case-specific public-service controls, native Arabic/English evaluation, adaptive evidence acquisition, an append-only evidence chain and a bilingual assurance record that states its limits.

### Does it send submitted data to a cloud model?

The demonstration path runs against deterministic local adapters. The static site replays recorded runs and labels that state explicitly. Nothing submitted in the demo is sent to a hosted model.

### Are the passes statistically proven?

Not always. Each control records whether it settled by a confidence bound or at budget exhaustion. The assurance record surfaces that distinction instead of hiding it.

### Can I add a use case or control?

Yes. The registry and suites are in the Apache-2.0 repository. Contributions should include provenance, fixtures and tests so the claim stays executable.

## Launch-day conversion path

Product Hunt → live landing → **Run the replay** → inspect one evidence chain → open GitHub → star, issue or contribute.

Primary event: replay started.

Secondary events: assurance record opened; GitHub visit; star; issue/discussion.

## Final gates

- [x] Public repository with Apache-2.0 licence.
- [x] Public live replay.
- [x] Main CI gates green.
- [x] Claims backed by committed evidence and tests.
- [x] Explicit limitations and non-endorsement language.
- [x] Final assets exported and visually checked.
- [ ] 45–60 second deployed-product video uploaded to YouTube as unlisted/public, not private.
- [ ] Product Hunt personal profile completed.
- [ ] Product Hunt draft created and teaser scheduled.
- [ ] Five fresh-browser usability sessions completed.
