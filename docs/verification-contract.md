# Verification and Execution Contract

This document defines the evidence required for a CVE reproduction and the
boundaries between execution, validation and verification. It specifies behavior;
it does not imply that a builder, runner or oracle is implemented. See
[package foundation](package-foundation.md) for available APIs and their limits.

## Evidence and incomplete packages

A reproduction requires vulnerability-specific evidence on a vulnerable build,
safe behavior on the patched build, passing matched negative controls and
attribution to the patch or relevant code region. Synthetic fixtures exercise
infrastructure but do not count as real CVE reproductions.

Before case expectations are available, retain a draft manifest and a structured
failure for the attempted stage. Never invent builds, executions, hashes or replay
entry points. When expectations exist, an observed environment failure can support
`INVALID_ENVIRONMENT` without target execution. Retain diagnostic evidence and
mark downstream checks as not evaluated.

| Condition | Evidence and result |
| --- | --- |
| Advisory retrieval fails before expectations exist | Failed source record, diagnostic artifact, draft manifest with `metadata_failure`. |
| Docker unavailable for a prepared case | Preflight evidence, `configuration_failure`, `INVALID_ENVIRONMENT`; no fictional runs. |
| Required resource enforcement unavailable | Diagnostic evidence and `resource_failure`; do not run without required limits. |
| Compilation fails | Actual failed build record and logs; no invented downstream execution. |
| Controls contradict target attribution | Retained comparison evidence and `INCONCLUSIVE`. |
| Artifact persistence fails | Explicit persistence error; do not claim a saved package. |

Partial record requirements and version differences are defined in
[schema compatibility](schema-compatibility.md). Artifact availability is not proof
of the claim it is cited to support.

## Check states and verdict precedence

All seven verification checks are required. Each uses `passed`, `failed`, or
`not_evaluated`, with a summary and evidence references. Passed and failed checks
require evidence. An unevaluated check requires a reason and may have no evidence
if no observation exists. Overall verification evidence remains nonempty.

Apply the following precedence:

1. Invalid environment, build identity, startup or harness conditions yield
   `INVALID_ENVIRONMENT`.
2. Contradictory controls, different candidate inputs, unresolved comparability,
   or insufficient attribution evidence yield `INCONCLUSIVE`.
3. With valid execution and adequate observations, an absent target signal or
   demonstrated failure to reach the target yields `NOT_REPRODUCED`.
4. Only seven passed checks yield `VERIFIED`.

A downstream check skipped solely because the target signal is conclusively
absent does not prevent `NOT_REPRODUCED`; unexplained missing telemetry does.
Record the prerequisite behind each skipped check. A timeout, crash, truncated
log or sanitizer keyword alone is never sufficient evidence of reproduction.
Verdict logic requires tests for competing failure conditions.

## Oracle and adapter boundaries

A trusted, versioned adapter interprets case-specific signals, reachability,
patched behavior and patch consistency. It consumes explicit records and artifact
access and returns typed check results with evidence and explanations. Generic
oracle code owns identity checks, comparison policy and final verdict derivation.

An adapter cannot assign the final verdict, silently change inputs, retrieve
dependencies during verification or repair the target. Never load executable code
from downloaded advisories or untrusted case content.

The `verification-result.oracle` contract records the oracle and adapter identities,
the exact adapter implementation artifact and a reviewed case-definition artifact.
The case definition records candidate/control identities, source-backed expectations,
comparison policy and intervention actor/reason. Retain artifact hashes and validate
the definition before use. Repeating the advisory is not patch attribution.

## Paired Docker execution

Builds, targets, triggers, generated artifacts and project tests run in Docker.
If Docker is unavailable, stop execution; do not substitute another runtime.
Host control code may inspect Docker and manage records without executing targets.

Dependency acquisition is a separate, controlled network-enabled phase. Preserve
resolved versions, checksums and commands. Builds and trigger execution use cached
inputs with networking disabled. Use the same image digest, architecture,
toolchain, instrumentation and limits across paired builds; record and justify
any asymmetry. The current validator's stricter supported comparison policy is
documented in [package foundation](package-foundation.md).

Use independent source/build locations and check revision, source-tree and binary
hashes to detect accidental reuse. Run the same candidate bytes on both builds and
matched benign controls on both. Observe installed tool and dependency versions
rather than copying declarations into result records.

Enforce elapsed time, memory, process count, writable disk capacity and output size.
A declared disk limit without an enforcement mechanism is insufficient. Unsupported
required limits stop execution. Record resource events and truncation explicitly.

## Publication, replay and reporting

Use unique record identities and atomic publication. Preserve diagnostics after
interruption; never publish partial artifact bytes as complete. Resume only from
integrity-checked completed stages, or create a new attempt without overwriting
prior evidence. Storage behavior is specified in [package foundation](package-foundation.md).

A complete reproduction must pass paired checks and package validation, and a
fresh isolated replay must reproduce the verdict and relevant observations.
Record pipeline, schema and adapter versions and the degree of manual intervention.
Reports include environment and trigger status, both candidate runs, negative
controls, code-region evidence, verdict, uncertainty, artifact links and replay
instructions. Failed cases remain part of the research data; one development case
does not justify an aggregate success-rate claim.

Contract tests cover valid comparisons, absent signals, unrelated crashes, failed
controls, missing/truncated telemetry, timeouts, invalid environments, interrupted
publication, identity mismatches, corrupt artifacts and unsupported schema versions.
Use mocked metadata and synthetic fixtures for routine tests; see the
[Docker test workflow](../tests/schema/README.md).
