# Contributing

Contributions are organized around measurable technical workstreams rather than generic feature requests.

## Start

```bash
make doctor
make test
```

## Contribution rules

- Add or update tests for behavior changes.
- Use synthetic fixtures.
- Do not add private/case data.
- Do not add secrets or `.env` files.
- Preserve source provenance when migrating prior work.
- Do not bypass authorization, verification, or provenance boundaries.
- Update `CURRENT_STATE.md` only when evidence supports the new status.

## Good contribution types

- `authority-model`
- `courtlistener`
- `search`
- `citation-validation`
- `quote-verification`
- `currentness`
- `adverse-authority`

## Pull requests

Explain:
- problem;
- approach;
- tests/evals;
- provenance impact;
- security/privacy impact;
- known limitations.

See `.github/PULL_REQUEST_TEMPLATE.md`.
