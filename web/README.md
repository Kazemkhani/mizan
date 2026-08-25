# MIZAN interface

The introduction page and the working console: submit a model, choose the use
case it is intended for, watch the engine adjudicate it, read the certificate,
then close the gaps the evaluation found and come back.

The remediation stage keeps measurement and projection apart, and says which is
which on the panel. The gaps are measured: each one is read from the control
states the engine produced and the probes it drew, including the controls that
passed without earning a confidence bound. The plan and the retraining run are
projection, marked as such, because MIZAN does not train models and does not
observe training. A projection issues nothing: the retrained version goes back
through the engine as a new version, which is the only thing that can certify
it.

## Run it

Against a live engine, from the repository root:

```bash
make dev          # API on 8000, interface on 5173
```

The interface checks `/api/v1/health` at start-up. When an engine answers, it
registers models and streams evaluations for real. When nothing answers, it
replays evaluations the engine recorded earlier, and says so in the header.

Interface only, no Python needed:

```bash
cd web && npm install && npm run dev
```

## Try it

Three prepared submissions live in `public/samples/`. The submit panel loads
any of them in one click, or serves the file for download so it can be dropped
back in like a real submission. After changing one, run `npm run bundle:samples`
so the bundled copy matches the file.

| File | Outcome |
|---|---|
| `agent-compliant-arabic-assistant.mizan.json` | Certified. Ninety-six probes on the citizen chatbot use case. |
| `agent-unsafe-multilingual.mizan.json` | Rejected after nineteen probes, on Arabic language accuracy. |
| `agent-undocumented.mizan.json` | Rejected. A thin model card fails the controls decided on documents. |

`public/samples/README.md` documents the submission format, including which
model card fields the documentary controls read.

## The recorded runs

`src/data/recorded_runs.json` holds fifteen evaluations, one per sample
submission per use case. They are not fixtures written by hand: each was
produced by running the real engine against the real probe corpus, with
`scripts/export_demo_runs.py`. Every step, verdict, decision basis and hash in
the replay came out of the engine.

Regenerate them after any change to the engine, the corpus or the control
register, so the replay and the live path cannot drift apart:

```bash
uv run python scripts/export_demo_runs.py
```

## Deploy

The build is static, so any static host serves it. The deployed interface runs
in replay mode unless it can reach a MIZAN API on the same origin.

**Vercel.** Import the repository; no settings are needed. The `vercel.json`
at the repository root builds this directory and publishes `web/dist`, and the
one here does the same for an import rooted at `web`.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/import?s=https%3A%2F%2Fgithub.com%2FKazemkhani%2Fmizan)

From a shell instead:

```bash
cd web && npx vercel deploy --prod
```

**GitHub Pages.** `.github/workflows/deploy-web.yml` builds and publishes when
manually dispatched, once Pages is set to deploy from GitHub Actions in the
repository settings. It is intentionally not triggered by a push while Pages
is unconfigured, so a private repository cannot publish a site by accident.

**Anything else.** `npm run build` writes `dist/`. Asset URLs are relative, so
serving from a subdirectory works without configuration.

**One file.** `npm run build:single` folds the build into a single HTML
document for a host that serves one page and nothing else. In that form the
typefaces come from the hosted stylesheet rather than the origin, and a
sandboxed viewer may block file downloads, which is why each sample can also
be loaded straight into the panel.

## Entity marks

Cards on the introduction page carry typographic marks drawn by MIZAN, not
official emblems, and the page says so. To show a real emblem, place the file
in `public/entity-logos/` and list it in that folder's `manifest.json`.
