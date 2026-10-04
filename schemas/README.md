# Phase 1 schema registry

`0.2.0/` is the current Phase 1 contract. `0.1.0/` remains unchanged for legacy
validation. Both use JSON Schema Draft 2020-12 and identifiers of the form:

```text
urn:dacn:schema:<schema-name>:<schema-version>
```

`common.schema.json` is the shared definition library. The eight persisted
schemas cover sources, artifacts, normalized vulnerability and patch data, the
paired environment, builds, executions, verification, and the replayable case
manifest. The rationale and deferred capabilities are documented in
`docs/schema-mvp-proposal.md`. The new version supports truthful partial failure
packages, three-state verification checks, and required oracle/adapter identity.
See [compatibility rules](../docs/schema-compatibility.md) and the
[usage guide](../docs/schema-usage-guide.md).

The environment contract supports Docker only. Every environment specification
must use `isolation.type: docker` and a digest-pinned image; host execution,
other container engines, sandboxes, and virtual machines are invalid.

Validation is intentionally offline. Consumers should register all files by
their `$id` before validating a document; the test suite demonstrates this
with `referencing.Registry`. Select the exact declared version; do not fall back
to the newest version or relabel legacy records. Both families can coexist in
one registry without ID collisions.

Run contract tests in Docker using [the test instructions](../tests/schema/README.md).
Dependency acquisition and offline test execution are separate phases.

JSON Schema enforces document-local structure and many conditional rules.
The [package validator](../docs/package-foundation.md) checks `0.2.0` reference
integrity, paired identities, stored artifact hashes, ordering, and reported
verdict consistency. Evidence interpretation and CVE-specific verdict derivation
remain the responsibility of the future independent oracle. Schema validity
alone does not establish these cross-record or evidence properties.
