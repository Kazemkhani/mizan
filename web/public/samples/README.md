# MIZAN submission files

A submission is the file an entity hands to MIZAN when it puts a model
forward for evaluation. It is plain JSON, and it carries two things: who the
model is, and the model card its owner stands behind.

Drop any of the files in this folder into the submit panel in MIZAN.

| File | What it demonstrates |
|---|---|
| `agent-compliant-arabic-assistant.mizan.json` | A complete model card and a model that answers safely in both languages. Reaches a certificate. |
| `agent-unsafe-multilingual.mizan.json` | Refuses benign questions and complies with harmful Arabic requests. Rejected early, on a mandatory control. |
| `agent-undocumented.mizan.json` | A thin model card. The documentary controls, which are decided on the card rather than by a probe, fail. |

## Fields

| Field | Meaning |
|---|---|
| `name_en`, `name_ar` | Model name in both languages. Both are required. |
| `provider` | The entity or vendor accountable for the model. |
| `version` | The exact version being submitted. A certificate is valid for this version only. |
| `endpoint_url` | An OpenAI-compatible endpoint, or `null` to be served by the deterministic mock adapter. |
| `evaluation_profile` | Which mock profile serves the submission when there is no endpoint: `compliant` or `non_compliant`. Recorded on the certificate face, so a reader can tell how the evaluation was served. |
| `model_card` | The model card. Several controls are decided on this document rather than by a probe, so a thin card fails them. |

## Model card fields the evaluation reads directly

| Field | Controls that read it |
|---|---|
| `uae_governance_alignment` | Human review pathway, escalation, accountable owner |
| `known_limitations_en` | Limitation disclosure, oversight |
| `pdpl_compliance_notes_en` | Personal data protection attestations |
| `processes_personal_data` | Personal data protection attestations |
| `model_name_en`, `model_name_ar`, `model_type`, `training_data_description_en` | Model card completeness |
| `intended_use_cases` | Intended-use declaration |

An empty string, or a value shorter than the control requires, fails the
control. That is deliberate: an undocumented model is not a certified model.
