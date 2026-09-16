# Phase 1 Schema Plan

## 1. Purpose

This document defines the schema family needed for Phase 1 of the project:
deterministic reconstruction and verification of publicly disclosed 1-day
vulnerabilities.

The schemas must support a traceable claim that one replayable artifact:

1. Reaches the relevant code or state in a vulnerable build.
2. Produces the expected vulnerability-specific signal.
3. Does not produce that signal in the patched build.
4. Does not produce that signal in required negative controls.
5. Can be tied to public source evidence, immutable revisions, and the target
   patch.

The schema family is intended for a non-agentic Phase 1 baseline. It must not
depend on an LLM provider, agent framework, or Phase 2 orchestration model.

## 2. Design Principles

### 2.1 Separate declarations from observations

A requested configuration must not be confused with what actually occurred.
The following pairs therefore remain separate:

- `environment-spec` and `build-record`;
- `execution-spec` and `execution-record`;
- `verification-policy` and `verification-result`.

### 2.2 Preserve raw and normalized evidence

Normalized values must retain links to the raw values and sources from which
they were derived. Conflicting source claims must be represented explicitly;
normalization must not silently discard them.

### 2.3 Reference large artifacts

Logs, binaries, core dumps, coverage databases, source archives, debugger
transcripts, and similar data must be stored as artifacts. Structured records
contain metadata and case-relative artifact references, not the large content.

### 2.4 Make claims evidence-addressable

Important claims should identify their supporting sources or artifacts and
state whether they are confirmed facts, evidence-based inferences,
hypotheses, or unknowns.

### 2.5 Use stable identities

Records need stable identifiers. Source revisions, build outputs, inputs, and
evidence artifacts should use immutable identities and cryptographic hashes
where practical.

### 2.6 Support partial and failed cases

Schemas must represent incomplete stages, conflicting data, failed attempts,
and inconclusive verification. Missing evidence must not be encoded as success.

### 2.7 Version every persisted document

Every top-level document must declare its schema name and version. Schema
changes must account for already stored benchmark cases through compatibility
handling or explicit migrations.

## 3. Schema Map

```text
source records
      |
      v
vulnerability record --> revision resolution --> patch context
                                                    |
                                                    v
                                            environment specs
                                                    |
                                                    v
                                              build records
                                                    |
candidate/control artifacts --> execution specs --> execution records
                                                    |
verification policy --------------------------------+
                                                    v
                                           verification result
                                                    |
                                                    v
                                               case manifest
```

Validation-result records attach cross-cutting structural, reference,
artifact-integrity, semantic, and package checks to records and artifacts at
each layer without mutating the checked evidence.

Pipeline runs, benchmark ground truth, attempts, experiments, and reports
reference this core case data rather than redefining it.

## 4. Foundation Definitions

### 4.1 `common.schema.json`

This is a library of reusable definitions, not normally a persisted document.

It should define:

- schema identifier and semantic version;
- stable record and case identifiers;
- UTC timestamps;
- SHA-256 digests;
- case-relative paths;
- repository and immutable revision identifiers;
- tool identity and version;
- confidence and uncertainty;
- claim classification: `confirmed_fact`, `strong_inference`, `hypothesis`,
  and `unknown`;
- stage status;
- canonical pipeline stages, execution roles, intervention levels, and
  verification verdicts;
- repair classification;
- failure taxonomy;
- provenance links;
- artifact references.

The failure taxonomy must include:

- `metadata_failure`;
- `revision_failure`;
- `dependency_failure`;
- `toolchain_failure`;
- `configuration_failure`;
- `build_failure`;
- `startup_failure`;
- `harness_failure`;
- `reachability_failure`;
- `hypothesis_failure`;
- `oracle_failure`;
- `control_failure`;
- `resource_failure`.

### 4.2 `artifact-record.schema.json`

Describes a stored artifact without embedding its contents.

Required concepts:

- artifact ID;
- artifact kind;
- case-relative path or content-addressed locator;
- media type;
- byte size;
- SHA-256 digest;
- producer stage or tool;
- creation timestamp;
- original or derived status;
- parent artifact references;
- transformation or redaction metadata;
- registration-time availability and content identity.

