# Schema Consistency Review

## 1. Scope

This review covers `docs/schema-plan.md` and
`docs/schema-field-design.md`. It checks the complete Phase 1 schema family for:

- schema inventory and canonical names;
- record and entity identifiers;
- cross-record reference direction;
- lifecycle and supersession behavior;
- shared enums and status meanings;
- requiredness and conditional fields;
- artifact integrity and validation flow;
- paired vulnerable/patched/control invariants;
- provenance and failure classification;
- benchmark and experiment separation.

This review covers the comprehensive future-facing design. The active
implementation is the reduced MVP under `schemas/0.1.0/`; its structural and
reference integrity is checked by the offline tests under `tests/schema/`.

## 2. Result

The comprehensive documentation contains matching plans and field designs for
the following 20 possible schemas:

1. `common`
2. `artifact-record`
3. `source-record`
4. `validation-result`
5. `vulnerability-record`
6. `revision-resolution`
7. `patch-context`
8. `environment-spec`
9. `build-record`
10. `execution-spec`
11. `execution-record`
12. `verification-policy`
13. `verification-result`
14. `case-manifest`
15. `attempt-record`
16. `pipeline-run`
17. `benchmark-case`
18. `experiment-manifest`
19. `experiment-result`
20. `case-report`

The schema plan and field-design inventory agree. The MVP intentionally
implements only the eight persisted records selected in
`docs/schema-mvp-proposal.md`, using `0.1.0` schema identities. The other
records remain deferred design material.

## 3. Findings and Resolutions

### 3.1 Validation schema missing from the plan

**Finding:** `validation-result` was introduced by the artifact-integrity
design but was absent from the original schema inventory and priority list.

**Resolution:** Added it to the plan as a cross-cutting foundation schema and
renumbered the implementation priorities to cover 20 schemas.

### 3.2 Case identity conflated with manifest identity

**Finding:** `case-manifest.record_id` originally used the `case` record kind.
Creating a superseding manifest would therefore either change the case identity
or reuse a record ID for different content.

**Resolution:** A stable `case_id` now identifies the research case, while
`case-manifest.record_id` uses the `case-manifest` kind and identifies one
immutable manifest version. Benchmark cases and reports carry both the stable
case ID and the exact manifest record ID they reviewed or summarized.

### 3.3 Back-references created validation cycles

**Finding:** Build and execution records referenced validation results that can
only be produced after those records exist. This created unnecessary forward
references and complicated immutable publication.

**Resolution:** Removed validation-result IDs from build and execution records.
Validation results point to their checked subjects. Verification results,
pipeline runs, case manifests, and experiment results may index the validation
records they consumed because they are produced later in the dependency order.

### 3.4 Mutable integrity state conflicted with immutable evidence

**Finding:** The initial artifact design placed general integrity status and
last-check information inside the artifact record.

**Resolution:** Artifact records now contain registration-time size, SHA-256,
timestamp, and actor only. Every later integrity check creates an immutable
`validation-result` record.

### 3.5 Manual capture policy lacked fields

**Finding:** The settled rules permitted controlled manual source capture but
the source schema did not record its reason or intervention level.

**Resolution:** Added a conditional manual-capture object with actor, reason,
capture time, original locator, intervention level, and proof that original
content was preserved. Automated evaluation still prohibits manual capture.

### 3.6 Failed retrieval content was ambiguous

**Finding:** An unsuccessful retrieval could place a diagnostic response body
in `content_artifact`, making it unclear whether the artifact was source
evidence or error evidence.

**Resolution:** `content_artifact` is now reserved for successful source
content. Failed-response bodies and diagnostics use
`retrieval.error_artifact`.

### 3.7 Source dates could acquire invented precision

**Finding:** Source publication, modification, and disclosure dates required a
UTC timestamp even when a source publishes only a calendar date.

**Resolution:** Added `source_temporal_value`, which preserves date versus
date-time precision and the exact raw source representation. Pipeline-observed
times continue to require UTC timestamps.

### 3.8 Failed revision resolution required a repository

**Finding:** `revision-resolution.repository` was required even when repository
identity itself could not be resolved.

**Resolution:** The repository is mandatory for resolved results and
conditional for ambiguous/failed results. A failed resolution still requires
evidence and a `revision_failure` record.

### 3.9 Shared vocabulary was repeated informally

**Finding:** Pipeline stages, execution roles, verification verdicts, and
intervention levels appeared in several schemas without canonical shared
definitions.

**Resolution:** Added shared definitions to `common` and retained narrower
schema-specific subsets only where justified.

### 3.10 Control builds lacked source ancestry

**Finding:** A build role of `control` did not say whether it was based on the
vulnerable or patched source revision.

