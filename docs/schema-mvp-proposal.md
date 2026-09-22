# Phase 1 Minimal Schema Proposal

## 1. Decision

Use eight persisted record schemas plus one small shared-definition library for
the first end-to-end Phase 1 implementation.

```text
common definitions (not persisted)

source-record ───────────────┐
                             v
artifact-record ──> vulnerability-record ──> environment-spec
                                                    |
                                                    v
                                              build-record
                                                    |
                                                    v
                                             execution-record
                                                    |
                                                    v
                                         verification-result
                                                    |
                                                    v
                                              case-manifest
```

The MVP is intentionally optimized for constructing and replaying one verified
case. Benchmark releases, controlled experiments, detailed attempt histories,
and presentation reports are later consumers of this core package.

The proposal has been adopted as the pre-runtime `schemas/0.1.0/` contract.
The former comprehensive `1.0.0` draft was removed before any real packages
depended on it.

## 2. Design limits

The MVP follows these limits:

1. A field is required only when it is needed to replay a case, verify its
   result, or diagnose why it failed.
2. Declarations and observations remain separate for environments and builds,
   but request and observation are combined for a single execution.
3. Raw logs, binaries, inputs, and traces remain external artifacts.
4. Provenance is recorded once per top-level record, not repeated on every
   nested value.
5. JSON Schema validates document-local structure. A small semantic validator
   handles relationships across records.
6. The first version preserves only the current state of a case. Detailed
   history and supersession are deferred until the pipeline actually needs
   them.
7. Identifiers are non-empty opaque strings with recommended prefixes. UUID
   version and URN grammar are not part of the MVP acceptance criteria.

## 3. Shared definitions

`common.schema.json` remains a library rather than a persisted record. It
should define only:

| Definition | Minimum shape |
|---|---|
| `record_id` | Non-empty string. |
| `case_id` | Non-empty string. |
| `timestamp` | RFC 3339 date-time. |
| `sha256` | 64 lowercase hexadecimal characters. |
| `relative_path` | Non-empty path that is not absolute and contains no `..` segment. |
| `record_ref` | `id` and `schema`. |
| `artifact_ref` | `id` and `sha256`. |
| `command` | Non-empty array of strings. |
| `provenance` | `created_at`, `created_by`, and optional `method` and `inputs`. |
| `failure` | Failure class, summary, and optional evidence artifacts. |
| `verdict` | `VERIFIED`, `NOT_REPRODUCED`, `INCONCLUSIVE`, or `INVALID_ENVIRONMENT`. |

Every persisted record uses this small envelope:

```yaml
schema: vulnerability-record
schema_version: 0.1.0
id: vulnerability-001
case_id: case-001       # omitted only when the record is intentionally global
provenance:
  created_at: 2026-09-17T00:00:00Z
  created_by: intake-tool
```

## 4. Persisted schemas

### 4.1 `source-record`

Stores one retrieved public source without trying to normalize its claims.

Required fields:

```text
schema, schema_version, id, case_id, provenance
source_type        advisory | repository | commit | issue | cwe | other
url
retrieved_at
retrieval_status   succeeded | failed
```

Conditional fields:

- Successful retrieval requires `content`, an artifact reference.
- Failed retrieval requires `error`, a short failure object.

Optional fields are `publisher`, `published_at`, `title`, `license`, and
`notes`. Raw response metadata may use a shallow `metadata` object.

### 4.2 `artifact-record`

Indexes immutable bytes stored outside structured records.

Required fields:

```text
schema, schema_version, id, case_id, provenance
kind
path
sha256
size_bytes
```

Optional fields are `media_type`, `producer`, `derived_from`, `description`,
and `available`. An unavailable artifact may omit path, digest, and size and
must include a reason; this is the only important conditional branch.

### 4.3 `vulnerability-record`

Combines normalized vulnerability metadata, revision resolution, and static
patch context.

Required fields:

```text
schema, schema_version, id, case_id, provenance
identifiers[]
title
summary
sources[]
repository.url
revisions.vulnerable
revisions.patched
revision_status      resolved | ambiguous | failed
```

Optional fields:

```text
cwe[]
affected_versions[]
fixed_versions[]
patch.commits[]
patch.diff_artifact
patch.changed_files[]
patch.changed_functions[]
root_cause
expected_signal
prerequisites[]
uncertainties[]
```

When `revision_status` is not `resolved`, the record requires a failure but
does not invent repository or revision values.

### 4.4 `environment-spec`

Declares one comparable vulnerable/patched build and execution environment.
Using one paired specification makes equality the default and role-specific
differences explicit.

Required fields:

```text
schema, schema_version, id, case_id, provenance
platform.os
platform.arch
isolation.type             docker
isolation.image_digest
toolchain                  shallow name-to-version object
dependencies               lock/manifest artifact references and policy
build.configure_commands[]
build.commands[]
network.acquisition
network.build              normally false
network.execution          normally false
limits.timeout_seconds
limits.memory_mb
```

Optional fields are environment variables, instrumentation, expected build
outputs, local service declarations, and `role_overrides`. Every role override
contains a reason; hidden vulnerable/patched divergence is prohibited by the
semantic validator.

Docker is the only supported build and execution environment. The image digest
is mandatory, and implementations must not fall back to host execution,
another container engine, a sandbox, or a virtual machine.

### 4.5 `build-record`

Records one actual vulnerable or patched build.

Required fields:

```text
schema, schema_version, id, case_id, provenance
role                    vulnerable | patched | control
environment_id
revision
source_tree_sha256
status                  succeeded | failed | invalid
started_at
completed_at
commands[]              command, exit code, stdout artifact, stderr artifact
```

A successful build requires at least one output artifact. A failed or invalid
build requires `failure`. Optional fields include observed tool versions,
dependency inventory, repairs, cache key, and deviations from the environment
specification.

### 4.6 `execution-record`

Combines the requested invocation and its observed outcome. A new record is
created for every run, so a separate execution specification is unnecessary
for the MVP.

Required fields:

```text
schema, schema_version, id, case_id, provenance
role                    vulnerable | patched | negative_control
comparison_group
build_id
executable              artifact reference
input                    artifact reference
input_role               candidate | benign_control
command[]
working_directory
environment              shallow string map; may be empty
limits
status                  completed | timed_out | resource_limited |
                        startup_failed | harness_failed
started_at
completed_at
stdout                  artifact reference
stderr                  artifact reference
```

Optional observations include exit code, terminating signal, sanitizer report,
stack trace, coverage summary, generated outputs, resource use, and output
truncation. Non-completed statuses require `failure`.

### 4.7 `verification-result`

Contains both the case-specific expectations and the deterministic oracle
result. A separate policy document becomes useful only when policies are reused
or independently versioned.

Required fields:

```text
schema, schema_version, id, case_id, provenance
expectations.target_signal
expectations.reachability
expectations.patched_behavior
executions.vulnerable
executions.patched
executions.negative_controls[]
checks[]                 id, passed, summary, evidence[]
verdict
rationale
evidence[]
```

Non-`VERIFIED` verdicts require `failure_class`. Optional fields include safe
behavior signals, uncertainty, limitations, and oracle tool identity.

The minimum checks are:

1. vulnerable and patched builds are valid and distinct;
2. all paired runs used the same candidate artifact;
3. the vulnerable run produced the target signal;
4. reachability or relevant state evidence exists;
5. the patched run did not produce the target signal or produced the expected
   safe behavior;
6. every negative control passed;
7. the observed difference is consistent with the patch or root cause.

### 4.8 `case-manifest`

Acts as the only root index and replay entry point.

Required fields:

```text
schema, schema_version, id, case_id, provenance
package_version
status                  draft | buildable | replayable | verified |
                        not_reproduced | inconclusive | invalid_environment
vulnerability_id
source_ids[]
environment_id
builds.vulnerable
builds.patched
artifact_ids[]
executions.vulnerable
executions.patched
executions.negative_controls[]
verification_result_id
replay.entry_point       artifact reference
replay.command[]
replay.working_directory
```