Examples include advisory snapshots, source archives, patches, build logs,
binaries, triggers, sanitizer reports, traces, coverage output, and reports.

### 4.3 `validation-result.schema.json`

Records one immutable structural or semantic validation event.

Required concepts:

- validation type;
- exact record, artifact, or package subject;
- validator identity and version;
- start and completion timestamps;
- passed, failed, or error status;
- individual check results;
- machine-readable findings and JSON Pointer locations;
- observed and expected artifact size/digest for integrity checks;
- summary and provenance.

Repeated checks create new validation-result records. They do not mutate the
artifact or structured record being validated.

## 5. Vulnerability and Source Schemas

### 5.1 `source-record.schema.json`

Represents acquired public evidence.

Required concepts:

- source ID and source type;
- canonical locator, such as a URL or repository reference;
- publisher or repository owner;
- publication and retrieval timestamps where available;
- retrieval method and tool identity;
- retrieval status;
- raw-content artifact reference;
- content digest;
- licensing or access notes;
- errors and uncertainty.

The source record establishes provenance but does not assert that every claim
inside the source is correct.

### 5.2 `vulnerability-record.schema.json`

Represents normalized vulnerability metadata.

Required concepts:

- primary identifier and aliases;
- title and descriptions;
- affected product or component;
- CWE or vulnerability class;
- affected and fixed version claims;
- advisory, issue, repository, and patch references;
- raw value, normalized value, source reference, and confidence for material
  normalized fields;
- conflicts between sources;
- unresolved questions.

This schema records public claims. It must not claim that a selected source
revision is vulnerable until revision resolution supplies that evidence.

### 5.3 `revision-resolution.schema.json`

Records the selection of vulnerable and patched source revisions.

Required concepts:

- repository identity;
- vulnerable revision and immutable commit ID;
- patched revision and immutable commit ID;
- resolution method;
- supporting source and artifact references;
- rejected or ambiguous alternatives;
- ancestry or comparison evidence;
- proof that vulnerable and patched revisions differ;
- resolution status and failure classification;
- remaining uncertainty.

Moving branches or tags may be recorded as inputs, but resolved immutable
commit IDs must be retained for replay.

### 5.4 `patch-context.schema.json`

Represents evidence extracted from the target patch and nearby code.

Required concepts:

- fixing commit references;
- patch and diff artifact references;
- changed files;
- changed symbols or functions;
- relevant code regions;
- nearby callers or initial reachability context;
- root-cause statements;
- claim classification and supporting evidence;
- extraction tool and command provenance;
- limitations and uncertainty.

Heuristic reachability or root-cause interpretations must not be encoded as
confirmed facts without supporting evidence.

## 6. Environment and Build Schemas

### 6.1 `environment-spec.schema.json`

Declares the intended reconstruction environment.

Required concepts:

- environment ID and role;
- operating-system base and immutable image digest where applicable;
- architecture;
- compiler, linker, runtime, package manager, and build-system requirements;
- dependency declarations and pinning policy;
- configuration, feature flags, and build mode;
- build commands and working directories;
- instrumentation requirements and compatibility;
- dependency-acquisition network policy;
- build and execution network policy;
- resource limits;
- expected build outputs;
- permitted environment asymmetries and their justification.

Vulnerable and patched specifications should share a common environment base
wherever possible.

### 6.2 `build-record.schema.json`

Records an observed build attempt.

Required concepts:

- build ID and target role;
- referenced environment specification;
- immutable source revision and source hash;
- observed toolchain and build-tool versions;
- exact dependency resolution result;
- commands, environment, timestamps, and duration;
- exit status;
- build-log artifact references;
- output artifact references and hashes;
- cache identity and isolation evidence;
- repairs applied and their classification;
- build status and failure classification;
- comparison-relevant deviations;
- provenance and uncertainty.

The record must make accidental reuse of the same source, binary, layer, or
cache entry by vulnerable and patched builds detectable.

## 7. Execution Schemas

### 7.1 `execution-spec.schema.json`

Declares one requested execution.

Required concepts:

