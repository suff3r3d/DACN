# Schema Compatibility: 0.1.0 and 0.2.0

## Implemented boundary

Both families contain eight persisted record schemas and a common definition
library. `0.1.0` is preserved byte-for-byte. `0.2.0` is the contract for new
record producers. Artifact storage and the
[semantic package validator](package-foundation.md) are implemented; builders,
execution harness, a migration command, and the oracle remain planned.

Register schemas offline by full `$id` and select the exact `schema` plus
`schema_version`. Unsupported versions fail explicitly. Loading both versions
does not convert records or validate cross-record links. Package version is
independent of schema version.

## Changes

| Contract | 0.2.0 behavior |
|---|---|
| Manifest failure | Optional `failure` with pipeline stage, existing failure class, summary, and nonempty diagnostic evidence. Requires a nonempty artifact inventory. Forbidden for `verified`. |
| Manifest progress | Partial build/execution maps allowed for incomplete or non-success packages. Omit absent roles and empty maps. |
| Final manifest | `verified` and `replayable` still require complete records and replay. Other final statuses require verification-result ID and artifact inventory, without fabricated runs. |
| Verification executions | Optional for non-success results; nonempty partial maps allowed. `VERIFIED` requires all three comparison roles and at least one negative control. |
| Check state | `status: passed | failed | not_evaluated` replaces `passed: boolean`. All seven named checks remain required. |
| Check evidence | Passed/failed checks need evidence. Not-evaluated checks need a `reason` and may have empty evidence. A reason is forbidden on evaluated checks. Overall evidence remains nonempty. |
| Success consistency | `VERIFIED` requires seven passed checks and no failure class. Non-success requires a failure class and at least one check that did not pass. |
| Oracle identity | Requires oracle name/version, adapter name/version and implementation artifact reference, and reviewed case-definition artifact reference. |

Other schemas differ only in their version constants and versioned references.
Docker-only isolation, digest pinning, resource fields, role labels, provenance,
and raw artifact references retain their existing contracts.

## Compatibility and future migration procedure

Existing data can continue to be read and validated as `0.1.0`; a schema-version
edit is not migration. When a future migration tool is implemented, it must:

1. Validate the original record against its original schema and preserve its
   exact bytes and raw artifacts.
2. Create new record IDs, retain a mapping from old IDs to new IDs, and update
   references consistently. Preserve the case ID and record migration inputs,
   actor, timestamp, and method in provenance.
3. Map a legacy `passed: true` to `status: passed` only as a representation
   change, preserving the claim and evidence rather than asserting new truth.
4. Treat legacy `passed: false` as ambiguous. Review original observations to
   distinguish an observed failure from missing evaluation. If the evidence
   cannot resolve it, stop migration for review and retain the legacy record.
5. Supply actual oracle/adapter/case-definition identities. If these cannot be
   recovered, keep legacy validation available and require re-verification for
   acceptance under the verification contract. Never invent identity, hashes, skip reasons, or runs.
6. Validate the new records and package relationships. A converted boolean or
   structurally valid record is not evidence of successful reproduction.

The test suite verifies side-by-side version registration, wrong/unknown-version
rejection, rejection of legacy booleans in `0.2.0`, and the requirement for newly
required identities. It does not claim to test an unimplemented migration tool
or automatically resolve the meaning of false checks.

## Structural limits

JSON Schema validates references' shapes, not existence, hash correctness,
ownership, or the contents of evidence. Partial records can be structurally
valid while semantically contradictory. The package validator checks paired
identities, retained references, artifact integrity, case membership, and
manifest/verdict agreement. It supports `0.2.0` semantic validation only;
legacy validation remains structural until an explicit migration is performed.
Evidence interpretation and verdict derivation remain oracle work. No schema
or package validation result alone is a CVE reproduction verdict.
