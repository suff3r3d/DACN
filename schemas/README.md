# Phase 1 schema registry

`0.1.0/` contains the deliberately small Phase 1 MVP schema family. Every
schema uses JSON Schema Draft 2020-12 and an identifier of the form:

```text
urn:dacn:schema:<schema-name>:0.1.0
```

`common.schema.json` is the shared definition library. The eight persisted
schemas cover sources, artifacts, normalized vulnerability and patch data, the
paired environment, builds, executions, verification, and the replayable case
manifest. The rationale and deferred capabilities are documented in
`docs/schema-mvp-proposal.md`.

The environment contract supports Docker only. Every environment specification
must use `isolation.type: docker` and a digest-pinned image; host execution,
other container engines, sandboxes, and virtual machines are invalid.

Validation is intentionally offline. Consumers should register all files by
their `$id` before validating a document; the test suite demonstrates this
with `referencing.Registry`.

Run the contract tests from the repository root:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

JSON Schema enforces document-local structure and many conditional rules.
Cross-document requirements—such as reference existence, paired-build
distinctness, artifact hash verification, chronological ordering, and exact
verdict derivation—remain the responsibility of the later semantic/package
validator. That validator is intentionally not part of this schema-only step.