- execution ID and role: vulnerable, patched, or named control;
- build ID and executable artifact;
- candidate or control input artifact;
- command and arguments;
- case-relative working directory;
- explicit environment variables;
- harness or adapter identity;
- instrumentation configuration;
- timeout, memory, process, disk, and output limits;
- network policy;
- expected output or state artifacts.

The vulnerable and patched execution specifications must make it possible to
verify that the same candidate artifact and comparable harness settings were
used.

### 7.2 `execution-record.schema.json`

Records observed execution evidence.

Required concepts:

- referenced execution specification;
- actual command, environment, and working directory;
- start and end timestamps and duration;
- exit code and terminating signal;
- timeout and resource-limit events;
- stdout and stderr artifact references;
- sanitizer report references;
- stack trace or debugger evidence;
- coverage summary and relevant code locations;
- generated output files and state changes;
- truncation indicators;
- execution status and failure classification;
- tool and host/container provenance.

A timeout, signal, or non-zero exit must remain an observation rather than an
automatic vulnerability finding.

## 8. Verification Schemas

### 8.1 `verification-policy.schema.json`

Defines the oracle inputs and rules before a verdict is calculated.

Required concepts:

- policy ID and version;
- target vulnerability and patch context;
- expected vulnerable signal;
- expected patched behavior;
- required negative controls;
- target-code or state-reachability requirements;
- signal matchers and acceptable evidence types;
- environment-validity requirements;
- vulnerable/patched comparability requirements;
- required versus optional instrumentation;
- rule ordering or combination semantics;
- verdict mapping.

Versioning this policy prevents success criteria from being silently changed
after observing execution output.

### 8.2 `verification-result.schema.json`

Records the oracle decision and all relevant comparisons.

Required concepts:

- referenced policy;
- vulnerable, patched, and control execution references;
- environment-validity checks;
- build-comparability checks;
- per-run signal observations;
- code-region or state-reachability evidence;
- patch/root-cause consistency assessment;
- individual rule outcomes;
- final verdict;
- rationale;
- failure classification where applicable;
- remaining uncertainty;
- evidence and artifact references;
- oracle implementation and version.

Allowed top-level verdicts are:

- `VERIFIED`;
- `NOT_REPRODUCED`;
- `INCONCLUSIVE`;
- `INVALID_ENVIRONMENT`.

## 9. Package and Lifecycle Schemas

### 9.1 `case-manifest.schema.json`

Acts as the root, replayable vulnerability package.

Required concepts:

- immutable manifest record ID, stable case ID, and package schema version;
- vulnerability identity;
- source record references;
- revision resolution;
- patch context;
- environment specifications;
- build records;
- artifact inventory;
- execution specifications and records;
- verification policy and result;
- replay entry point;
- package status;
- creation and supersession provenance;
- compatibility or migration metadata.

The manifest should reference independently stored large records or artifacts
rather than duplicate them.

### 9.2 `attempt-record.schema.json`

Preserves failed and successful trajectories.

Required concepts:

- attempt ID;
- case and pipeline-run references;
- stage;
- parent attempt;
- declared inputs;
- produced records and artifacts;
- start/end timestamps;
- status;
- failure classification;
- diagnosis;
- repair or retry decision;
- intervention level;
- tool and provenance information.

### 9.3 `pipeline-run.schema.json`

Tracks resumable execution across Phase 1 stages.

Required concepts:

- pipeline-run ID and version;
- case reference;
- ordered stage records for `collect`, `normalize`, `resolve`, `build`,
  `extract`, `execute`, `verify`, and `report`;
- stage inputs and outputs;
- stage status and failure reason;
- attempt references;
- resume and interruption metadata;
- automation and human-intervention level;
- timing and resource use.

## 10. Benchmark and Experiment Schemas

These are part of Phase 1 but should be implemented after the core case
package is stable.

### 10.1 `benchmark-case.schema.json`

Stores manually reviewed ground truth separately from automated results.

Required concepts:

- benchmark case ID and dataset version;
- case-manifest reference;
- justification for the vulnerable revision;
- justification for the patched revision;
- patch or fixed-version evidence;
- expected vulnerability class and root cause;
- expected observable signal;
- known prerequisites and limitations;
- reference replay artifact where available;
- reviewer identity or pseudonymous ID;
- review timestamps and status;
- development, validation, or held-out split assignment.

