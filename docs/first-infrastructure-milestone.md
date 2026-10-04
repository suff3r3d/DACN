# First End-to-End Infrastructure Milestone

Status: the `0.2.0` contracts, compatibility tests, artifact storage, and
[package validator](package-foundation.md) are implemented. Builders, runners,
the oracle, and migration tooling remain planned. `schemas/0.1.0/`
remains available unchanged for legacy validation. See
[compatibility details](schema-compatibility.md).

## Objective and scope

Produce one replayable, manually reviewed public CVE case through a deterministic
pipeline, plus synthetic fixtures that exercise infrastructure failures. A real
case is complete only with CVE-specific evidence on the vulnerable build, safe
patched behavior, passing matched negative controls, and patch/code-region
attribution. A synthetic fixture does not count as a benchmark reproduction.

Use one Linux architecture and one project adapter initially. Accept explicit
source references, reviewed revisions, and a reference trigger. Preserve manual
interventions as evidence; this milestone measures infrastructure capability,
not autonomous reproduction performance. No CVE or architecture is selected by
this document.

Follow [AGENTS.md](../AGENTS.md), the
[MVP scope](schema-mvp-proposal.md), and the
[usage guide](schema-usage-guide.md). Advanced agents, automatic trigger
generation, automatic repair, broad CVE discovery, and experiment aggregation
remain deferred.

## Decision 1: Represent early failures without fictional runs

Keep package progress separate from a reproduction verdict. Before sufficient
inputs exist to invoke verification, retain a `draft` manifest and a structured
failure describing the last attempted stage. Do not manufacture a build,
execution, source hash, or replay entry point to satisfy final-state fields.

The `0.2.0` contract revision makes these bounded changes:

- Add optional manifest `failure`, containing `stage`, `class`, `summary`, and
  diagnostic artifact references. Require a nonempty evidence list when a
  failure is recorded. Use the existing failure taxonomy and pipeline stages.
- Allow partial manifest build/execution maps while the package is incomplete
  or has a non-success verdict. Every included reference must resolve to a real
  record. Empty maps may be omitted.
- Permit verification to consume partial execution references for non-success
  verdicts. Omit runs that never occurred; retain all attempted run records.
- Require final-status manifests to reference a verification result, but require
  complete paired builds, executions, controls, and replay only for `verified`
  and `replayable`. Other terminal statuses retain every available record and
  diagnostics without claiming replay capability.

Once case expectations exist, the verifier can report `INVALID_ENVIRONMENT`
from an observed Docker/build/startup failure without target execution. Its
environment check fails with diagnostic evidence; downstream checks are not
evaluated. If case expectations themselves are unavailable, retain the draft
failure rather than inventing expectations to issue a verdict.

Examples:

| Event | Persisted result |
|---|---|
| Advisory retrieval fails before expectations are defined | Failed source record, diagnostic artifact, draft manifest with `metadata_failure`. |
| Docker is unavailable for a prepared case | Preflight diagnostic, partial manifest, `INVALID_ENVIRONMENT`; no build or execution records. |
| Vulnerable compilation fails | Actual failed build record and logs, partial manifest, `INVALID_ENVIRONMENT`; no invented patched run. |
| All comparisons complete but controls contradict attribution | Actual comparison records and `INCONCLUSIVE`; replay included if available. |

A Docker availability failure belongs to `configuration_failure`; unsupported
required resource enforcement belongs to `resource_failure`. Record the concrete
reason. Diagnostics collected by the controller do not execute a target on the
host. If artifact persistence itself fails, return an explicit persistence error
and do not claim a successfully saved package.

## Decision 2: Distinguish failure from unavailable evaluation

In `0.2.0`, replace check `passed: boolean` with:

```text
status: passed | failed | not_evaluated
summary: nonempty explanation
evidence: artifact references
reason: required only for not_evaluated
```