**Resolution:** The source-build identity now includes
`comparison_source_role`, restricted to `vulnerable` or `patched`.

### 3.11 Repeated executions conflicted with policy wording

**Finding:** The policy required exactly one vulnerable and patched run even
though repeatability experiments may require multiple runs.

**Resolution:** Policies require at least one of each and explicitly declare
minimum and maximum run counts.

### 3.12 Non-verified verdict classification was underspecified

**Finding:** `verification-result.failure_class` was only conditionally
described as applicable, allowing unexplained negative outcomes.

**Resolution:** A failure class is required for every verdict except
`VERIFIED`. Rationale and evidence remain required independently.

### 3.13 Interrupted and cancelled lifecycle records lacked reasons

**Finding:** Attempt and pipeline records required failures for failed states
but did not require an explanation for interruption or cancellation.

**Resolution:** Added conditional `termination_reason` fields for interrupted
and cancelled states.

### 3.14 Unavailable artifacts required a known media type

**Finding:** An artifact that could not be obtained still required a media type,
which could force an invented value.

**Resolution:** Media type is required for available or quarantined bytes and
optional when the artifact is unavailable.

### 3.15 Bidirectional lifecycle references require coordinated publication

**Finding:** Attempts reference produced records while build, execution, and
verification records reference the attempt that produced them. Pipeline runs
and attempts have a similar bidirectional association.

**Resolution:** IDs are allocated before work starts. The attempt/output set is
published as one consistency unit, and released packages require all references
to resolve. Transient running state is operational state, not final research
evidence.

### 3.16 Aggregate validation indexes could reference themselves

**Finding:** Verification results, case manifests, pipeline runs, and experiment
results contained validation-result indexes whose descriptions could include
validation of the containing record. Such validation necessarily occurs after
the immutable subject exists and would create a forward self-reference.

**Resolution:** These indexes now contain only validation results consumed as
inputs. Validation of the containing record remains external. A later
superseding manifest may index validation of an earlier manifest, but an
immutable record cannot reference its own future validation result.

## 4. Canonical Identity Rules

The review establishes these distinctions:

| Identity | Meaning | Stability |
|---|---|---|
| `record_id` | One immutable persisted document | Never reused for different content |
| `case_id` | One research case across manifest versions | Stable across supersession |
| Local ID | One embedded object inside its parent | Unique only within that scope |
| Artifact SHA-256 | Exact stored byte content | Changes whenever bytes change |
| `case_key` | Human-readable lookup key | Stable where practical, not a reference key |

Every field ending in `_id` must document whether it is a stable entity ID, a
resolvable record reference, or a parent-local ID.

## 5. Reference Direction

The authoritative dependency direction is:

```text
source/artifact evidence
  -> normalized vulnerability
  -> revision resolution
  -> patch context
  -> environment specification
  -> build record
  -> execution specification and record
  -> verification policy and result
  -> case manifest and report
  -> benchmark and experiment aggregation
```

Validation results point to already created subjects. Checked records do not
point forward to later validation results. Later aggregate records may index
validation results they consumed as inputs, but never validation of themselves.

Two intentional bidirectional relationships remain:

- source snapshots and their acquired artifact records;
- attempts and the output records they produced.

Both use preallocated IDs and coordinated publication. Released packages may
not contain dangling references.

## 6. Canonical Status Boundaries

- Build success means required build commands completed and expected outputs
  were registered. It does not mean the environment is valid for verification.
- Execution completion means the bounded invocation finished. It does not mean
  a vulnerability was reproduced.
- Artifact registration records byte identity. Later validation proves the
  stored bytes still agree.
- Package `replayable` means the package can be rerun in its declared Docker
  container. It does not mean `VERIFIED`.
- Only `verification-result.verdict` determines reproduction outcome.
- Benchmark ground truth is human-reviewed reference data, not an automated
  pipeline result.
- Experiment aggregates cannot count `INCONCLUSIVE` or
  `INVALID_ENVIRONMENT` as successful reproductions.

## 7. Remaining Implementation Checks

No unresolved documentation conflict currently blocks implementation. The
following checks must be enforced when JSON Schemas and semantic validators are
implemented:

1. Every `_id` field resolves to the expected record kind where it is a record
   reference.
2. Stable `case_id` values agree across all case-scoped records.
3. No released package contains dangling bidirectional references.
4. All enum uses reference the canonical common definition or an explicitly
   documented subset.
5. Every conditional rule has both a valid and invalid fixture.
6. Cross-document verdict invariants are tested semantically rather than
   assumed from structural validity.
7. Schema-plan and field-design inventories remain synchronized as versions
   evolve.