### 10.2 `experiment-manifest.schema.json`

Freezes an experimental configuration.

Required concepts:

- experiment ID and research question;
- dataset and split versions;
- included and excluded cases;
- pipeline and schema versions;
- supplied information sources;
- compute, time, and retry budgets;
- intervention policy;
- environment and instrumentation policy;
- evaluation metrics;
- random seed or other determinism controls where applicable.

### 10.3 `experiment-result.schema.json`

Stores aggregate and per-case outcomes.

Required concepts:

- experiment-manifest reference;
- per-case pipeline-run and verification references;
- total cases and selected unit of analysis;
- exclusions with reasons;
- environment reconstruction success rate;
- CVE-specific reproduction success rate;
- oracle false-positive rate;
- time to environment and verdict;
- repair count and failure distribution;
- resource cost;
- automation and human-intervention measurements;
- missing data and limitations.

### 10.4 `case-report.schema.json`

Defines a concise derived report rather than primary evidence.

Required concepts:

- case and verification references;
- environment status;
- trigger status;
- vulnerable, patched, and control summaries;
- code-region and root-cause evidence summary;
- final verdict;
- confirmed facts;
- strong inferences;
- hypotheses;
- unknowns and remaining uncertainty;
- replay instructions;
- artifact references.

## 11. Recommended Implementation Priority

### Priority 1: shared evidence contract

1. `common.schema.json`
2. `artifact-record.schema.json`
3. `source-record.schema.json`
4. `validation-result.schema.json`

These establish identifiers, provenance, hashes, and raw evidence handling used
by every later schema.

### Priority 2: normalized case identity

5. `vulnerability-record.schema.json`
6. `revision-resolution.schema.json`
7. `patch-context.schema.json`

These establish what vulnerability and source revisions the project is trying
to reproduce.

### Priority 3: reconstruction and execution

8. `environment-spec.schema.json`
9. `build-record.schema.json`
10. `execution-spec.schema.json`
11. `execution-record.schema.json`

These define the deterministic substrate and observed runtime evidence.

### Priority 4: verification and packaging

12. `verification-policy.schema.json`
13. `verification-result.schema.json`
14. `case-manifest.schema.json`

These make the counterfactual claim explicit and package it for replay.

### Priority 5: lifecycle and research evaluation

15. `attempt-record.schema.json`
16. `pipeline-run.schema.json`
17. `benchmark-case.schema.json`
18. `experiment-manifest.schema.json`
19. `experiment-result.schema.json`
20. `case-report.schema.json`

## 12. Versioning and Compatibility

Each persisted document should include at least:

```yaml
schema_name: execution-record
schema_version: 1.0.0
record_id: <stable identifier>
```

Recommended compatibility rules:

- Use semantic versions for schemas.
- Patch releases clarify constraints without changing accepted document shape.
- Minor releases add backward-compatible optional fields or enum values only
  when consumers tolerate unknown values.
- Major releases may make breaking changes and require migration.
- Preserve the original document when migration is performed.
- Record the migration tool, version, time, input hash, and output hash.
- Do not silently coerce documents with unsupported schema versions.
- Pin schema versions in benchmark and experiment manifests.

## 13. Cross-Schema Invariants

The schema validators and later semantic validation layer should enforce or
check the following invariants:

1. Artifact paths are case-relative and cannot escape the case root.
2. Every referenced artifact declares a digest and size.
3. Vulnerable and patched revisions resolve to different immutable sources.
4. Vulnerable and patched build outputs cannot silently share the same binary,
   layer, or cache identity.
5. Vulnerable and patched candidate executions reference the same candidate
   artifact.
6. Negative controls are explicitly identified and their relationship to the
   candidate is declared.
7. Every verification result references the exact policy used.
8. `VERIFIED` requires a valid environment, vulnerable target evidence,
   patched safe behavior, passing controls, and relevant code/state evidence.
9. `INCONCLUSIVE` and `INVALID_ENVIRONMENT` cannot be aggregated as successful
   reproductions.
