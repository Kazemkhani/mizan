# Security policy

## Supported versions

Until MIZAN publishes its first stable release, security fixes target the latest
commit on the default branch. Historical commits and unmaintained forks are not
supported.

## Report a vulnerability

Do not disclose a suspected vulnerability in a public issue, pull request,
discussion or social post.

Use [GitHub's private security advisory
form](https://github.com/Kazemkhani/mizan/security/advisories/new). If that form
is unavailable, email `novalabshq@gmail.com` with the subject
`[MIZAN Security]`.

Include, where possible:

- the affected component and commit;
- a minimal reproduction or proof of concept;
- the impact and realistic attack path;
- any suggested mitigation; and
- whether the finding has been shared anywhere else.

Maintainers will acknowledge valid reports privately, investigate them and
coordinate disclosure after a fix is available. Please do not access data that
is not yours, degrade a service, or publish exploit details before that process
is complete.

## Scope

Security reports may cover the Python engine and API, the React interface,
evidence integrity, certificate issuance, dependency or workflow compromise,
and unsafe handling of submitted model artefacts. Questions about governance
policy or model quality that do not create a software security impact belong in
a regular issue.