Keep all seven check keys mandatory. Passed and failed checks require nonempty
evidence. A not-evaluated check may have empty evidence when no observation
exists, but must explain its missing prerequisite; reference diagnostic evidence
when available. Missing or truncated telemetry is not evidence of absence.
Overall verification evidence remains nonempty.

Evaluate verdicts with the following precedence:

1. Observed invalid environment, build identity, startup, or harness conditions
   yield `INVALID_ENVIRONMENT`.
2. Contradictory controls, different candidate inputs, unresolved comparability,
   or insufficient evidence needed for attribution yield `INCONCLUSIVE`.
3. With valid execution and adequate observations, an absent target signal or
   demonstrated failure to reach the target yields `NOT_REPRODUCED`.
4. Only seven passed checks yield `VERIFIED`.

An unevaluated downstream check caused solely by a conclusively absent target
signal does not prevent `NOT_REPRODUCED`; unexplained missing telemetry does.
The oracle must document which prerequisite caused every skipped check.
Timeouts and resource events require classification, never automatic success.
Implement this precedence as a tested decision table, with explicit competing
failure examples, rather than relying on narrative interpretation.

## Decision 3: Put executable assertions in a reviewed adapter

Keep expectations as human-readable descriptions. A trusted, versioned Python
adapter implements the case-specific interpretation of observations. Generic
code owns identity/integrity checks, comparison scheduling, verdict derivation,
and packaging. The adapter evaluates signal, reachability, safe behavior, and
patch consistency against reviewed ground truth and raw observations.

An adapter receives explicit records and artifact access and returns typed check
results with evidence references and diagnostic explanations. It cannot assign
the final verdict, silently change inputs, retrieve dependencies during
verification, or repair the target. Never load executable adapter code from
downloaded advisory content or an untrusted package.

Require `verification-result.oracle` for milestone output. Extend it in `0.2.0`
to identify the generic oracle name/version, adapter name/version, and artifact
references for the exact adapter implementation and reviewed case definition.
Retain hashes of those artifacts. Record the candidate/control identities,
source-backed expectations, intervention actor/reason, and comparison policy
in the case-definition artifact. Validate that configuration before use; keep
its interface small instead of introducing the deferred policy schema family.

Patch consistency requires executable observations tied to the reviewed patch
and relevant code region. Finding a sanitizer keyword or repeating the advisory
description is insufficient.

## Versioning and compatibility

Do not edit `0.1.0` semantics in place. Implement the revised family under
`schemas/0.2.0/`, with matching versioned schema IDs and offline registration.
Keep `0.1.0` validation available; new producers use `0.2.0`. The schemas and
contract tests exist; the migration procedure below is a requirement for future
tooling, not an implemented converter.

Migration preserves original records and artifacts. A legacy `passed: true`
maps to `status: passed`. A legacy false boolean is ambiguous: conversion must
use recorded evidence to distinguish `failed` from `not_evaluated`, or stop for
review. Never silently reinterpret it. Missing adapter identity is not invented;
legacy results can remain readable but require re-verification for milestone
acceptance. Preserve old-to-new record references and migration provenance.

## Components and implementation sequence

Python is the proposed implementation language, consistent with existing schema
tests. Keep these as ordinary modules and explicit interfaces, not agents.

| Order | Component | Inputs and outputs | Completion gate |
|---|---|---|---|
| 1 | Contracts and package foundation | Versioned records and artifact bytes → validated records, immutable artifacts, semantic diagnostics | Partial failures, hashes, reference types, paths, case IDs, roles, and migration behavior are tested. |
| 2 | Case preparation | Reviewed public source references and case configuration → source/artifact/vulnerability records | Revisions are immutable and distinct; material claims have evidence; interventions are recorded. |
| 3 | Docker acquisition and builder | Paired environment, revisions, dependencies → separate build records and binaries | Digest-pinned environment, measured tools/dependencies, bounded execution, independent source/output hashes. |
| 4 | Static extraction and runner | Patch, builds, candidate and controls → patch context and execution records | Raw diff retained; inferred context labeled; candidate and benign controls execute on both builds with complete observations. |
| 5 | Oracle | Reviewed expectations, artifacts, and actual executions → verification result | Seven checks and deterministic verdict precedence pass positive and adversarial tests. |
| 6 | Package/report/replay | Available records and verdict → manifest, report, replay entry point | Fresh isolated replay reproduces the evidence-backed verdict without hidden intervention. |