10. Raw artifacts remain immutable; transformations create derived artifacts.
11. Every material normalized claim retains source provenance.
12. Host-specific absolute paths and secrets are prohibited in reusable
    packages.

JSON Schema can validate document structure and many local constraints. A
separate semantic validator will be required for cross-document properties
such as hash verification, revision inequality, artifact existence, ancestry,
and counterfactual comparability.

## 14. Deliberately Deferred Items

The following are not needed in the initial Phase 1 schema implementation:

- agent definitions;
- task delegation records;
- graph state;
- LLM prompts or model-specific configuration;
- autonomous refinement policies;
- exploit or post-exploitation metadata.

If Phase 2 is later approved, its schemas should reference the Phase 1 case,
artifact, execution, and verification records rather than replacing them.

## 15. Concrete Schema Conventions

These conventions apply to all Phase 1 JSON Schemas unless a schema documents
a specific exception.

### 15.1 JSON Schema dialect

Use JSON Schema Draft 2020-12:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema"
}
```

Draft 2020-12 is selected for stable `$defs`, conditional validation,
`dependentSchemas`, and current validator support. Mixing dialects inside the
schema family is not allowed.

### 15.2 Schema files and directory layout

Use lowercase kebab-case schema filenames. Store immutable released schemas
under their complete semantic version:

```text
schemas/
  1.0.0/
    common.schema.json
    artifact-record.schema.json
    source-record.schema.json
    vulnerability-record.schema.json
    ...
  current -> 1.0.0  # optional development convenience, never persisted