References may be absent while status is `draft` or `buildable`. A replayable
or final-verdict package requires the complete set. Optional fields are replay
prerequisites, known limitations, and a shallow schema-version map.

## 5. Current-to-MVP mapping

| Current schema | MVP treatment | Destination or reason |
|---|---|---|
| `common` | Keep and reduce | Shared primitives only. |
| `artifact-record` | Keep and reduce | Immutable external bytes. |
| `source-record` | Keep and reduce | Raw public evidence. |
| `validation-result` | Defer | Semantic validator may emit this after the core pipeline works. |
| `vulnerability-record` | Keep and broaden | Owns normalized metadata. |
| `revision-resolution` | Merge | Becomes `vulnerability-record.revisions`. |
| `patch-context` | Merge | Becomes `vulnerability-record.patch` and root-cause fields. |
| `environment-spec` | Keep and reduce | One paired specification with explicit overrides. |
| `build-record` | Keep and reduce | Actual per-role build observation. |
| `execution-spec` | Merge | Requested invocation fields move into `execution-record`. |
| `execution-record` | Keep and broaden | Request plus observation for one run. |
| `verification-policy` | Merge | Expectations move into `verification-result`. |
| `verification-result` | Keep and broaden | Expectations, checks, and verdict. |
| `case-manifest` | Keep and reduce | Current root index and replay descriptor. |
| `attempt-record` | Defer | Initially use failure and repair arrays on build/execution records. |
| `pipeline-run` | Defer | Operational state is not needed in the first replay package. |
| `benchmark-case` | Defer | Add after several manually replayed cases exist. |
| `experiment-manifest` | Defer | Add when RQ experiments are ready to run. |
| `experiment-result` | Defer | Add with the experiment runner. |
| `case-report` | Defer as a schema | Generate Markdown/HTML directly from the manifest and verdict. |

Nothing in the deferred group is prohibited. It simply does not block the
first reproducible case.

## 6. Cross-document semantic validator

The MVP semantic validator needs only these rules:

1. Every referenced record and artifact exists.
2. Referenced artifact digests match stored bytes.
3. All case-scoped records share the manifest's `case_id`.
4. Vulnerable and patched revisions, source-tree hashes, and output binaries
   are not accidentally identical unless explicitly justified.
5. Builds use the manifest's environment and the vulnerability record's
   revisions.
6. Compared executions use the same candidate digest and declared limits.
7. Control inputs or control dimensions differ exactly as declared.
8. The verification verdict follows the seven minimum checks in section 4.7.
9. Final manifest status agrees with the verification verdict.
10. Replay paths are relative and runtime network access is disabled unless
    explicitly reviewed.

These checks are ordinary deterministic code. They do not require an LLM,
agent framework, or a general rule engine.

## 7. Explicitly accepted limitations

The MVP does not initially provide:

- immutable supersession chains;
- detailed retry trajectories;
- reusable or separately versioned verification policies;
- generalized experiment aggregation;
- benchmark split access control;
- a machine-readable presentation report;
- field-level provenance for every normalized scalar;
- schema-level enforcement of all cross-record relationships.

Those features should be introduced only after a concrete case demonstrates
the need. Adding them later is easier than forcing every early pipeline stage
to populate them now.

## 8. Adoption recommendation

Do not mutate the current `1.0.0` family in place if any stored package already
depends on it. Instead, choose one of these paths:

- If no real packages exist, replace the current draft and label the MVP
  `0.1.0` until one end-to-end case succeeds.
- If packages already exist, keep `1.0.0` as the comprehensive format and add
  an MVP profile that explicitly identifies the required subset.

The project used the first option: the MVP is implemented as `0.1.0`. The
comprehensive field design remains documentation for evaluating later needs,
not a promise that all deferred records will be implemented.
