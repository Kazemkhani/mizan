## What this changes

<!-- One paragraph. Name the behaviour that differs, not the files touched. -->

## Gate output

An exit code is a claim. Paste the real, unpiped output. Beware `cmd | tail`, which reports the exit status of `tail`.

```
$ uv run python -m pytest -q


$ python3 scripts/audit/register_lint.py


$ python3 scripts/audit/verify_grounding.py


```

## Checklist

- [ ] British English throughout, including comments and this description
- [ ] No em-dashes, no emojis
- [ ] Every new number is script-produced, officially sourced with a read date, or labelled an assumption
- [ ] No scorer, threshold or keyword list was adjusted to make something pass
- [ ] No retry was added to absorb flakiness
- [ ] New behaviour has a test that fails without the change
- [ ] Consequential choices recorded in `docs/DECISIONS.md` with the next free number