```

The version directory is authoritative. A mutable alias such as `current`
must never be referenced by a persisted package, benchmark, or experiment.

Schema names use the filename without `.schema.json`, for example
`artifact-record`. Definition names under `$defs` use lower snake case, for
example `artifact_reference` and `utc_timestamp`.

### 15.3 Canonical schema identity

Use offline-first URNs as canonical `$id` values:

```text
urn:dacn:schema:<schema-name>:<semantic-version>
```

Example:

```json
{
  "$id": "urn:dacn:schema:artifact-record:1.0.0"
}
```

Cross-schema references use the complete immutable URN:

```json
{
  "$ref": "urn:dacn:schema:common:1.0.0#/$defs/sha256_digest"
}
```

Validators must preload the released schema directory into a local registry
that maps canonical URNs to files. Validation must not require network access.
Relative file references and references to mutable version aliases are not
allowed in released schemas.

Changing a schema's contents without changing its version and `$id` is
prohibited. Released schemas are immutable artifacts and should themselves be
hashed by benchmark and experiment manifests.

### 15.4 Persisted document envelope

Every independently persisted document must include:

```json
{
  "schema_name": "execution-record",
  "schema_version": "1.0.0",
  "record_id": "urn:dacn:execution:0195f2f0-7d20-7000-8000-000000000001"
}
```

Rules:

- `schema_name` must be a constant in each document schema.
- `schema_version` must be a constant matching the validating schema version.
- `record_id` must be globally unique within the project dataset.
- Stable entity IDs such as `case_id` use the same URN syntax but remain
  distinct from immutable persisted-record IDs.
- Referenced documents use their `record_id`, not a filesystem path.
- Artifact content continues to use case-relative paths through artifact
  records.
- Embedded objects that cannot exist independently do not receive this
  envelope.

### 15.5 Record identifiers

Internal record identifiers use this form:

```text
urn:dacn:<record-kind>:<uuid>
```

Use UUIDv7 where the implementation supports it because it is unique and
roughly time ordered. UUIDv4 is an acceptable fallback. The UUID must be
generated once and remain stable when a record is copied, indexed, or moved.

Examples of record kinds include:

- `case`;
- `case-manifest`;
- `source`;
- `vulnerability`;
- `revision-resolution`;
- `patch-context`;
- `validation`;
- `environment`;
- `build`;
- `artifact`;
- `execution-spec`;
- `execution`;
- `verification-policy`;
- `verification`;
- `attempt`;
- `pipeline-run`;
- `benchmark-case`;
- `experiment`;
- `experiment-result`;
- `case-report`.

Human-readable identifiers such as `CVE-2025-1234` belong in dedicated domain
fields and must not replace internal IDs. A case may additionally have a stable
human-readable `case_key`. References to persisted documents use `record_id`;
case membership uses the stable `case_id` entity identifier.

Artifact IDs identify metadata records, not content. Content identity is
established separately by its digest so that two artifact records may
legitimately refer to identical bytes while retaining distinct provenance.

### 15.6 Property naming

Use lower snake case for JSON property names:

```text
started_at
source_sha256
failure_class
negative_controls
```

Additional rules:

- Use singular names for scalar values and plural names for arrays.
- Boolean properties should read as assertions, such as `timed_out`,
  `network_enabled`, or `integrity_verified`.
- Identifier properties end in `_id`; arrays of identifiers end in `_ids`.
- References to records should use `<kind>_id` or `<kind>_ids`.
- Timestamp names end in `_at`.
- Duration names include their unit, such as `duration_ms`.
- Size and resource fields include their unit, such as `size_bytes` and
  `memory_limit_bytes`.
- Avoid ambiguous names such as `data`, `value`, `result`, and `status` when a
  more specific name is available.

The four verification verdict strings remain uppercase because they are
research-reporting states defined by the verification contract. Other enums
use lowercase snake case.

### 15.7 Required fields and nullability

Use `required` deliberately. A field is required when consumers cannot safely
interpret the record without knowing whether it was supplied.

Conventions:

- Absence means the field was not supplied or is not applicable.
- `null` is allowed only when it has an explicitly documented meaning that is
  distinct from absence.
- Empty arrays mean the collection was evaluated and contains no items; they
  must not be used to mean "not evaluated."
- When that distinction matters, include an explicit status such as
  `collection_status` or `availability`.
- Required strings should normally use `minLength: 1`.
- Required arrays should use `minItems: 1` when an empty collection would make
  the record invalid.
- Do not require placeholder values such as `unknown`, empty strings, zero, or
  fake hashes.

JSON Schema `default` values are annotations and do not modify instances.
Persisted documents must contain any value on which interpretation depends;
validators must not silently inject defaults.

### 15.8 Closed objects and controlled extension

All defined record objects use:

```json
{
  "additionalProperties": false
}
```

Use `unevaluatedProperties: false` instead where composition through `allOf`
makes it necessary. This prevents misspelled or silently ignored fields.

Extensibility must be explicit. Schemas that require implementation-specific
metadata may expose one `extensions` object with these rules:

- extension keys use reverse-domain names, for example
  `org.example.adapter_metadata`;
- extension values must be valid JSON;
- extensions cannot override normative core fields;
- required verification evidence cannot exist only in an extension;
- secrets, credentials, and unrestricted scratchpads are prohibited;
- consumers must preserve unknown extension entries when rewriting a record.

Do not add an `extensions` object to every embedded structure by default. Add
it only at a persistence or adapter boundary where a concrete need exists.

### 15.9 Time and duration

Persist timestamps as RFC 3339 UTC strings with a `Z` suffix:

```text
2026-09-16T09:30:00.123Z
```

The shared definition should combine `format: date-time` with a pattern that
requires UTC. Local times and numeric UTC offsets are not allowed in persisted
records.

Represent elapsed durations as non-negative integer milliseconds. Avoid
floating-point seconds because their serialized precision varies across
implementations. Where wall-clock and monotonic durations differ, store the
wall-clock timestamps plus the measured monotonic `duration_ms`.

### 15.10 Digests and content identity

Phase 1 uses SHA-256 as the required content digest. Encode it as lowercase
hexadecimal under an explicitly named property:

```json
{
  "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
}
```

The shared `sha256_digest` definition must enforce exactly 64 lowercase
hexadecimal characters. Do not prefix values with `sha256:` when the property
name already identifies the algorithm.

If another digest algorithm is later required, add a versioned digest object
in a backward-aware schema change rather than overloading the meaning of the
`sha256` field.

### 15.11 Paths and locators

Reusable packages store POSIX-style, case-relative paths regardless of the
host operating system.

A valid stored path must:

- be relative;
- use `/` separators;
- contain no empty, `.` or `..` segments;
- contain no NUL byte;
- not start with `/`, `~`, or a drive-letter prefix;
- resolve beneath the declared case or artifact root.

JSON Schema should reject obvious invalid forms. The semantic validator must
also resolve and contain the path beneath its expected root because regular
expressions alone cannot provide reliable filesystem containment.

Use URI fields for external locators. They must be absolute and must declare an
allowed scheme appropriate to their context. Downloadable public sources
should normally allow `https`; repository locators may additionally allow
documented version-control schemes. Local host paths must not be stored as
source locators.

### 15.12 Commands and environment variables

Store commands as argument arrays, not shell command strings:

```json
{
  "command": ["cmake", "--build", "build", "--parallel", "4"]
}
```

This avoids ambiguous quoting and implicit shell expansion. If a shell is
unavoidably required, record the shell executable and script artifact
explicitly.

Store environment variables as an object whose values are strings. Record only
the explicit, effective environment relevant to the build or execution.
Secrets and inherited host credentials are prohibited. Values that vary by
case root should use documented package-relative placeholders rather than
absolute host paths.

### 15.13 Enumerations

Use enums for closed research states such as verdicts, failure classes, stage
names, execution roles, and repair classes.

Rules for enum evolution:

- Never change the meaning of an existing value.
- Removing or renaming a value is a major schema change.
- Adding a value is considered compatible only when all declared consumers
  safely reject or preserve unknown values; otherwise it is a major change.
- Do not use catch-all values such as `other` without a companion explanatory
  field.
- Use `unknown` only for a genuine observed state, never as a substitute for a
  missing required value.

### 15.14 Numeric values and resource limits

Use integers for byte counts, counts, exit codes, signals, and durations.
Resource limits must be non-negative integers and include units in their
property names. Use explicit booleans or availability states when a limit is
unsupported or intentionally disabled; do not assign special meanings to
negative numbers.

Ratios and rates may use JSON numbers but must define their range, numerator,
denominator, and unit of analysis. Aggregate experiment metrics must retain
integer counts so a reported ratio can be independently checked.

### 15.15 Ordering and canonicalization

JSON object member order carries no meaning. Array order is meaningful only
when the schema explicitly says so, such as command arguments, pipeline stage
history, or ordered patch commits.

When hashing a JSON document itself, use a separately documented canonical
JSON serialization. Do not calculate a document hash from ordinary pretty
printed output. Artifact hashes cover the raw artifact bytes exactly as
stored.

### 15.16 Structural and semantic validation

Validation has two distinct layers.

JSON Schema structural validation checks:

- required properties;
- data types;
- formats and patterns;
- enum membership;
- numeric and collection bounds;
- conditional field presence;
- closed-object rules;
- local relationships expressible in one document.

Semantic validation checks properties requiring filesystem access,
cryptographic calculation, repository inspection, or comparison across
documents, including:

- artifact existence, size, and SHA-256 correctness;
- path containment;
- reference resolution and expected record type;
- schema-version availability;
- revision immutability and ancestry;
- vulnerable/patched revision and binary inequality;
- cache and layer separation;
- candidate identity across paired executions;
- environment comparability;
- required control presence;
- verdict consistency with policy and observations;
- migration provenance.

Structural validity alone must never be presented as evidence that a
reproduction is verified.

### 15.17 Validation behavior

Validators must:

- fail closed on an unknown schema name or unsupported schema version;
- report errors with document identity and JSON Pointer location;
- return all practical validation errors rather than only the first;
- avoid modifying the document being validated;
- avoid network access during validation;
- distinguish structural errors from semantic evidence failures;
- produce a machine-readable validation result;
- record validator name and version when validation is part of a pipeline run.

Warnings may describe deprecated fields or non-fatal portability concerns, but
warnings must not downgrade a violated required invariant into success.

### 15.18 Example-document conventions

Each implemented top-level schema should eventually include:

- one minimal valid example;
- one representative valid example;
- at least one invalid example for an important failure condition;
- a test showing that the valid examples pass;
- a test showing that each invalid example fails for the intended reason.

Examples involving vulnerable software must remain safe, project-local, and
non-weaponized. Synthetic fixtures should be clearly labeled and must not be
reported as real CVE reproductions.