The semantic validator checks reference existence and type, case membership,
artifact size/hash and path containment, chronological consistency, correct
revision/build mapping, candidate equality, declared control differences,
comparison groups, limits, and manifest/verdict agreement. Validation cannot
prove source claims merely because they have evidence references.

Use unique run IDs and atomic publication of records. Interrupted operations
must preserve diagnostics and avoid publishing partial bytes as complete
artifacts. Resume only from integrity-checked completed stages; otherwise create
a new attempt without overwriting prior evidence. Detailed attempt schemas and
automatic retry remain deferred.

## Docker execution contract

All builds, targets, triggers, generated artifacts, and project tests run in
Docker. Host control code may inspect Docker and manage records, but must never
substitute host target execution. If Docker is unavailable, stop execution and
record the environment failure.

Dependency acquisition is an explicit network-enabled phase with retained
resolution results, checksums, and commands. Build and trigger phases use cached
inputs with network disabled. Record and enforce a common image digest,
architecture, toolchain, instrumentation, and limits across paired builds.
Retain justified role-specific differences explicitly.

Enforce elapsed time, memory, process count, disk capacity, and captured-output
size. Select and test an enforceable writable-storage strategy during builder
implementation; a declared disk limit is not enforcement. Unsupported required
limits stop the run. Terminate and collect bounded diagnostics for resource
events. Preserve truncation metadata instead of claiming complete telemetry.

Use separate source/build locations for each revision. Reject accidental equal
revisions, source trees, or executables for this first case. The same candidate
bytes run on both builds; matched benign inputs run on both as negative controls.
Observe tool versions and dependency inventory rather than copying declarations.

## Test and acceptance plan

Run schema, unit, and integration tests in a digest-pinned Docker test
environment. Mock metadata services and use synthetic targets for ordinary
integration tests. Acquire test dependencies separately from offline execution.

Required scenarios include:

- Valid paired behavior and safe negative controls.
- Valid execution with absent target signal or confirmed missed reachability.
- Same signal on patched or benign runs, and unrelated crashes.
- Missing telemetry, malformed or truncated reports, and timed-out execution.
- Docker unavailable, build failure, unsupported limits, and interrupted resume.
- Same vulnerable/patched revision or binary, mismatched candidate, cross-case
  references, artifact corruption, and manifest/verdict disagreement.
- Unknown schema version, legacy ambiguous false checks, and truthful partial
  failure packages with no invented execution records.

The milestone is accepted only when one reviewed real CVE yields `VERIFIED`, all
required controls pass, structural and semantic validation pass, and a fresh
replay using preserved inputs yields the same verdict and relevant observations.
Record pipeline/schema/adapter versions and manual intervention level. Synthetic
failure scenarios must demonstrate all three non-success verdicts. Keep failed
case evidence and report uncertainty; a difficult case cannot be promoted to
success to complete the milestone.

The report includes environment and trigger status, both candidate executions,
negative controls, code/root-cause evidence, verdict, limitations, artifact links,
and replay instructions. No aggregate research success rate is claimed from one
development case.

## Remaining implementation choices

Select the real CVE, supported architecture, immutable images, dependency
inventory method, and enforceable disk-limit mechanism during their respective
implementation steps. Verify platform capabilities before choosing a target.
The official wording of RQ1.1/RQ1.2 is not present in the reviewed repository;
experiment design awaits that source. These choices do not alter the evidence
or verification acceptance criteria above.
