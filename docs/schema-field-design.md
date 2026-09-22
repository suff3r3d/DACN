# Foundation Schema Field Design

> **Status:** This is the comprehensive future-facing design retained for
> reference. The active pre-runtime contract is the smaller `0.1.0` MVP in
> `docs/schema-mvp-proposal.md` and `schemas/0.1.0/`. Deferred schemas in this
> document are not current implementation requirements.

## 1. Scope

This document designs the complete Phase 1 schema family field-by-field. It
starts with shared definitions and evidence records, then covers vulnerability
understanding, reconstruction, execution, verification, packaging, lifecycle,
benchmark, experiment, and reporting records.

It is a design specification, not an implementation. The tables below define
the intended JSON shape, requiredness, structural constraints, and semantic
rules that later JSON Schema files and validators must implement.

The design follows the conventions in `docs/schema-plan.md`:

- JSON Schema Draft 2020-12;
- immutable, versioned schema URNs;
- strict objects;
- UTC timestamps;
- SHA-256 content digests;
- POSIX-style case-relative paths;
- explicit provenance;
- no embedded large artifacts;
- no dependency on an LLM or agent framework.

## 2. Notation

The field tables use these terms:

- **Required**: the property must be present.
- **Conditional**: the property is required only under a stated condition.
- **Optional**: the property may be omitted when it is not applicable or was
  not collected.
- **Semantic**: the rule requires checks beyond ordinary JSON Schema
  validation.

All objects are closed by default. Implementations should use
`additionalProperties: false`, or `unevaluatedProperties: false` where schema
composition requires it.

## 3. `common.schema.json`

### 3.1 Purpose

`common.schema.json` is a definition library. It is not an independently
persisted document and therefore does not use the persisted-document envelope.
Other schemas reference its definitions by immutable URN.

Proposed canonical identity:

```text
urn:dacn:schema:common:1.0.0
```

### 3.2 Primitive definitions

#### `$defs/non_empty_string`

| Constraint | Value |
|---|---|
| JSON type | `string` |
| Minimum length | `1` |

This is a structural primitive. Domain fields should impose tighter maximum
lengths where practical.

#### `$defs/schema_name`

| Constraint | Value |
|---|---|
| JSON type | `string` |
| Pattern | `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$` |

Examples: `artifact-record`, `execution-spec`, `verification-result`.

#### `$defs/semantic_version`

| Constraint | Value |
|---|---|
| JSON type | `string` |
| Pattern | strict SemVer 2.0.0 without a leading `v` |

Examples: `1.0.0`, `1.2.0-rc.1`. Persisted production packages should use
released versions rather than prerelease schema versions.

#### `$defs/record_id`

| Constraint | Value |
|---|---|
| JSON type | `string` |
| Format | absolute URI |
| Pattern | `^urn:dacn:[a-z][a-z0-9-]*:[0-9a-fA-F-]{36}$` |

The last segment is a canonical UUID string. UUIDv7 is preferred; UUIDv4 is an
acceptable fallback. A semantic validator should verify that the UUID version
is allowed and that the identifier is unique in its dataset.

The same lexical form is used for stable entity IDs such as `case_id`. A
`record_id` identifies one immutable persisted document and must resolve when
used in a record reference. A stable entity ID groups successive records and
does not itself imply that a document with that ID exists. Field descriptions
must state when an ID is an entity identity rather than a record reference.

#### `$defs/stable_entity_id`

Uses the same lexical constraints as `record_id`, but represents a stable
entity identity rather than a resolvable immutable document. The distinction
is semantic and must be explicit in the consuming field description.

#### `$defs/local_id`

Used for objects that are addressable only within a parent document, such as a
claim or validation finding.

| Constraint | Value |
|---|---|
| JSON type | `string` |
| Pattern | `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$` |
| Maximum length | `128` |

Local IDs must be unique within the array or object that contains them.

#### `$defs/utc_timestamp`

| Constraint | Value |
|---|---|
| JSON type | `string` |
| Format | `date-time` |
| Pattern | RFC 3339 date-time ending in `Z` |

Examples: `2026-09-16T09:30:00Z` and
`2026-09-16T09:30:00.123456Z`. Numeric offsets and local times are rejected.

#### `$defs/source_temporal_value`

Represents a time asserted by a public source without inventing precision.

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `precision` | enum | Required | `date` or `date_time`. |
| `value` | string | Required | `date` format for date precision; UTC timestamp for date-time precision. |
| `raw_value` | non-empty string | Required | Exact source representation. |

Internally observed pipeline times continue to use `utc_timestamp`.

#### `$defs/duration_ms`

| Constraint | Value |
|---|---|
| JSON type | `integer` |
| Minimum | `0` |

#### `$defs/byte_count`

| Constraint | Value |
|---|---|
| JSON type | `integer` |
| Minimum | `0` |

#### `$defs/sha256_digest`

| Constraint | Value |
|---|---|
| JSON type | `string` |
| Pattern | `^[0-9a-f]{64}$` |

The digest is lowercase hexadecimal and covers the raw stored bytes exactly.

#### `$defs/media_type`

| Constraint | Value |
|---|---|
| JSON type | `string` |
| Pattern | syntactically valid media type without free-form comments |

Examples: `application/json`, `text/plain`, `application/octet-stream`.
Parameters such as character encoding may be included when known.

#### `$defs/relative_path`

| Constraint | Value |
|---|---|
| JSON type | `string` |
| Minimum length | `1` |
| Representation | POSIX-style relative path |

Structural validation should reject leading `/`, leading `~`, backslashes,
NUL bytes, empty segments, `.` segments, `..` segments, and drive-letter
prefixes. Semantic validation must resolve the path and verify containment
beneath its declared root.

#### `$defs/absolute_uri`

| Constraint | Value |
|---|---|
| JSON type | `string` |
| Format | `uri` |

Context-specific schemas must further restrict allowed schemes.

#### `$defs/json_pointer`

| Constraint | Value |
|---|---|
| JSON type | `string` |
| Format | JSON Pointer syntax |

The empty string may represent the document root. Non-empty pointers begin
with `/` and use RFC 6901 escaping.

### 3.3 Persisted-document envelope

Define `$defs/record_envelope` for composition into every independently
persisted record.

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Schema-specific constant, such as `artifact-record`. |
| `schema_version` | semantic version | Required | Schema-specific constant matching the validating schema. |
| `record_id` | record ID | Required | Stable, globally unique identifier for this record. |
| `created_at` | UTC timestamp | Required | Time this record was first persisted. |
| `created_by` | actor identity | Required | Actor responsible for creating the record. |

The envelope intentionally excludes `updated_at`. Phase 1 evidence records
should be append-only. A material correction creates a new record and links it
to the superseded record instead of silently rewriting evidence.

### 3.4 Record references

#### `$defs/record_reference`

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `record_id` | record ID | Required | Identifier of the referenced document. |
| `schema_name` | schema name | Required | Expected target schema. |

Semantic validation must resolve the ID, verify the target exists, and confirm
that its declared `schema_name` matches the reference. A reference does not
contain a filesystem path.

#### `$defs/artifact_reference`

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `artifact_id` | record ID | Required | `record_id` of an `artifact-record`. |
| `sha256` | SHA-256 digest | Required | Expected content hash, preventing silent retargeting. |

The identifier must use the `artifact` record kind. Semantic validation must
resolve the record and verify that both the referenced metadata and stored
bytes agree with `sha256`.

#### `$defs/record_or_artifact_reference`

Accepts exactly one `record_reference` or `artifact_reference`. It is used only
where a stage input or output may legitimately be either kind; domain fields
should prefer the narrower reference whenever possible.

### 3.5 Actor and tool identity

#### `$defs/tool_identity`

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `name` | non-empty string | Required | Stable tool or program name. |
| `version` | non-empty string | Required | Observed version output or immutable release identifier. |
| `executable` | string | Optional | Portable executable name, not a host-specific absolute path. |
| `sha256` | SHA-256 digest | Optional | Hash of the exact executable or packaged tool when available. |
| `configuration_artifact` | artifact reference | Optional | Configuration affecting the operation. |

`version` may be `unavailable` only when version discovery was attempted and
the surrounding record explains why it could not be determined. Empty or
invented version values are prohibited.

#### `$defs/actor_identity`

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `actor_type` | enum | Required | `tool`, `human`, or `system`. |
| `actor_id` | non-empty string | Required | Stable tool ID, system component name, or pseudonymous reviewer ID. |
| `tool` | tool identity | Conditional | Required when `actor_type` is `tool`; prohibited otherwise. |

Names, email addresses, credentials, and other unnecessary personal data must
not be stored. Human review can use a project-local pseudonymous identifier.

### 3.6 Provenance

#### `$defs/provenance_event`

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `activity_id` | stable entity ID | Required | Activity identity using the `activity` kind; it is not a record reference. |
| `activity_type` | enum | Required | See the activity types below. |
| `performed_by` | actor identity | Required | Actor that performed the activity. |
| `started_at` | UTC timestamp | Required | Activity start. |
| `completed_at` | UTC timestamp | Required | Activity completion. |
| `method` | non-empty string | Required | Concise method, resolver, adapter, or procedure name. |
| `input_records` | array of record references | Optional | Structured inputs; unique by `record_id`. |
| `input_artifacts` | array of artifact references | Optional | Artifact inputs; unique by `artifact_id`. |
| `command` | array of strings | Optional | Exact argument vector when a command was executed; at least one item. |
| `exit_code` | integer | Optional | Process exit status when applicable. |
| `notes` | string | Optional | Concise limitations or context; not an unrestricted log. |

Allowed `activity_type` values for v1:

- `acquisition`;
- `normalization`;
- `revision_resolution`;
- `static_extraction`;
- `dependency_resolution`;
- `build`;
- `execution`;
- `verification`;
- `migration`;
- `manual_review`;
- `reporting`;
- `other`.

When `activity_type` is `other`, a separate `activity_type_detail` field is
required. `completed_at` must not precede `started_at`.

The implementation exposes the activity enum as `$defs/activity_type` and
command argument arrays as `$defs/command` so later schemas reuse identical
constraints.

### 3.7 Evidence-backed claims

#### `$defs/claim_classification`

Allowed values:

- `confirmed_fact`;
- `strong_inference`;
- `hypothesis`;
- `unknown`.

#### `$defs/confidence_assessment`

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `level` | enum | Required | `high`, `medium`, `low`, or `unknown`. |
| `rationale` | non-empty string | Required | Why this level was assigned. |
| `method` | non-empty string | Optional | Named rubric or calculation method. |

A numeric probability is deliberately excluded from v1 because the project
does not yet define a calibrated probability model.

#### `$defs/evidence_reference`

Exactly one target must be supplied.

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `source_id` | record ID | Conditional | References a `source-record`. |
| `artifact` | artifact reference | Conditional | References stored executable or documentary evidence. |
| `record` | record reference | Conditional | References another structured record. |
| `location` | evidence location | Optional | Pinpoints supporting material within the target. |
| `supports` | boolean | Required | `true` for supporting evidence, `false` for contradicting evidence. |
| `note` | string | Optional | Concise explanation of relevance. |

`location` is a closed object that may contain one appropriate locator:

- `json_pointer` for structured documents;
- `line_start` and optional `line_end` for text;
- `symbol` for source code;
- `commit_path` plus optional line information for repository content.

#### `$defs/normalized_claim`

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `claim_id` | local ID | Required | Unique within the parent record. |
| `field_path` | JSON Pointer | Required | Normalized field to which the claim applies. |
| `raw_value` | any JSON value | Required | Source value preserved without normalization. |
| `normalized_value` | any JSON value | Required | Value produced by normalization. |
| `classification` | claim classification | Required | Epistemic category of the claim. |
| `confidence` | confidence assessment | Required | Evidence-based confidence and rationale. |
| `evidence` | array of evidence references | Required | At least one item. |
| `disposition` | enum | Required | `accepted`, `conflicting`, `rejected`, or `unresolved`. |
| `rationale` | non-empty string | Required | Transformation, acceptance, or rejection rationale. |
| `provenance` | provenance event | Required | How the normalized claim was produced. |

The `raw_value` must remain faithful to the referenced source. If parsing or
redaction changes it, the derived value must instead be stored in an artifact
with provenance.

### 3.8 Status and failure definitions

#### `$defs/stage_status`

Allowed values:

- `pending`;
- `running`;
- `succeeded`;
- `failed`;
- `skipped`;
- `interrupted`.

#### `$defs/pipeline_stage`

Allowed values are `collect`, `normalize`, `resolve`, `build`, `extract`,
`execute`, `verify`, and `report`.

#### `$defs/verification_verdict`

Allowed values are `VERIFIED`, `NOT_REPRODUCED`, `INCONCLUSIVE`, and
`INVALID_ENVIRONMENT`.

#### `$defs/execution_role`

Allowed values are `vulnerable`, `patched`, `negative_control`, and
`environment_control`.

#### `$defs/intervention_level`

Allowed values, ordered from least to most intervention, are `none`,
`configuration_only`, `human_ground_truth`, `manual_strategy`,
`manual_artifact_edit`, and `other`.

#### `$defs/record_status`

Allowed values:

- `draft`;
- `complete`;
- `invalid`;
- `superseded`.

`complete` means all requirements for that record type are satisfied; it does
not imply successful vulnerability reproduction.

#### `$defs/failure_class`

Allowed values:

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

#### `$defs/failure_record`

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `failure_class` | failure class | Required | Primary classification. |
| `summary` | non-empty string | Required | Concise human-readable description. |
| `occurred_at` | UTC timestamp | Required | Time the failure became observable. |
| `stage` | stage name enum | Required | Pipeline stage in which it occurred. |
| `retryable` | boolean | Required | Whether retry can reasonably succeed without changing evidence or configuration. |
| `evidence` | array of evidence references | Optional | Evidence supporting the classification. |
| `details_artifact` | artifact reference | Optional | Large diagnostic content. |
| `uncertainty` | array of non-empty strings | Optional | Known uncertainty in the diagnosis. |

Allowed stage names are `collect`, `normalize`, `resolve`, `build`, `extract`,
`execute`, `verify`, and `report`.

#### `$defs/repair_record`

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `repair_id` | local ID | Required | Unique within its parent attempt or build. |
| `classification` | enum | Required | `environment_only`, `source_compatible`, or `semantics_changing`. |
| `description` | non-empty string | Required | What changed and why. |
| `patch_artifact` | artifact reference | Optional | Exact change, when representable as an artifact. |
| `applied_at` | UTC timestamp | Required | Application time. |
| `provenance` | provenance event | Required | Actor, inputs, and method. |
| `justification` | non-empty string | Required | Why the repair was necessary and acceptable. |

A `semantics_changing` repair must be surfaced to later comparability and
verification checks and cannot silently participate in a direct comparison.

The repair enum is also exposed independently as
`$defs/repair_classification`.

### 3.9 Availability and uncertainty

#### `$defs/availability_status`

Allowed values:

- `available`;
- `unavailable`;
- `not_collected`;
- `incompatible`;
- `not_applicable`.

#### `$defs/uncertainty_item`

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `uncertainty_id` | local ID | Required | Unique in the containing record. |
| `summary` | non-empty string | Required | What remains uncertain. |
| `impact` | enum | Required | `low`, `medium`, `high`, or `blocking`. |
| `related_fields` | array of JSON Pointers | Optional | Fields affected by the uncertainty. |
| `evidence` | array of evidence references | Optional | Supporting or conflicting evidence. |

### 3.10 Controlled extensions

#### `$defs/extensions`

Defines the explicit extension container described in the schema conventions.
Property names use a reverse-domain namespace such as
`org.example.adapter_metadata`; values may be any valid JSON. Consuming schemas
decide whether to expose this object. Core evidence requirements cannot be
satisfied only through extensions, and secrets remain prohibited.

## 4. `artifact-record.schema.json`

### 4.1 Purpose

An artifact record describes one immutable byte sequence or a known unavailable
artifact. It contains metadata, integrity information, provenance, and storage
location, but never embeds large artifact content.

Proposed canonical identity:

```text
urn:dacn:schema:artifact-record:1.0.0
```

### 4.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `artifact-record`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `artifact` record kind. |
| `created_at` | UTC timestamp | Required | Metadata record creation time. |
| `created_by` | actor identity | Required | Actor that registered the artifact. |
| `case_id` | stable entity ID | Optional | Owning case identity when case-scoped; must use the `case` kind. |
| `artifact_kind` | enum | Required | Functional type listed below. |
| `artifact_kind_detail` | non-empty string | Conditional | Required only when `artifact_kind` is `other`. |
| `media_type` | media type | Conditional | Required when bytes are available or quarantined; optional when unavailable. |
| `availability` | availability object | Required | Storage and availability state. |
| `content` | content identity object | Conditional | Required when available; prohibited when no bytes were obtained. |
| `origin` | enum | Required | `acquired`, `generated`, or `derived`. |
| `source_ids` | array of record IDs | Conditional | Source records from which an acquired artifact came. |
| `derivation` | derivation object | Conditional | Required when origin is `derived`; prohibited otherwise. |
| `provenance` | provenance event | Required | How the artifact was acquired, generated, or derived. |
| `handling` | handling object | Required | Execution and publication safety metadata. |
| `labels` | array of strings | Optional | Short non-normative indexing labels; unique values. |
| `description` | string | Optional | Concise explanation; not a substitute for raw content. |
| `supersedes_artifact_id` | record ID | Optional | Prior metadata record corrected by this record. |
| `extensions` | object | Optional | Controlled reverse-domain extensions. |

### 4.3 Artifact kinds

Allowed `artifact_kind` values for v1:

- `source_snapshot`;
- `source_archive`;
- `advisory_snapshot`;
- `patch`;
- `diff`;
- `dependency_lock`;
- `build_log`;
- `binary`;
- `library`;
- `docker_metadata`;
- `trigger`;
- `negative_control`;
- `harness`;
- `replay_script`;
- `stdout`;
- `stderr`;
- `sanitizer_report`;
- `stack_trace`;
- `debugger_transcript`;
- `coverage_data`;
- `coverage_summary`;
- `core_dump`;
- `generated_output`;
- `validation_report`;
- `case_report`;
- `manifest`;
- `other`.

### 4.4 `availability` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `status` | enum | Required | `available`, `unavailable`, or `quarantined`. |
| `reason` | non-empty string | Conditional | Required unless status is `available`. |
| `observed_at` | UTC timestamp | Required | Storage-availability observation made when this immutable record was created. |

`quarantined` means bytes exist but ordinary consumers must not open or execute
them until the handling policy permits it.

### 4.5 `content` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `path` | relative path | Required | Location beneath the package artifact root. |
| `size_bytes` | byte count | Required | Exact size of the raw bytes at registration. |
| `sha256` | SHA-256 digest | Required | Digest computed from the registered raw bytes. |
| `registered_at` | UTC timestamp | Required | Time the bytes and content identity were registered. |
| `registered_by` | actor identity | Required | Actor that calculated and registered the content identity. |

Later integrity checks produce separate validation-result records and never
mutate this content identity. Evidence consumers must require a successful
validation result from the relevant pipeline run.

### 4.6 `derivation` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `parent_artifacts` | array of artifact references | Required | At least one, unique by `artifact_id`. |
| `transformation` | non-empty string | Required | Named transformation or procedure. |
| `transformation_version` | non-empty string | Optional | Version of a standardized transformation. |
| `parameters` | object | Optional | Non-secret JSON parameters needed to understand or replay the transformation. |
| `lossy` | boolean | Required | Whether information was removed or changed irreversibly. |
| `redacted` | boolean | Required | Whether content was removed for disclosure, privacy, or safety. |
| `redaction_reason` | non-empty string | Conditional | Required when `redacted` is true. |

The original parent artifact must remain referenced and preserved when a
redacted or normalized derivative is created.

### 4.7 `handling` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `risk_class` | enum | Required | `benign`, `controlled_reproduction`, or `risk_increasing`. |
| `executable` | boolean | Required | Whether the artifact is directly executable or loadable as code. |
| `execution_scope` | enum | Required | `none` or `project_docker_only`. |
| `network_egress_allowed` | boolean | Required | Must normally be false for build and trigger execution artifacts. |
| `contains_secrets` | boolean | Required | Must always be false for valid persisted project artifacts. |
| `publication_status` | enum | Required | `internal`, `review_required`, or `approved`. |
| `handling_notes` | string | Optional | Additional non-secret restrictions. |

`risk_increasing` does not authorize publication or execution. It marks an
artifact for explicit review. The project must not automatically publish such
artifacts.

### 4.8 Conditional rules

1. `content` is required when `availability.status` is `available` or
   `quarantined`.
2. `content` is prohibited when `availability.status` is `unavailable`.
3. `source_ids` is required and non-empty when `origin` is `acquired`.
4. `derivation` is required only when `origin` is `derived`.
5. A `generated` artifact must identify its producing command or method in
   `provenance`.
6. `artifact_kind_detail` is required only for `artifact_kind: other`.
7. `contains_secrets: true` is structurally invalid.
8. Executable artifacts cannot use `execution_scope: none` unless the record
   explains that execution is prohibited; v1 should prefer
   `project_docker_only`.
9. `network_egress_allowed: true` requires a handling note and is not permitted
   for trigger execution without a separately reviewed policy.
10. `supersedes_artifact_id` must not equal the current `record_id`.

### 4.9 Semantic invariants

1. `content.path` resolves beneath the package artifact root.
2. Stored byte length equals `content.size_bytes`.
3. Stored byte digest equals `content.sha256`.
4. The path does not collide with another artifact having different bytes.
5. Parent artifacts exist and match the digests in their references.
6. Derivation provenance names all material inputs.
7. Raw parent artifacts remain accessible when a derived artifact is used.
8. A quarantined artifact is not opened or executed by ordinary validation.
9. An artifact referenced as executable evidence is available and has a
   successful integrity validation result for the relevant pipeline run.
10. Correction through `supersedes_artifact_id` does not alter or delete the
    superseded raw artifact.

### 4.10 Minimal conceptual example

```json
{
  "schema_name": "artifact-record",
  "schema_version": "1.0.0",
  "record_id": "urn:dacn:artifact:0195f2f0-7d20-7000-8000-000000000001",
  "created_at": "2026-09-16T09:30:00Z",
  "created_by": {
    "actor_type": "tool",
    "actor_id": "artifact-store",
    "tool": {"name": "artifact-store", "version": "0.1.0"}
  },
  "case_id": "urn:dacn:case:0195f2f0-7d20-7000-8000-000000000002",
  "artifact_kind": "stdout",
  "media_type": "text/plain; charset=utf-8",
  "availability": {
    "status": "available",
    "observed_at": "2026-09-16T09:30:00Z"
  },
  "content": {
    "path": "executions/vulnerable/stdout.log",
    "size_bytes": 128,
    "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    "registered_at": "2026-09-16T09:30:00Z",
    "registered_by": {
      "actor_type": "tool",
      "actor_id": "artifact-store",
      "tool": {"name": "artifact-store", "version": "0.1.0"}
    }
  },
  "origin": "generated",
  "provenance": {
    "activity_id": "urn:dacn:activity:0195f2f0-7d20-7000-8000-000000000003",
    "activity_type": "execution",
    "performed_by": {
      "actor_type": "tool",
      "actor_id": "execution-harness",
      "tool": {"name": "execution-harness", "version": "0.1.0"}
    },
    "started_at": "2026-09-16T09:29:59Z",
    "completed_at": "2026-09-16T09:30:00Z",
    "method": "bounded-process-execution"
  },
  "handling": {
    "risk_class": "controlled_reproduction",
    "executable": false,
    "execution_scope": "none",
    "network_egress_allowed": false,
    "contains_secrets": false,
    "publication_status": "internal"
  }
}
```

The digest in this conceptual example is syntactically valid but is not
presented as the digest of actual evidence.

## 5. `source-record.schema.json`

### 5.1 Purpose

A source record represents one retrieval snapshot of one public information
source. It preserves where information came from, when it was retrieved, what
bytes were obtained, and how retrieval occurred. It does not declare that the
source's claims are true.

A later retrieval that returns changed content creates a new source record and
artifact. It does not overwrite the earlier snapshot.

Proposed canonical identity:

```text
urn:dacn:schema:source-record:1.0.0
```

### 5.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `source-record`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `source` record kind. |
| `created_at` | UTC timestamp | Required | Source-record creation time. |
| `created_by` | actor identity | Required | Actor that created the record. |
| `source_kind` | enum | Required | Source category listed below. |
| `source_kind_detail` | non-empty string | Conditional | Required only for `source_kind: other`. |
| `title` | non-empty string | Optional | Human-readable source title when supplied by the source. |
| `publisher` | publisher object | Required | Entity responsible for the source. |
| `locator` | locator object | Required | Canonical external location requested. |
| `published_at` | source temporal value | Optional | Publication date/time asserted by the source without invented precision. |
| `modified_at` | source temporal value | Optional | Last modification date/time asserted by the source or transport. |
| `language` | string | Optional | BCP 47 language tag when known. |
| `retrieval` | retrieval object | Required | The acquisition attempt and result. |
| `manual_capture` | manual-capture object | Conditional | Required only for manual capture. |
| `content_artifact` | artifact reference | Conditional | Required when content bytes were successfully obtained. |
| `previous_snapshot_id` | record ID | Optional | Earlier source record for the same canonical locator. |
| `related_source_ids` | array of record IDs | Optional | Closely related source records; unique items. |
| `access` | access object | Required | Public availability and legal/access notes. |
| `provenance` | provenance event | Required | Acquisition provenance. |
| `uncertainties` | array of uncertainty items | Optional | Known uncertainty about identity, dates, or completeness. |
| `notes` | string | Optional | Concise context; must not embed the source content. |
| `supersedes_source_id` | record ID | Optional | Prior metadata record corrected by this record. |
| `extensions` | object | Optional | Controlled reverse-domain extensions. |

### 5.3 Source kinds

Allowed `source_kind` values for v1:

- `cve_record`;
- `cna_advisory`;
- `vendor_advisory`;
- `government_advisory`;
- `vulnerability_database`;
- `repository`;
- `commit`;
- `tag`;
- `issue`;
- `pull_request`;
- `release_notes`;
- `security_policy`;
- `mailing_list_post`;
- `research_publication`;
- `public_poc_reference`;
- `package_registry`;
- `build_documentation`;
- `dependency_metadata`;
- `other`.

`public_poc_reference` records public documentary evidence. It does not by
itself authorize downloading, executing, adapting, or publishing a PoC.

### 5.4 `publisher` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `name` | non-empty string | Required | Organization, project, or individual name as publicly presented. |
| `publisher_type` | enum | Required | `cna`, `vendor`, `maintainer`, `government`, `database`, `researcher`, `community`, or `unknown`. |
| `identifier` | non-empty string | Optional | Stable public identifier, such as a CNA short name or repository owner. |
| `homepage` | absolute URI | Optional | Public publisher homepage; normally HTTPS. |

`publisher_type` is descriptive provenance, not a trust score. Reliability is
assessed at the claim level from evidence and conflicts.

### 5.5 `locator` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `uri` | absolute URI | Required | Exact public location requested. |
| `canonical_uri` | absolute URI | Optional | Canonicalized location after redirects or repository normalization. |
| `repository_revision` | non-empty string | Optional | Revision named by the locator, if any; may initially be a tag or branch. |
| `repository_path` | relative path | Optional | Path within a repository. |
| `fragment` | string | Optional | Source-specific section or anchor when it carries evidentiary meaning. |

Allowed URI schemes must be explicitly configured. Ordinary advisory retrieval
should use HTTPS. Repository sources may use additional read-only schemes when
the acquisition policy permits them. Credentials, embedded access tokens, and
host-local paths are prohibited.

### 5.6 `retrieval` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `status` | enum | Required | Retrieval outcome listed below. |
| `requested_at` | UTC timestamp | Required | Time acquisition began. |
| `completed_at` | UTC timestamp | Required | Time acquisition ended. |
| `method` | enum | Required | `http_get`, `git_fetch`, `api`, `package_manager`, `manual_capture`, or `other`. |
| `method_detail` | non-empty string | Conditional | Required when method is `other`. |
| `tool` | tool identity | Required | Exact retrieval tool. |
| `http_status` | integer | Optional | HTTP response code when applicable, range 100 through 599. |
| `etag` | string | Optional | Transport ETag exactly as observed. |
| `last_modified` | string | Optional | Transport header exactly as observed. |
| `redirect_chain` | array of absolute URIs | Optional | Ordered redirect locations. |
| `response_media_type` | media type | Optional | Media type reported by the transport. |
| `error_summary` | non-empty string | Conditional | Required for unsuccessful terminal outcomes. |
| `error_artifact` | artifact reference | Optional | Detailed retrieval diagnostic output. |

Allowed retrieval statuses:

- `succeeded`;
- `not_modified`;
- `not_found`;
- `access_denied`;
- `rate_limited`;
- `failed`.

The completion time must not precede the request time. Redirect chains and
response headers are observations, not normalized source identities.

The `manual-capture` object contains a required reason, intervention level
(`human_ground_truth` or `manual_strategy`), pseudonymous reviewer actor,
capture timestamp, original locator, and `original_content_preserved` boolean.
The boolean must be true for a successful manual capture. Transcription or
correction, if needed, produces a derived artifact and preserves the original.

### 5.7 `access` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `publicly_accessible` | boolean | Required | Whether retrieval required no private authorization. |
| `authentication_used` | boolean | Required | Whether credentials were used. Must be false for benchmark evidence unless explicitly reviewed. |
| `license` | non-empty string | Optional | SPDX identifier or exact public license name when known. |
| `terms_uri` | absolute URI | Optional | Applicable public terms or license location. |
| `redistribution_status` | enum | Required | `allowed`, `restricted`, `unknown`, or `not_applicable`. |
| `access_notes` | string | Optional | Concise legal or access limitation. |

Credentials themselves must never be stored. Public accessibility does not
imply that the captured content may be redistributed.

### 5.8 Conditional rules

1. `content_artifact` is required for `retrieval.status: succeeded`.
2. `content_artifact` is prohibited for `not_found`, `access_denied`,
   `rate_limited`, and `failed`. Transport response bodies and diagnostics use
   `retrieval.error_artifact`.
3. `not_modified` requires `previous_snapshot_id`; the prior snapshot supplies
   the content identity.
4. `error_summary` is required for `not_found`, `access_denied`,
   `rate_limited`, and `failed`.
5. `http_status` is permitted only for HTTP- or API-based methods.
6. `method_detail` is required only for `method: other`.
7. `source_kind_detail` is required only for `source_kind: other`.
8. `repository_revision` and `repository_path` are permitted only for
   repository-related source kinds.
9. `previous_snapshot_id`, `related_source_ids`, and
   `supersedes_source_id` must reference `source-record` IDs and must not
   reference the current record itself.
10. `authentication_used: true` requires an access note explaining why the
    source remains legally usable for the project; no credential material may
    appear anywhere in the record or artifacts.
11. `manual_capture` is required exactly when retrieval method is
    `manual_capture` and is permitted only in benchmark-curation or development
    pipeline modes.

### 5.9 Semantic invariants

1. The content artifact exists and its digest matches its stored bytes.
2. The content artifact kind is appropriate for a source snapshot.
3. The retrieval provenance and top-level provenance describe the same
   acquisition event, or explicitly link related activities.
4. `canonical_uri` reflects only documented normalization or observed
   redirects; it must not silently change the source identity.
5. A later snapshot for the same locator preserves the earlier source record
   and artifact.
6. A `not_modified` record resolves to an earlier successful snapshot.
7. `published_at` and `modified_at` are preserved as source assertions and are
   not substituted for `retrieval.completed_at`.
8. The record contains no secrets, authorization headers, cookies, or private
   tokens.
9. Failed retrievals remain valid research records when they contain status,
   timing, method, and failure evidence.
10. Source kind and publisher type do not automatically determine claim
    confidence; downstream normalization must evaluate the specific evidence.

### 5.10 Minimal conceptual example

```json
{
  "schema_name": "source-record",
  "schema_version": "1.0.0",
  "record_id": "urn:dacn:source:0195f2f0-7d20-7000-8000-000000000010",
  "created_at": "2026-09-16T10:00:00Z",
  "created_by": {
    "actor_type": "tool",
    "actor_id": "source-collector",
    "tool": {"name": "source-collector", "version": "0.1.0"}
  },
  "source_kind": "vendor_advisory",
  "publisher": {
    "name": "Example Project",
    "publisher_type": "maintainer",
    "homepage": "https://example.invalid/"
  },
  "locator": {
    "uri": "https://example.invalid/security/advisory-1"
  },
  "retrieval": {
    "status": "succeeded",
    "requested_at": "2026-09-16T09:59:59Z",
    "completed_at": "2026-09-16T10:00:00Z",
    "method": "http_get",
    "tool": {"name": "source-collector", "version": "0.1.0"},
    "http_status": 200,
    "response_media_type": "text/html; charset=utf-8"
  },
  "content_artifact": {
    "artifact_id": "urn:dacn:artifact:0195f2f0-7d20-7000-8000-000000000011",
    "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
  },
  "access": {
    "publicly_accessible": true,
    "authentication_used": false,
    "redistribution_status": "unknown"
  },
  "provenance": {
    "activity_id": "urn:dacn:activity:0195f2f0-7d20-7000-8000-000000000012",
    "activity_type": "acquisition",
    "performed_by": {
      "actor_type": "tool",
      "actor_id": "source-collector",
      "tool": {"name": "source-collector", "version": "0.1.0"}
    },
    "started_at": "2026-09-16T09:59:59Z",
    "completed_at": "2026-09-16T10:00:00Z",
    "method": "http-get"
  }
}
```

The domain and digest in this example are placeholders. The example documents
shape only and does not claim that source content exists at that location.

## 6. Relationships Between the Foundation Schemas

```text
source-record
  content_artifact ----------> artifact-record
  retrieval.error_artifact --> artifact-record
  provenance inputs ---------> record/artifact references

artifact-record
  source_ids ----------------> source-record
  derivation.parents --------> artifact-record
  provenance inputs ---------> record/artifact references

common.schema.json
  supplies all shared definitions to both schemas
```

The apparent source/artifact cycle is intentional and resolvable:

- a source record references the artifact containing the retrieved bytes;
- an acquired artifact may reference the source record that explains where
  those bytes came from.

Implementations should create both IDs before persistence and commit the two
records atomically, or permit a short-lived draft state followed by immutable
completion records. Released packages must not contain dangling references.

## 7. Settled Foundation Decisions

The following choices are part of the v1 design.

### 7.1 Schema versions

Use the complete SemVer 2.0.0 syntax. Prerelease versions are permitted only
for development fixtures. Persisted cases, benchmark releases, and experiment
manifests must reference stable schema releases. Build metadata must not be
used to distinguish schema behavior.

### 7.2 Relative paths

JSON Schema rejects obvious unsafe forms, including absolute paths, drive
prefixes, backslashes, NUL bytes, empty segments, and `.` or `..` segments.
Semantic validation remains authoritative for resolving a path and proving
that it stays beneath the declared package root. Valid and invalid path
fixtures must accompany the schema implementation.

### 7.3 JSON document hashes

Schema v1 does not require representation-independent JSON canonicalization.
Artifacts are hashed as their exact stored bytes and structured records use
stable record IDs. When a serialized JSON document needs byte-level integrity,
it is registered as an artifact. RFC 8785 canonicalization may be added later
only if a concrete need for semantic document hashes emerges.

### 7.4 Artifact integrity history

An available artifact record contains the size and SHA-256 calculated during
registration. Successful registration asserts that these values were computed
from the stored bytes. Later integrity checks create separate validation-result
records; they do not mutate the artifact record.

Accordingly, the `content` object in Section 4.5 contains:

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `path` | relative path | Required | Location beneath the package artifact root. |
| `size_bytes` | byte count | Required | Exact size at registration. |
| `sha256` | SHA-256 digest | Required | Digest computed from the registered bytes. |
| `registered_at` | UTC timestamp | Required | Time the bytes and digest were registered. |
| `registered_by` | actor identity | Required | Actor that calculated and registered the content identity. |

Mutable `integrity_status`, `integrity_checked_at`, and
`integrity_checked_by` fields are not part of v1. An artifact used by a
verification result must have a successful, referenced validation result from
the relevant pipeline run.

### 7.5 Manual source capture

Manual capture is permitted for benchmark curation and development cases. It
must record a pseudonymous human actor, public locator, reason, capture time,
raw snapshot artifact, and intervention level. It is prohibited during
automated evaluation runs. Manually transcribed or corrected content cannot
silently replace the original source.

### 7.6 Atomic source and artifact publication

Collectors allocate source and artifact IDs first, stage the bytes and both
records, validate their hashes and references, and then publish the completed
set atomically. Database implementations should use a transaction; filesystem
implementations should use a staging directory followed by atomic rename.
Draft state may exist internally but is not part of the released v1 package
contract. Released packages cannot contain dangling references.

## 8. `vulnerability-record.schema.json`

### 8.1 Purpose

A vulnerability record is the normalized intake representation of one publicly
disclosed vulnerability. It consolidates identifiers, descriptions,
classifications, affected/fixed version claims, repository candidates, and
references while retaining claim-level provenance and conflicts.

It does not prove that a particular source revision is vulnerable or patched.
That determination belongs to `revision-resolution`.

Proposed canonical identity:

```text
urn:dacn:schema:vulnerability-record:1.0.0
```

### 8.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `vulnerability-record`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `vulnerability` record kind. |
| `created_at` | UTC timestamp | Required | Record creation time. |
| `created_by` | actor identity | Required | Actor that produced the normalized record. |
| `record_status` | record status | Required | Normally `draft`, `complete`, `invalid`, or `superseded`. |
| `identifiers` | array of identifier objects | Required | At least one; unique by `(scheme, value)`. |
| `title` | localized text | Required | Concise normalized title. |
| `descriptions` | array of localized text | Required | At least one normalized description. |
| `vulnerability_classes` | array of classification objects | Required | May be empty only when classification status is explicitly unresolved. |
| `products` | array of product objects | Required | At least one affected product or component candidate. |
| `version_statements` | array of version-statement objects | Required | Raw and normalized affected/fixed claims. |
| `repository_candidates` | array of repository-candidate objects | Optional | Candidate upstream repositories; unique by canonical locator. |
| `references` | array of categorized source references | Required | At least one public source. |
| `disclosure` | disclosure object | Required | Public disclosure evidence and dates. |
| `normalization_claims` | array of normalized claims | Required | Claim-level raw/normalized values and evidence. |
| `conflicts` | array of conflict objects | Optional | Material source disagreements. |
| `uncertainties` | array of uncertainty items | Optional | Missing or unresolved metadata. |
| `provenance` | provenance event | Required | Normalization procedure and inputs. |
| `supersedes_vulnerability_id` | record ID | Optional | Earlier normalized record corrected by this one. |
| `extensions` | object | Optional | Controlled reverse-domain extensions. |

### 8.3 `identifier` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `scheme` | enum | Required | `cve`, `ghsa`, `osv`, `vendor`, or `other`. |
| `value` | non-empty string | Required | Identifier exactly as normalized for the scheme. |
| `scheme_detail` | non-empty string | Conditional | Required for `scheme: other`. |
| `primary` | boolean | Required | Whether this is the package's primary public identifier. |
| `evidence` | array of evidence references | Required | At least one supporting source. |

Exactly one identifier must have `primary: true`. CVE values must use uppercase
`CVE-YYYY-NNNN...` form. Identifier aliases remain independent; the schema
must not infer equivalence merely from similar descriptions.

### 8.4 `localized_text` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `language` | string | Required | BCP 47 language tag. |
| `text` | non-empty string | Required | Normalized human-readable text. |
| `evidence` | array of evidence references | Required | Sources supporting the text. |

Descriptions must be unique by language and text. Multiple differing
descriptions in the same language are allowed when their sources or emphasis
differ.

### 8.5 `classification` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `system` | enum | Required | `cwe` or `other`. |
| `identifier` | non-empty string | Required | For example `CWE-787`. |
| `name` | non-empty string | Optional | Human-readable classification name. |
| `classification` | claim classification | Required | Fact, inference, hypothesis, or unknown. |
| `confidence` | confidence assessment | Required | Confidence and rationale. |
| `evidence` | array of evidence references | Required | At least one item unless classification is `unknown`. |

When no usable class is available, use a single entry with
`classification: unknown` and explain the absence through confidence rationale
or an uncertainty item. Do not invent a CWE from the observed crash alone.

### 8.6 `product` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `product_id` | local ID | Required | Stable within the vulnerability record. |
| `vendor` | non-empty string | Optional | Vendor or maintaining organization. |
| `name` | non-empty string | Required | Product or project name. |
| `component` | non-empty string | Optional | Affected subcomponent. |
| `ecosystem` | non-empty string | Optional | Package ecosystem, such as `npm`, `PyPI`, or `Maven`. |
| `package_name` | non-empty string | Optional | Ecosystem package coordinate. |
| `platforms` | array of non-empty strings | Optional | Reported affected platforms. |
| `evidence` | array of evidence references | Required | At least one source. |

Product identity is a normalized claim, not a repository resolution. Multiple
products may refer to one repository or one product may span repositories.

### 8.7 `version_statement` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `statement_id` | local ID | Required | Unique within the record. |
| `product_id` | local ID | Required | References a product in the same record. |
| `status` | enum | Required | `affected`, `fixed`, `unaffected`, or `unknown`. |
| `version_scheme` | enum | Required | `semver`, `pep440`, `maven`, `rpm`, `debian`, `git`, `ecosystem_specific`, or `unknown`. |
| `raw_expression` | non-empty string | Required | Version statement exactly as provided by a source. |
| `normalized_expression` | non-empty string | Optional | Normalized range or version expression. |
| `introduced` | non-empty string | Optional | Lower boundary when separately representable. |
| `fixed` | non-empty string | Optional | First fixed version when separately representable. |
| `last_affected` | non-empty string | Optional | Last affected version when asserted. |
| `limit` | non-empty string | Optional | Exclusive upper boundary when it is not a fixed release. |
| `evidence` | array of evidence references | Required | At least one source. |
| `confidence` | confidence assessment | Required | Confidence in normalization. |

Boundary fields are optional because version ecosystems differ. A normalized
expression must not be created when its semantics cannot be represented
without loss; preserve the raw expression and mark uncertainty instead.

### 8.8 `repository_candidate` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `candidate_id` | local ID | Required | Unique in this record. |
| `vcs` | enum | Required | `git`, `mercurial`, `subversion`, or `other`. |
| `locator` | absolute URI | Required | Public repository locator without credentials. |
| `canonical_locator` | absolute URI | Optional | Evidence-backed canonical form. |
| `subdirectory` | relative path | Optional | Component location within a monorepo. |
| `relationship` | enum | Required | `upstream`, `mirror`, `fork`, `vendor_snapshot`, or `unknown`. |
| `evidence` | array of evidence references | Required | At least one item. |
| `confidence` | confidence assessment | Required | Confidence that this repository contains the affected code. |

Only `revision-resolution` may select the authoritative comparison repository.

### 8.9 `categorized_source_reference` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `source_id` | record ID | Required | References a `source-record`. |
| `roles` | array of enums | Required | At least one source role; unique values. |
| `note` | string | Optional | Concise relevance note. |

Allowed roles:

- `identity`;
- `description`;
- `classification`;
- `affected_versions`;
- `fixed_versions`;
- `repository`;
- `patch`;
- `build_metadata`;
- `disclosure`;
- `reference_only`.

### 8.10 `disclosure` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `status` | enum | Required | `public`, `disputed`, or `insufficient_evidence`. |
| `public_at` | source temporal value | Conditional | Required for `public` without inventing missing time precision. |
| `evidence` | array of evidence references | Required | At least one public source. |
| `usable_fix_reference_present` | boolean | Required | Whether intake found a patch, fixing commit, or fixed version candidate. |

Only records with `status: public` and a usable fix reference may proceed as
benchmark candidates under the project safety policy.

### 8.11 `conflict` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `conflict_id` | local ID | Required | Unique within the record. |
| `field_path` | JSON Pointer | Required | Normalized field affected. |
| `claim_ids` | array of local IDs | Required | At least two conflicting normalization claims. |
| `status` | enum | Required | `unresolved`, `resolved`, or `accepted_with_uncertainty`. |
| `resolution` | non-empty string | Conditional | Required unless unresolved. |
| `resolved_by_evidence` | array of evidence references | Conditional | Required for `resolved`. |

Conflicts must remain recorded after resolution so the selected value remains
auditable.

### 8.12 Conditional rules

1. Exactly one identifier is primary.
2. `record_status: complete` requires at least one public identifier, product,
   affected or fixed version claim, public disclosure evidence, and usable fix
   reference.
3. `supersedes_vulnerability_id` must reference another vulnerability record
   and cannot reference the current record.
4. Every `product_id`, `statement_id`, `candidate_id`, `claim_id`, and
   `conflict_id` is unique in its scope.
5. Every version statement references an existing product.
6. Every conflict references existing normalization claims.
7. Repository locators cannot contain credentials.
8. `fixed` version statements do not prove the corresponding source revision;
   revision resolution remains required.

### 8.13 Semantic invariants

1. All source and artifact references resolve and match expected record types.
2. Every material normalized field has claim-level provenance.
3. Raw values remain traceable to immutable source snapshots.
4. Conflicting version claims are not silently collapsed.
5. The record represents a publicly disclosed vulnerability, not an inferred
   zero-day candidate.
6. A complete record identifies a plausible public fix source without claiming
   that the fix has already been verified.
7. Supersession preserves the prior record and explains the correction.

## 9. `revision-resolution.schema.json`

### 9.1 Purpose

A revision-resolution record selects and justifies immutable vulnerable and
patched source revisions in one authoritative repository. It records how
moving tags, version claims, advisory references, and fixing commits were
resolved and retains ambiguity when resolution is incomplete.

Proposed canonical identity:

```text
urn:dacn:schema:revision-resolution:1.0.0
```

### 9.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `revision-resolution`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `revision-resolution` kind. |
| `created_at` | UTC timestamp | Required | Record creation time. |
| `created_by` | actor identity | Required | Resolving actor. |
| `vulnerability_id` | record ID | Required | Referenced vulnerability record. |
| `status` | enum | Required | `resolved`, `ambiguous`, or `failed`. |
| `repository` | resolved-repository object | Conditional | Required when a repository candidate was identified; mandatory for `resolved`. |
| `vulnerable_revision` | resolved-revision object | Conditional | Required for `resolved`; optional for partial ambiguous results. |
| `patched_revision` | resolved-revision object | Conditional | Required for `resolved`; optional for partial ambiguous results. |
| `fix_commits` | array of resolved-revision objects | Conditional | Required and non-empty when a fixing commit is known. |
| `relationship` | revision-relationship object | Conditional | Required when both comparison revisions are known. |
| `comparability` | source-comparability object | Conditional | Required when both comparison revisions are known. |
| `alternatives` | array of revision-alternative objects | Optional | Rejected or unresolved candidates. |
| `selection_rationale` | non-empty string | Conditional | Required when status is `resolved`. |
| `evidence` | array of evidence references | Required | Sources and repository evidence used. |
| `failure` | failure record | Conditional | Required when status is `failed`. |
| `uncertainties` | array of uncertainty items | Optional | Remaining ambiguity. |
| `provenance` | provenance event | Required | Resolver, commands, and inputs. |
| `supersedes_resolution_id` | record ID | Optional | Earlier resolution corrected by this one. |
| `extensions` | object | Optional | Controlled reverse-domain extensions. |

### 9.3 `resolved_repository` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `vcs` | enum | Required | `git`, `mercurial`, or `subversion`; initial implementation should prioritize Git. |
| `locator` | absolute URI | Required | Public upstream or justified comparison repository. |
| `canonical_locator` | absolute URI | Required | Normalized repository identity. |
| `relationship` | enum | Required | `upstream`, `mirror`, `fork`, or `vendor_snapshot`. |
| `subdirectory` | relative path | Optional | Affected component in a monorepo. |
| `repository_source_id` | record ID | Required | Source record supporting repository identity. |
| `identity_evidence` | array of evidence references | Required | At least one item. |

Credentials, writable endpoints, and local host paths are prohibited.

### 9.4 `resolved_revision` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `role` | enum | Required | `vulnerable`, `patched`, or `fix_commit`. |
| `requested_reference` | non-empty string | Required | Tag, version, branch, or commit supplied by evidence. |
| `immutable_revision` | non-empty string | Required | Full immutable VCS object identifier. |
| `object_format` | enum | Required | `sha1`, `sha256`, or `vcs_specific`. |
| `tree_digest` | SHA-256 digest | Required | Digest of the normalized checked-out source tree used by the project. |
| `commit_timestamp` | UTC timestamp | Optional | Timestamp asserted by the VCS object. |
| `resolved_at` | UTC timestamp | Required | Resolution time. |
| `resolution_method` | enum | Required | `direct_commit`, `tag_peel`, `version_tag`, `parent_of_fix`, `release_mapping`, or `other`. |
| `resolution_method_detail` | non-empty string | Conditional | Required for `other`. |
| `evidence` | array of evidence references | Required | At least one source or repository artifact. |
| `verification_command` | array of strings | Required | Argument vector used to verify the immutable revision. |

For Git SHA-1 repositories, `immutable_revision` must be 40 lowercase
hexadecimal characters; Git SHA-256 uses 64. Abbreviated hashes are not
allowed. Branch names alone are never immutable revisions.

### 9.5 `revision_relationship` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `relationship` | enum | Required | `direct_successor`, `descendant`, `divergent`, or `unknown`. |
| `merge_base_revision` | non-empty string | Optional | Immutable merge-base identifier when applicable. |
| `commits_between` | integer | Optional | Non-negative first-parent or documented traversal count. |
| `comparison_method` | non-empty string | Required | Exact ancestry method. |
| `evidence_artifact` | artifact reference | Required | Raw ancestry or graph output. |

`descendant` is preferred but not mandatory: backports may be divergent. A
divergent pair requires explicit justification in the selection rationale.

### 9.6 `source_comparability` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `distinct_revisions` | boolean | Required | Immutable revision identifiers differ. |
| `distinct_trees` | boolean | Required | Normalized tree digests differ. |
| `same_repository_identity` | boolean | Required | Both revisions belong to the selected repository identity. |
| `target_patch_present_only_in_patched` | boolean | Required | Patch membership check outcome. |
| `comparison_artifacts` | array of artifact references | Required | At least one diff or repository-check artifact. |
| `asymmetries` | array of asymmetry objects | Optional | Known unavoidable source-level comparison differences. |

Each asymmetry records a `field`, vulnerable value, patched value,
justification, impact (`none`, `low`, `medium`, or `high`), and evidence.

### 9.7 `revision_alternative` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `candidate_reference` | non-empty string | Required | Candidate tag, version, branch, or revision. |
| `candidate_role` | enum | Required | `vulnerable`, `patched`, or `fix_commit`. |
| `disposition` | enum | Required | `rejected`, `ambiguous`, or `unavailable`. |
| `reason` | non-empty string | Required | Evidence-based reason. |
| `evidence` | array of evidence references | Optional | Supporting evidence. |

### 9.8 Conditional rules

1. `status: resolved` requires vulnerable and patched revisions,
   relationship, comparability, and selection rationale.
2. `status: failed` requires a `revision_failure` failure record and prohibits
   claims of a complete comparison pair.
3. `status: resolved` requires a repository; a failed result may omit it when
   repository identity itself could not be established.
4. Resolved vulnerable and patched roles must be correct and unique.
5. Fix commits must use `role: fix_commit`.
6. `resolution_method_detail` is required only for method `other`.
7. A divergent pair requires at least one documented asymmetry or explicit
   rationale addressing the divergence.
8. `supersedes_resolution_id` cannot reference the current record.

### 9.9 Semantic invariants

1. The repository can be retrieved legally from the recorded locator.
2. Immutable revisions exist in the selected repository and resolve to the
   recorded tree digests.
3. Vulnerable and patched immutable revisions differ.
4. Vulnerable and patched normalized tree digests differ.
5. The target fix is absent from the vulnerable revision and present in the
   patched revision, subject to documented backport structure.
6. Tags are resolved and recorded as immutable objects; later tag movement
   cannot alter the selected revisions.
7. Revision evidence traces back to public sources and raw repository output.
8. Ambiguity remains represented as ambiguity rather than being coerced into a
   resolved pair.

## 10. `patch-context.schema.json`

### 10.1 Purpose

A patch-context record captures static, evidence-based context for the target
fix: patch commits, changed files and symbols, root-cause hypotheses, and
initial reachability information. It separates directly observed diff facts
from interpretations.

Proposed canonical identity:

```text
urn:dacn:schema:patch-context:1.0.0
```

### 10.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `patch-context`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `patch-context` kind. |
| `created_at` | UTC timestamp | Required | Record creation time. |
| `created_by` | actor identity | Required | Extracting actor. |
| `vulnerability_id` | record ID | Required | Referenced vulnerability record. |
| `revision_resolution_id` | record ID | Required | Resolved comparison pair. |
| `status` | enum | Required | `complete`, `partial`, `unavailable`, or `failed`. |
| `patch_set` | patch-set object | Conditional | Required for complete or partial extraction. |
| `changed_files` | array of changed-file objects | Conditional | Required and non-empty when a textual patch exists. |
| `changed_symbols` | array of changed-symbol objects | Optional | Functions, methods, types, or data symbols affected. |
| `root_cause` | array of root-cause statements | Optional | Evidence-backed explanation; may remain unknown. |
| `reachability` | array of reachability-context objects | Optional | Initial static entry-point and path information. |
| `expected_observables` | array of observable-hypothesis objects | Optional | Candidate signals for later oracle design. |
| `limitations` | array of non-empty strings | Optional | Extraction or interpretation limits. |
| `evidence` | array of evidence references | Required | Patch and repository evidence. |
| `failure` | failure record | Conditional | Required for failed extraction. |
| `uncertainties` | array of uncertainty items | Optional | Unresolved root-cause or reachability questions. |
| `provenance` | provenance event | Required | Extraction tools, commands, and inputs. |
| `supersedes_patch_context_id` | record ID | Optional | Earlier context corrected by this one. |
| `extensions` | object | Optional | Controlled reverse-domain extensions. |

### 10.3 `patch_set` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `fix_revisions` | array of non-empty strings | Required | Ordered immutable fixing commits; at least one. |
| `base_revision` | non-empty string | Required | Immutable comparison base. |
| `head_revision` | non-empty string | Required | Immutable patched comparison head. |
| `patch_artifact` | artifact reference | Required | Exact raw patch. |
| `diff_artifact` | artifact reference | Required | Normalized or tool-produced diff used for extraction. |
| `commit_messages_artifact` | artifact reference | Optional | Raw commit messages. |
| `patch_applies_cleanly` | boolean | Required | Result against the recorded base revision. |
| `application_evidence` | artifact reference | Required | Command output proving patch applicability or failure. |

The patch and normalized diff may reference the same bytes when no
transformation occurred, but their provenance and artifact kind must remain
appropriate.

### 10.4 `changed_file` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `file_change_id` | local ID | Required | Unique within the patch context. |
| `change_type` | enum | Required | `added`, `modified`, `deleted`, `renamed`, `copied`, or `binary`. |
| `old_path` | relative path | Conditional | Required unless the file was added. |
| `new_path` | relative path | Conditional | Required unless the file was deleted. |
| `old_sha256` | SHA-256 digest | Conditional | Required when an old file exists. |
| `new_sha256` | SHA-256 digest | Conditional | Required when a new file exists. |
| `language` | non-empty string | Optional | Detected or declared programming language. |
| `additions` | integer | Optional | Non-negative textual line count. |
| `deletions` | integer | Optional | Non-negative textual line count. |
| `diff_artifact` | artifact reference | Required | File-level or containing diff evidence. |

Binary files do not require textual line counts. Renames require both old and
new paths.

### 10.5 `changed_symbol` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `symbol_change_id` | local ID | Required | Unique within the patch context. |
| `file_change_id` | local ID | Required | References a changed file. |
| `symbol_kind` | enum | Required | `function`, `method`, `type`, `macro`, `global`, `module`, or `unknown`. |
| `old_symbol` | symbol location | Optional | Symbol before the patch. |
| `new_symbol` | symbol location | Optional | Symbol after the patch. |
| `change_summary` | non-empty string | Required | Concise observed change. |
| `classification` | claim classification | Required | Fact or inference status. |
| `confidence` | confidence assessment | Required | Confidence and rationale. |
| `evidence` | array of evidence references | Required | Diff or source evidence. |

A symbol location contains a symbol name plus optional signature, start line,
end line, and enclosing symbol. At least one of `old_symbol` or `new_symbol` is
required.

### 10.6 `root_cause_statement` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `root_cause_id` | local ID | Required | Unique within the patch context. |
| `summary` | non-empty string | Required | Concise proposed or confirmed root cause. |
| `mechanism` | non-empty string | Required | Technical mechanism connecting precondition to unsafe behavior. |
| `preconditions` | array of non-empty strings | Required | At least one required input or state condition. |
| `affected_symbols` | array of local IDs | Required | At least one changed-symbol reference. |
| `cwe_ids` | array of strings | Optional | CWE identifiers consistent with the mechanism. |
| `classification` | claim classification | Required | Normally fact, strong inference, or hypothesis. |
| `confidence` | confidence assessment | Required | Confidence and rationale. |
| `evidence` | array of evidence references | Required | At least one item. |

A patch-looking change alone normally supports an inference, not a confirmed
root cause. Confirmation should require corroborating advisory, regression,
execution, or maintainer evidence.

### 10.7 `reachability_context` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `reachability_id` | local ID | Required | Unique within the patch context. |
| `entry_point` | symbol location | Required | Candidate externally or harness-reachable entry. |
| `target_symbol_change_id` | local ID | Required | Changed target symbol. |
| `path` | array of path-edge objects | Optional | Ordered static call or data-flow path. |
| `status` | enum | Required | `confirmed`, `inferred`, `not_found`, or `unknown`. |
| `analysis_method` | non-empty string | Required | Static tool or manual method. |
| `classification` | claim classification | Required | Epistemic classification. |
| `confidence` | confidence assessment | Required | Confidence and rationale. |
| `evidence` | array of evidence references | Required | Static evidence. |
| `limitations` | array of non-empty strings | Optional | Dynamic dispatch, configuration, generated code, or other limitations. |

Each path edge records `from_symbol`, `to_symbol`, `edge_type` (`call`,
`callback`, `data_flow`, `registration`, or `unknown`), classification,
confidence, and evidence.

Static reachability does not establish that a candidate input reached the code
at runtime. Execution and verification records must supply dynamic evidence
when the oracle requires it.

### 10.8 `observable_hypothesis` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `observable_id` | local ID | Required | Unique within the patch context. |
| `kind` | enum | Required | `sanitizer`, `stack_trace`, `coverage`, `assertion`, `state_change`, `output`, or `other`. |
| `description` | non-empty string | Required | Expected observable behavior. |
| `target_symbols` | array of local IDs | Required | Relevant changed symbols. |
| `classification` | claim classification | Required | Normally hypothesis or strong inference before execution. |
| `confidence` | confidence assessment | Required | Confidence and rationale. |
| `evidence` | array of evidence references | Required | Patch or advisory basis. |

This structure informs later `verification-policy` design but cannot itself
serve as executable proof.

### 10.9 Conditional rules

1. `status: complete` requires a patch set, changed files, and at least one
   changed symbol or an explicit limitation explaining why symbol extraction
   is unavailable.
2. `status: partial` requires a patch set plus limitations or uncertainties.
3. `status: unavailable` requires evidence explaining why no usable patch could
   be extracted.
4. `status: failed` requires an appropriate failure record.
5. Changed-file paths and hashes follow change-type requirements.
6. Changed symbols reference existing changed files.
7. Root-cause and observable entries reference existing changed symbols.
8. Reachability targets reference existing changed symbols.
9. `supersedes_patch_context_id` cannot reference the current record.

### 10.10 Semantic invariants

1. Patch revisions agree with the referenced revision-resolution record.
2. Patch and diff artifact hashes match their stored bytes.
3. Changed-file hashes match files at the recorded base and head revisions.
4. Patch applicability is supported by preserved command output.
5. Direct diff facts are distinguishable from inferred root cause and
   reachability.
6. Static reachability is never reported as runtime reachability.
7. Expected observables remain hypotheses until execution evidence supports
   them.
8. A partial or failed extraction is preserved and cannot be silently promoted
   to complete.

## 11. Relationships in the Vulnerability-Understanding Tranche

```text
source-records
      |
      v
vulnerability-record
      |
      v
revision-resolution -----> repository and revision evidence artifacts
      |
      v
patch-context -----------> patch, diff, source, and extraction artifacts
```

The boundaries are deliberate:

- `vulnerability-record` represents public metadata claims.
- `revision-resolution` selects immutable comparison source states.
- `patch-context` describes what changed and what the change may mean.
- None of these schemas claims successful reproduction.
- Runtime evidence and final verdicts belong to later execution and
  verification schemas.

## 12. `validation-result.schema.json`

### 12.1 Purpose

A validation-result record captures one immutable structural or semantic
validation event. It allows integrity checks to be repeated without mutating
the evidence record being checked.

Proposed canonical identity:

```text
urn:dacn:schema:validation-result:1.0.0
```

### 12.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `validation-result`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `validation` kind. |
| `created_at` | UTC timestamp | Required | Result creation time. |
| `created_by` | actor identity | Required | Validating actor. |
| `validation_type` | enum | Required | `schema`, `artifact_integrity`, `reference_integrity`, `semantic`, or `package`. |
| `subject` | validation-subject object | Required | Exact record or artifact checked. |
| `validator` | tool identity | Required | Validator implementation and version. |
| `started_at` | UTC timestamp | Required | Validation start. |
| `completed_at` | UTC timestamp | Required | Validation completion. |
| `status` | enum | Required | `passed`, `failed`, or `error`. |
| `schema_checked` | schema descriptor | Conditional | Required for schema validation. |
| `artifact_observation` | artifact observation | Conditional | Required for artifact-integrity validation. |
| `checks` | array of validation-check objects | Required | At least one check. |
| `findings` | array of validation-finding objects | Optional | Failures, errors, and warnings. |
| `summary` | non-empty string | Required | Concise outcome. |
| `provenance` | provenance event | Required | Inputs and validation method. |
| `extensions` | object | Optional | Controlled reverse-domain extensions. |

### 12.3 Nested objects

`validation-subject` contains exactly one of:

- `record`, a record reference;
- `artifact`, an artifact reference;
- `case_manifest_id`, a case-manifest record ID.

`schema descriptor` contains `schema_name`, `schema_version`, canonical
`schema_id`, and optional schema-artifact reference.

`artifact observation` contains:

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `path_checked` | relative path | Required | Resolved package-relative path. |
| `observed_size_bytes` | byte count | Required | Size observed during this check. |
| `observed_sha256` | SHA-256 digest | Required | Digest observed during this check. |
| `expected_size_bytes` | byte count | Required | Size from the artifact record. |
| `expected_sha256` | SHA-256 digest | Required | Digest from the artifact record. |

Each `validation-check` contains a local `check_id`, stable `check_code`,
description, status (`passed`, `failed`, `skipped`, or `error`), and optional
evidence references.

Each `validation-finding` contains a local `finding_id`, severity (`info`,
`warning`, `error`, or `fatal`), stable finding code, message, optional JSON
Pointer, optional related record or artifact, and evidence references.

### 12.4 Conditional and semantic rules

1. `passed` requires every required check to pass and no error or fatal
   finding.
2. `failed` requires at least one failed check or error/fatal finding.
3. `error` means the validator could not complete; it is not equivalent to a
   failed subject.
4. Artifact-integrity validation requires an artifact subject and observation.
5. Schema validation requires a record subject and schema descriptor.
6. Observed artifact size and digest must be calculated from stored bytes, not
   copied from the artifact record.
7. Validation records are append-only; repeated validation creates new records.
8. A validation result does not itself establish vulnerability reproduction.

## 13. `environment-spec.schema.json`

### 13.1 Purpose

An environment specification declares the intended, reproducible platform for
dependency acquisition, building, and execution. It is configuration, not an
observation of what was actually created.

Proposed canonical identity:

```text
urn:dacn:schema:environment-spec:1.0.0
```

### 13.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `environment-spec`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `environment` kind. |
| `created_at` | UTC timestamp | Required | Specification creation time. |
| `created_by` | actor identity | Required | Authoring actor. |
| `case_id` | stable entity ID | Required | Owning case identity; must use the `case` kind. |
| `name` | non-empty string | Required | Human-readable environment name. |
| `roles` | array of enums | Required | One or more of `vulnerable`, `patched`, `control`, or `shared`. |
| `platform` | platform object | Required | OS, architecture, and isolation requirements. |
| `toolchain` | array of tool requirements | Required | Compiler, linker, runtime, package manager, and build tools. |
| `dependencies` | dependency-policy object | Required | Dependency declarations and resolution rules. |
| `configuration` | build-configuration object | Required | Build mode, features, flags, and configuration commands. |
| `instrumentation` | array of instrumentation requirements | Optional | Required, optional, unavailable, or incompatible instrumentation. |
| `network_policies` | phase-network-policy object | Required | Separate acquisition, build, and execution policies. |
| `resource_limits` | resource-limits object | Required | Default bounded resource policy. |
| `filesystem` | filesystem-policy object | Required | Mounts, writable locations, and disk limits. |
| `services` | array of service requirements | Optional | Required local services; no public targets. |
| `environment_variables` | object of strings | Optional | Explicit non-secret variables. |
| `comparability_group` | non-empty string | Required | Groups vulnerable/patched specs expected to be comparable. |
| `declared_asymmetries` | array of environment-asymmetry objects | Optional | Unavoidable role-specific differences. |
| `provenance` | provenance event | Required | Sources and transformation used to author the spec. |
| `supersedes_environment_id` | record ID | Optional | Prior specification replaced by this one. |
| `extensions` | object | Optional | Controlled adapter extensions. |

### 13.3 `platform` object

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `operating_system` | non-empty string | Required | OS family. |
| `distribution` | non-empty string | Optional | Distribution name. |
| `release` | non-empty string | Required | Exact release or image release. |
| `architecture` | enum | Required | Initially `x86_64`, `aarch64`, `x86`, or `other`. |
| `architecture_detail` | non-empty string | Conditional | Required for `other`. |
| `libc` | non-empty string | Optional | C library and version requirement. |
| `kernel_requirement` | non-empty string | Optional | Kernel constraint where material. |
| `isolation` | enum | Required | Constant `docker`. |
| `base_image` | image identity | Required | Digest-pinned Docker image identity. |

An image identity contains registry, repository, optional human-readable tag,
and mandatory immutable digest. A tag alone is insufficient.

### 13.4 Tool, dependency, and configuration objects

Each `tool requirement` contains:

- `role`: `compiler`, `linker`, `runtime`, `sdk`, `package_manager`,
  `build_system`, `debugger`, or `other`;
- name;
- exact version or evidence-backed version constraint;
- acquisition source reference;
- required boolean;
- optional executable name and expected SHA-256.

The `dependency-policy` contains:

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `manager` | non-empty string | Optional | Package/dependency manager. |
| `manifest_artifacts` | array of artifact references | Optional | Project dependency manifests. |
| `lock_artifacts` | array of artifact references | Optional | Exact lock or resolution inputs. |
| `pinning` | enum | Required | `fully_pinned`, `partially_pinned`, `record_resolution`, or `unresolved`. |
| `resolution_command` | command array | Optional | Dependency-resolution command. |
| `offline_build_required` | boolean | Required | Must normally be true after acquisition. |
| `allowed_registries` | array of absolute URIs | Optional | Acquisition-only allowlist. |

The `build-configuration` contains build mode, source directory, build
directory, configure commands, build commands, optional install commands,
compiler flags, linker flags, enabled/disabled features, expected outputs, and
parallelism. Commands are argument arrays and directories are relative paths.

### 13.5 Instrumentation and limits

Each instrumentation requirement contains `kind` (`asan`, `ubsan`, `msan`,
`tsan`, `coverage`, `debug_symbols`, `core_dump`, `debugger`, or `other`),
availability (`required`, `optional`, `unavailable`, or `incompatible`), tool
requirement, flags, expected artifacts, and rationale.

The resource-limits object contains non-negative integer values for:

- `timeout_ms`;
- `memory_limit_bytes`;
- `process_limit`;
- `disk_limit_bytes`;
- `output_limit_bytes`;
- optional `cpu_time_ms` and `open_file_limit`.

The phase-network-policy contains distinct `dependency_acquisition`, `build`,
and `execution` objects. Each specifies `enabled`, optional allowlisted
destinations, and justification. Build and execution default to disabled;
execution network access requires explicit review.

### 13.6 Conditional and semantic rules

1. Docker is the only permitted build and execution environment, and every
   environment requires a digest-pinned base image. Host execution, other
   container engines, sandboxes, and virtual machines are not valid fallbacks.
2. Required toolchain components must specify an exact version or a documented
   resolution strategy.
3. Secrets and host credentials are prohibited from environment variables.
4. Dependency network access is separate from build and execution access.
5. `offline_build_required: true` requires build network access to be disabled.
6. Members of one comparability group use the same platform, toolchain,
   dependency policy, instrumentation, and limits except for declared
   asymmetries.
7. Semantics-changing source repairs cannot be hidden in configuration.
8. Services must be project-local and cannot identify public/live targets.

## 14. `build-record.schema.json`

### 14.1 Purpose

A build record captures what actually happened while materializing one source
revision under an environment specification. It records resolved tools and
dependencies, commands, repairs, outputs, cache identity, and failures.

Proposed canonical identity:

```text
urn:dacn:schema:build-record:1.0.0
```

### 14.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `build-record`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `build` kind. |
| `created_at` | UTC timestamp | Required | Record creation time. |
| `created_by` | actor identity | Required | Build harness actor. |
| `case_id` | stable entity ID | Required | Owning case identity; must use the `case` kind. |
| `attempt_id` | record ID | Required | Build attempt that produced this record. |
| `role` | enum | Required | `vulnerable`, `patched`, or `control`. |
| `environment_spec_id` | record ID | Required | Requested environment. |
| `revision_resolution_id` | record ID | Required | Source-pair resolution. |
| `source_revision` | source-build identity | Required | Exact revision and source tree used. |
| `status` | enum | Required | `succeeded`, `failed`, `interrupted`, or `invalid`. |
| `started_at` | UTC timestamp | Required | Build start. |
| `completed_at` | UTC timestamp | Required | Build end. |
| `duration_ms` | duration | Required | Monotonic elapsed duration. |
| `observed_platform` | platform observation | Required | Actual image, OS, and architecture. |
| `observed_tools` | array of tool identities | Required | Actual tool versions; unique by role and name. |
| `dependency_resolution` | dependency-resolution object | Required | Exact observed resolution. |
| `commands` | array of command-result objects | Required | Ordered configure/build/install commands. |
| `repairs` | array of repair records | Optional | Explicit build repairs. |
| `outputs` | array of build-output objects | Conditional | Required and non-empty on success. |
| `cache` | cache-identity object | Required | Cache isolation and reuse evidence. |
| `failure` | failure record | Conditional | Required unless succeeded. |
| `deviations` | array of environment-asymmetry objects | Optional | Differences from the specification. |
| `provenance` | provenance event | Required | Build procedure and inputs. |
| `extensions` | object | Optional | Controlled adapter extensions. |

### 14.3 Build-specific nested objects

`source-build identity` contains repository canonical locator,
`comparison_source_role` (`vulnerable` or `patched`), immutable revision,
normalized tree SHA-256, checkout artifact or manifest, and dirty state. Dirty
state must be false unless every modification is represented by a repair
artifact. A control build therefore remains traceable to the vulnerable or
patched source on which it is based.

`platform observation` contains isolation type, immutable image digest, OS
release, architecture, optional kernel/libc observations, and environment
identity digest.

`dependency-resolution` contains status (`resolved`, `partial`, or `failed`),
manager and version, ordered acquisition commands, resolved-lock artifact,
dependency inventory artifact, checksums-verified boolean, network policy
observed, and errors.

Each `command-result` contains a local command ID, phase (`configure`, `build`,
`install`, or `validation`), argument array, relative working directory,
explicit environment, start/end times, duration, exit code, terminating signal,
stdout/stderr artifact references, timeout/resource events, and status.

Each `build-output` contains name, kind (`executable`, `library`, `package`,
`symbols`, or `other`), artifact reference, relative install path if relevant,
and role in later execution.

`cache-identity` contains cache key, source tree digest, environment identity
digest, dependency digest, configuration digest, cache-hit boolean, cache
producer build ID when hit, and isolation-check result.

### 14.4 Conditional and semantic rules

1. Success requires all required commands to succeed and all expected outputs
   to be present and registered with content identity. Subsequent integrity
   validation is represented by separate validation-result records.
2. Failure, interruption, and invalid status require a failure record.
3. A semantics-changing repair forces status `invalid` for direct paired
   comparison unless separately reviewed and explicitly allowed.
4. Source revision and tree digest must match the selected role in revision
   resolution.
5. Observed platform and tools must satisfy the environment specification or
   appear as explicit deviations.
6. Vulnerable and patched records cannot silently share outputs, source trees,
   cache keys, or layers.
7. A cache hit is valid only when every cache-key input agrees and the producer
   build is compatible with the current role.
8. Dependency resolution failure is not reclassified as build failure.
9. Logs and binaries are artifact references, never embedded content.

## 15. `execution-spec.schema.json`

### 15.1 Purpose

An execution specification declares one bounded invocation of a built target.
It is independent of any specific project adapter and contains no observed
outcome.

Proposed canonical identity:

```text
urn:dacn:schema:execution-spec:1.0.0
```

### 15.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `execution-spec`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `execution-spec` kind. |
| `created_at` | UTC timestamp | Required | Specification creation time. |
| `created_by` | actor identity | Required | Authoring actor. |
| `case_id` | stable entity ID | Required | Owning case identity; must use the `case` kind. |
| `comparison_group` | non-empty string | Required | Groups paired and control executions. |
| `role` | enum | Required | `vulnerable`, `patched`, `negative_control`, or `environment_control`. |
| `build_id` | record ID | Required | Build to execute. |
| `executable_artifact` | artifact reference | Required | Exact binary, library, or harness entry point. |
| `input` | execution-input object | Required | Candidate or control input identity. |
| `control_relationship` | control relationship | Conditional | Required for control roles. |
| `command` | array of strings | Required | Exact argument vector; at least one item. |
| `working_directory` | relative path | Required | Directory within isolated runtime root. |
| `environment_variables` | object of strings | Required | Explicit effective variables; may be empty. |
| `stdin` | stdin specification | Required | `null_device`, `artifact`, or `inline_empty`; artifact mode references an artifact. |
| `harness` | harness specification | Required | Stable adapter and invocation contract. |
| `instrumentation` | array of instrumentation configurations | Optional | Runtime instrumentation. |
| `resource_limits` | resource-limits object | Required | Per-run bounds. |
| `network_policy` | network policy | Required | Normally disabled. |
| `filesystem_policy` | runtime-filesystem policy | Required | Read-only and writable paths plus disk bound. |
| `expected_outputs` | array of expected-output descriptors | Optional | Files or state to collect, not expected vulnerability signals. |
| `provenance` | provenance event | Required | How the specification was produced. |
| `extensions` | object | Optional | Controlled adapter extensions. |

### 15.3 Input, controls, and harness

The `execution-input` object contains an artifact reference, input role
(`candidate` or `benign_control`), delivery mechanism (`argument`, `stdin`,
`file`, `environment`, or `harness_specific`), and optional destination path.

The `control relationship` contains:

- control type (`matched_benign_input`, `alternate_build`,
  `instrumentation_control`, or `other`);
- target candidate artifact reference;
- dimensions intentionally changed;
- dimensions held constant;
- rationale.

The `harness specification` contains harness artifact, adapter name and version,
entry point, setup and cleanup command arrays, and interface version. Setup and
cleanup commands execute under the same isolation and network policy.

### 15.4 Conditional and semantic rules

1. Vulnerable and patched specifications in a comparison group reference the
   same candidate artifact digest.
2. Control roles require a control relationship; candidate roles prohibit it.
3. A matched benign control must use a distinct input artifact and declare the
   candidate to which it is matched.
4. The build role must agree with the execution role, except a negative input
   control may intentionally use the vulnerable build.
5. Network access is disabled unless explicitly justified and reviewed.
6. Paths resolve within the isolated runtime root.
7. Secrets and host credentials are prohibited.
8. The executable and all input artifacts must have successful integrity
   validation results before execution.
9. Expected outputs describe collection targets only and cannot encode an
   after-the-fact verdict.

## 16. `execution-record.schema.json`

### 16.1 Purpose

An execution record captures one observed run, including raw output and
telemetry artifacts. It records facts; it does not assign the final
vulnerability verdict.

Proposed canonical identity:

```text
urn:dacn:schema:execution-record:1.0.0
```

### 16.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `execution-record`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `execution` kind. |
| `created_at` | UTC timestamp | Required | Record creation time. |
| `created_by` | actor identity | Required | Execution harness actor. |
| `case_id` | stable entity ID | Required | Owning case identity; must use the `case` kind. |
| `attempt_id` | record ID | Required | Execution attempt. |
| `execution_spec_id` | record ID | Required | Requested run. |
| `status` | enum | Required | `completed`, `timed_out`, `resource_limited`, `startup_failed`, `harness_failed`, or `interrupted`. |
| `started_at` | UTC timestamp | Required | Run start. |
| `completed_at` | UTC timestamp | Required | Run end. |
| `duration_ms` | duration | Required | Monotonic elapsed duration. |
| `actual_invocation` | invocation observation | Required | Actual command, directory, environment, and artifact identities. |
| `process_result` | process-result object | Optional | Exit and signal information when a process started. |
| `resource_events` | array of resource-event objects | Optional | Timeout, OOM, disk, process, CPU, or output-limit events. |
| `stdout_artifact` | artifact reference | Required | Raw bounded stdout, including an empty artifact. |
| `stderr_artifact` | artifact reference | Required | Raw bounded stderr, including an empty artifact. |
| `output_truncated` | boolean | Required | Whether any raw process output exceeded collection bounds. |
| `telemetry` | array of telemetry-observation objects | Optional | Sanitizer, debugger, stack, coverage, assertion, or trace evidence. |
| `generated_outputs` | array of generated-output objects | Optional | Files or state changes produced by the run. |
| `observed_resources` | resource-usage object | Optional | Peak memory, CPU, process, disk, and output usage. |
| `failure` | failure record | Conditional | Required for non-completed harness/environment outcomes. |
| `provenance` | provenance event | Required | Runner, inputs, and method. |
| `extensions` | object | Optional | Controlled instrumentation extensions. |

### 16.3 Runtime observations

`actual invocation` contains command array, relative working directory,
explicit environment, executable artifact reference, input artifact reference,
build ID, isolation identity, harness identity, and effective network policy.

`process result` contains an optional non-negative exit code, optional terminating signal,
whether a core was produced, and process-started boolean. At least one of exit
code or signal is required when a started process terminates.

Each `resource event` contains kind (`timeout`, `memory`, `cpu`, `process`,
`disk`, `output`, or `other`), limit, observed value when available, timestamp,
and evidence artifact.

Each `telemetry observation` contains kind (`sanitizer`, `stack_trace`,
`debugger`, `coverage`, `assertion`, `trace`, or `other`), availability status,
tool identity, summary, artifact references, and relevant code locations.

Each `generated output` contains relative path, artifact reference, output kind,
collection status, and optional before/after state artifact references.

### 16.4 Conditional and semantic rules

1. Actual invocation must satisfy the execution specification or record every
   deviation explicitly.
2. Timeout or resource limitation is an execution condition, never an
   automatic vulnerability signal.
3. Startup and harness failures use their matching failure classes rather than
   hypothesis or reachability failures.
4. Raw stdout and stderr are preserved even when empty, truncated, or malformed.
5. Truncation records the configured limit and does not alter the collected raw
   prefix.
6. Every telemetry summary links to raw evidence when such evidence exists.
7. Generated files are immutable artifacts; raw outputs are not edited after
   collection.
8. Candidate, executable, build, and isolation identities must be sufficient to
   detect accidental reuse across comparison roles.

## 17. `verification-policy.schema.json`

### 17.1 Purpose

A verification policy defines the oracle contract before results are judged.
It declares required runs, target signals, safe behavior, reachability evidence,
comparability checks, controls, and deterministic verdict rules.

Proposed canonical identity:

```text
urn:dacn:schema:verification-policy:1.0.0
```

### 17.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `verification-policy`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `verification-policy` kind. |
| `created_at` | UTC timestamp | Required | Policy creation time. |
| `created_by` | actor identity | Required | Policy author. |
| `case_id` | stable entity ID | Required | Owning case identity; must use the `case` kind. |
| `vulnerability_id` | record ID | Required | Target vulnerability. |
| `patch_context_id` | record ID | Required | Static evidence informing the policy. |
| `policy_version` | semantic version | Required | Version of case-specific oracle behavior. |
| `required_runs` | array of run-requirement objects | Required | Vulnerable, patched, and control roles. |
| `environment_requirements` | array of policy-check objects | Required | Environment validity conditions. |
| `comparability_requirements` | array of policy-check objects | Required | Paired-build/run equality conditions. |
| `signals` | array of signal-definition objects | Required | Target, safe, reachability, and exclusion signals. |
| `control_requirements` | array of control-requirement objects | Required | Required negative controls. |
| `decision_rules` | array of decision-rule objects | Required | Ordered, deterministic verdict mapping. |
| `limitations` | array of non-empty strings | Optional | Known oracle limitations. |
| `evidence` | array of evidence references | Required | Basis for expected behavior. |
| `provenance` | provenance event | Required | How the policy was authored. |
| `supersedes_policy_id` | record ID | Optional | Prior policy replaced by this one. |
| `extensions` | object | Optional | Controlled matcher extensions. |

### 17.3 Run, signal, and control definitions

A `run requirement` contains role, minimum count, maximum count, execution-spec
IDs or selection criteria, required status, and whether missing data invalidates
the environment or makes the verdict inconclusive.

A `policy check` contains stable check ID, description, severity, declarative
operator, operands expressed as JSON Pointers or constants, and failure outcome.
Arbitrary executable expressions are prohibited.

A `signal definition` contains:

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `signal_id` | local ID | Required | Unique policy signal. |
| `purpose` | enum | Required | `target`, `safe_behavior`, `reachability`, or `exclusion`. |
| `description` | non-empty string | Required | Meaning of the signal. |
| `source` | enum | Required | `stdout`, `stderr`, `exit_code`, `signal`, `sanitizer`, `stack_trace`, `coverage`, `assertion`, `state_change`, or `generated_output`. |
| `matcher` | matcher object | Required | Declarative match operation. |
| `required_in_roles` | array of run roles | Optional | Roles where it must appear. |
| `forbidden_in_roles` | array of run roles | Optional | Roles where it must not appear. |
| `evidence` | array of evidence references | Required | Why this signal is relevant. |

Matcher kinds are `literal`, `regular_expression`, `numeric_comparison`,
`exit_code_set`, `signal_set`, `stack_frame`, `source_location`,
`coverage_location`, and `artifact_predicate`. Regex dialect and flags must be
declared. Matchers operate only on bounded recorded evidence and cannot invoke
shell commands or external code.

A `control requirement` contains control ID, control type, required run role,
relationship to the candidate, expected absent/present signals, dimensions held
constant, and failure outcome.

### 17.4 Decision rules

Each decision rule contains:

- unique rule ID;
- priority integer;
- description;
- all/any declarative condition references;
- emitted verdict;
- optional failure class;
- rationale template.

Rules must cover at least:

1. invalid build or execution environment;
2. missing required evidence;
3. target signal in patched or control runs;
4. vulnerable target signal absent;
5. target signal without code/state evidence;
6. all verification conditions satisfied.

### 17.5 Conditional and semantic rules

1. Required runs include at least one vulnerable and one patched candidate role
   plus at least one negative control requirement. A policy may require repeated
   runs and must declare their counts.
2. Target and reachability signals are required for `VERIFIED`.
3. Patched and control roles forbid the CVE-specific target signal unless the
   policy explicitly models a non-binary safe form.
4. Environment-invalidating rules take precedence over reproduction rules.
5. Control failures cannot emit `VERIFIED`.
6. Policy creation time must precede or equal the verification execution start,
   unless a later policy is explicitly used only for reanalysis and reported as
   such.
7. Every matcher is declarative, bounded, and reproducible.

## 18. `verification-result.schema.json`

### 18.1 Purpose

A verification result applies one immutable verification policy to exact build,
execution, control, and evidence records. It is the authoritative structured
oracle output for a case attempt.

Proposed canonical identity:

```text
urn:dacn:schema:verification-result:1.0.0
```

### 18.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `verification-result`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `verification` kind. |
| `created_at` | UTC timestamp | Required | Result creation time. |
| `created_by` | actor identity | Required | Oracle actor. |
| `case_id` | stable entity ID | Required | Owning case identity; must use the `case` kind. |
| `attempt_id` | record ID | Required | Verification attempt. |
| `policy_id` | record ID | Required | Exact verification policy. |
| `oracle` | tool identity | Required | Oracle implementation and version. |
| `started_at` | UTC timestamp | Required | Evaluation start. |
| `completed_at` | UTC timestamp | Required | Evaluation end. |
| `inputs` | verification-inputs object | Required | Exact build and execution records evaluated. |
| `environment_checks` | array of check-result objects | Required | Environment validity outcomes. |
| `comparability_checks` | array of check-result objects | Required | Pair equivalence and distinctness outcomes. |
| `observations` | array of run-observation objects | Required | Per-run matched signals and evidence. |
| `control_results` | array of control-result objects | Required | At least one required control result. |
| `rule_results` | array of rule-result objects | Required | Every applicable policy rule. |
| `verdict` | enum | Required | `VERIFIED`, `NOT_REPRODUCED`, `INCONCLUSIVE`, or `INVALID_ENVIRONMENT`. |
| `failure_class` | failure class | Conditional | Required for every verdict except `VERIFIED`. |
| `rationale` | non-empty string | Required | Evidence-based final rationale. |
| `confirmed_facts` | array of evidence-backed statements | Required | May be empty but must be explicit. |
| `strong_inferences` | array of evidence-backed statements | Required | May be empty. |
| `hypotheses` | array of evidence-backed statements | Required | May be empty. |
| `unknowns` | array of evidence-backed statements | Required | May be empty. |
| `uncertainties` | array of uncertainty items | Optional | Remaining uncertainty. |
| `validation_result_ids` | array of record IDs | Required | Validation of material inputs consumed by the oracle; excludes validation of this result itself. |
| `provenance` | provenance event | Required | Oracle inputs and method. |
| `extensions` | object | Optional | Controlled oracle extensions. |

### 18.3 Verification observations

`verification inputs` names vulnerable and patched build IDs, vulnerable and
patched execution IDs, control execution IDs, candidate artifact reference,
and relevant patch-context record.

Each `check result` contains policy check ID, status (`passed`, `failed`,
`skipped`, or `error`), observed values, expected values, and evidence.

Each `run observation` contains execution ID, role, execution validity,
matched-signal IDs, absent required-signal IDs, relevant code locations,
evidence references, and concise interpretation.

Each `control result` contains policy control ID, execution IDs, status
(`passed`, `failed`, or `invalid`), signal observations, and evidence.

Each `rule result` contains policy rule ID, applicability, condition results,
status, emitted candidate verdict where applicable, and evidence.

An `evidence-backed statement` contains statement text, classification fixed by
the containing array, and one or more evidence references.

### 18.4 Verdict invariants

`VERIFIED` requires all of the following:

1. vulnerable and patched environments are valid;
2. revisions, source trees, build outputs, and roles are distinct and correct;
3. paired executions used the same candidate artifact;
4. the vulnerable execution contains the expected target signal;
5. required code-region or state-reachability evidence is present;
6. the patched execution exhibits the defined safe behavior or lacks the
   target signal as specified;
7. every required negative control passes;
8. the observed difference is consistent with patch and root-cause evidence;
9. all material artifacts and references have successful validation results;
10. no higher-priority invalidating policy rule fired.

Additional rules:

- Environment or harness invalidity produces `INVALID_ENVIRONMENT`.
- A valid environment with no sufficient vulnerable signal produces
  `NOT_REPRODUCED`.
- Contradictory signals, failed controls, missing attribution, or insufficient
  telemetry produce `INCONCLUSIVE`.
- `INCONCLUSIVE` and `INVALID_ENVIRONMENT` cannot be reported as success.
- The rationale must cite evidence represented in the input records; model or
  analyst assertion alone is insufficient.

## 19. `case-manifest.schema.json`

### 19.1 Purpose

The case manifest is the root index for one replayable vulnerability package.
It connects independently versioned records and artifacts without duplicating
large evidence or stage outputs.

Proposed canonical identity:

```text
urn:dacn:schema:case-manifest:1.0.0
```

### 19.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `case-manifest`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `case-manifest` kind and identifies this immutable manifest version. |
| `created_at` | UTC timestamp | Required | Initial package creation time. |
| `created_by` | actor identity | Required | Package creator. |
| `case_id` | stable entity ID | Required | Must use the `case` kind and remains stable across manifest versions. |
| `case_key` | non-empty string | Required | Stable human-readable key, normally derived from the primary public identifier. |
| `package_version` | semantic version | Required | Version of this case package, independent of schema versions. |
| `status` | enum | Required | `draft`, `intake_complete`, `buildable`, `replayable`, `verified`, `not_reproduced`, `inconclusive`, `invalid_environment`, or `archived`. |
| `vulnerability_id` | record ID | Required | Current normalized vulnerability record. |
| `source_ids` | array of record IDs | Required | All source snapshots used by the package; at least one. |
| `revision_resolution_id` | record ID | Optional | Current revision resolution. |
| `patch_context_id` | record ID | Optional | Current static patch context. |
| `environment_spec_ids` | array of record IDs | Required | May be empty before environment design. |
| `build_ids` | array of record IDs | Required | May be empty before building. |
| `artifact_ids` | array of record IDs | Required | Complete artifact inventory for this package. |
| `execution_spec_ids` | array of record IDs | Required | May be empty before execution planning. |
| `execution_ids` | array of record IDs | Required | May be empty before execution. |
| `verification_policy_ids` | array of record IDs | Required | Preserves current and superseded policies used in results. |
| `verification_result_ids` | array of record IDs | Required | Attempt history; may be empty. |
| `current_verification_result_id` | record ID | Conditional | Required when a final case status reflects a verdict. |
| `attempt_ids` | array of record IDs | Required | All retained attempts. |
| `pipeline_run_ids` | array of record IDs | Required | All pipeline runs for the package. |
| `validation_result_ids` | array of record IDs | Required | Validation results consumed while assembling this manifest; excludes validation of this manifest itself. |
| `replay` | replay descriptor | Conditional | Required when status is replayable or any final-verdict state. |
| `compatibility` | compatibility object | Required | Required reader/schema versions and migrations. |
| `supersedes_case_manifest_id` | record ID | Optional | Prior manifest version. |
| `provenance` | provenance event | Required | Assembly inputs and method. |
| `extensions` | object | Optional | Controlled package extensions. |

### 19.3 Replay and compatibility

The `replay descriptor` contains:

- replay entry-point artifact reference;
- interface version;
- argument array;
- relative working directory;
- required environment-spec IDs;
- expected pipeline stages;
- network requirements, which must normally be none after acquisition;
- concise prerequisites and limitations.

The `compatibility` object contains minimum reader version, complete mapping of
schema names to exact versions, optional migration-record IDs, and whether
unknown extensions must be preserved.

### 19.4 Conditional and semantic rules

1. All referenced records exist, have expected schema types, and belong to this
   case or are explicitly shared immutable records.
2. Artifact inventory includes every artifact reachable from package records.
3. `verified`, `not_reproduced`, `inconclusive`, and `invalid_environment`
   statuses agree with the current verification result verdict.
4. `verified` requires a replay descriptor and a `VERIFIED` result.
5. `replayable` means the package can execute in its declared Docker container;
   it does not imply successful reproduction.
6. Package updates keep `case_id`, create a new manifest `record_id`, and link
   through supersession; evidence records are not silently replaced.
7. No host-specific absolute path, secret, or dangling reference is allowed.
8. Package validation includes artifact hashes and cross-record invariants, not
   only JSON Schema validity.
9. Validation of this manifest or complete package is represented by a later
   validation-result record. It may be indexed by a superseding manifest but
   cannot be a forward reference in the manifest it validates.

## 20. `attempt-record.schema.json`

### 20.1 Purpose

An attempt record preserves one bounded try at a pipeline stage, including
failures, diagnosis, repairs, resource use, and intervention. Attempts make
failed trajectories first-class research data.

Proposed canonical identity:

```text
urn:dacn:schema:attempt-record:1.0.0
```

### 20.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `attempt-record`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `attempt` kind. |
| `created_at` | UTC timestamp | Required | Record creation time. |
| `created_by` | actor identity | Required | Attempt recorder. |
| `case_id` | stable entity ID | Required | Owning case identity; must use the `case` kind. |
| `pipeline_run_id` | record ID | Required | Containing pipeline run. |
| `stage` | stage enum | Required | `collect`, `normalize`, `resolve`, `build`, `extract`, `execute`, `verify`, or `report`. |
| `sequence` | integer | Required | Non-negative order within the stage. |
| `parent_attempt_id` | record ID | Optional | Attempt whose outcome led to this retry. |
| `trigger` | enum | Required | `initial`, `retry`, `resume`, `repair`, or `manual_request`. |
| `status` | enum | Required | `succeeded`, `failed`, `interrupted`, `cancelled`, or `invalid`. |
| `started_at` | UTC timestamp | Required | Attempt start. |
| `completed_at` | UTC timestamp | Required | Attempt end. |
| `duration_ms` | duration | Required | Monotonic elapsed duration. |
| `inputs` | array of record or artifact references | Required | Declared inputs; may be empty only for initial collection. |
| `outputs` | array of record or artifact references | Required | Produced outputs; may be empty on early failure. |
| `failure` | failure record | Conditional | Required for failed or invalid attempts. |
| `termination_reason` | non-empty string | Conditional | Required for interrupted or cancelled attempts. |
| `diagnosis` | diagnosis object | Conditional | Required when a retry or repair follows a failure. |
| `repairs` | array of repair records | Optional | Changes applied in this attempt. |
| `intervention` | intervention object | Required | Human/model/tool contribution level. |
| `resource_usage` | resource-usage object | Required | Time, compute, storage, and optional monetary cost. |
| `budget` | attempt-budget object | Optional | Limits assigned to the attempt. |
| `provenance` | provenance event | Required | Exact method and actors. |
| `extensions` | object | Optional | Controlled stage extensions. |

### 20.3 Diagnosis, intervention, and budget

A `diagnosis` contains primary failure class, alternative failure classes,
summary, evidence, confidence assessment, and recommended next action. A repair
must address the diagnosed failure class; unrelated trial-and-error must remain
visible as such.

The `intervention` object contains level (`none`, `configuration_only`,
`human_ground_truth`, `manual_strategy`, `manual_artifact_edit`, or `other`),
actor identities, description, and whether the intervention is permitted by
the current experiment policy.

The `attempt budget` contains timeout, retry allowance, CPU allowance, memory
limit, disk limit, and optional monetary limit with currency.

### 20.4 Conditional and semantic rules

1. Retry, resume, and repair attempts require a parent attempt.
2. Parent attempts belong to the same case and pipeline stage unless a
   cross-stage dependency is explicitly represented through inputs.
3. Failed and invalid attempts require a failure record.
4. Successful attempts cannot hide failed child commands or invalid outputs.
5. Attempts never overwrite earlier outputs; replacements use new record IDs.
6. Manual intervention forbidden by an experiment policy invalidates that
   attempt for the controlled evaluation but does not erase it.
7. Resource use and retry counts contribute to experiment metrics.
8. Attempt IDs may be allocated before their output records. The attempt and
   its produced records must be published as one consistency unit so neither
   side contains a dangling reference.

## 21. `pipeline-run.schema.json`

### 21.1 Purpose

A pipeline-run record tracks one resumable traversal of the Phase 1 pipeline
and connects stage status, attempts, budgets, versions, and final outputs.

Proposed canonical identity:

```text
urn:dacn:schema:pipeline-run:1.0.0
```

### 21.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `pipeline-run`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `pipeline-run` kind. |
| `created_at` | UTC timestamp | Required | Run-record creation time. |
| `created_by` | actor identity | Required | Orchestrating component. |
| `case_id` | stable entity ID | Required | Target case identity; must use the `case` kind. |
| `pipeline_identity` | pipeline identity | Required | Name, version, source revision, and configuration artifact. |
| `mode` | enum | Required | `development`, `benchmark_curation`, `baseline_evaluation`, or `replay`. |
| `status` | enum | Required | `pending`, `running`, `succeeded`, `failed`, `interrupted`, or `cancelled`. |
| `started_at` | UTC timestamp | Required | Run start. |
| `completed_at` | UTC timestamp | Conditional | Required for terminal status. |
| `duration_ms` | duration | Conditional | Required for terminal status. |
| `resumed_from_run_id` | record ID | Optional | Earlier interrupted run. |
| `stages` | array of pipeline-stage records | Required | Exactly one ordered entry for each configured stage. |
| `attempt_ids` | array of record IDs | Required | All attempts associated with this run. |
| `input_records` | array of record references | Required | Declared run inputs. |
| `output_records` | array of record references | Required | Final outputs produced. |
| `budget` | run-budget object | Required | Time, retries, compute, storage, and optional monetary budget. |
| `resource_usage` | resource-usage object | Required | Actual aggregate use. |
| `intervention_summary` | intervention-summary object | Required | Counts and highest intervention level. |
| `validation_result_ids` | array of record IDs | Required | Validation outcomes consumed during the run; excludes validation of this run record itself. |
| `failure` | failure record | Conditional | Required for failed terminal status. |
| `termination_reason` | non-empty string | Conditional | Required for interrupted or cancelled runs. |
| `provenance` | provenance event | Required | Orchestration method and inputs. |
| `extensions` | object | Optional | Controlled pipeline extensions. |

### 21.3 Stage records

Each pipeline-stage record contains stage name, status, dependency stage names,
start/end times, attempt IDs, selected successful attempt ID, input/output
record references, failure summary, and resume token artifact when applicable.

The configured stage order is:

```text
collect -> normalize -> resolve -> build -> extract -> execute -> verify -> report
```

Stages may be skipped only with an explicit reason and only when their outputs
are supplied as declared validated inputs.

### 21.4 Conditional and semantic rules

1. A stage cannot start until required predecessor outputs are available.
2. Concurrent work may occur only where declared dependencies allow it.
3. The selected attempt is one of the stage's attempts and has compatible
   status.
4. Resumption preserves prior attempt and artifact identities.
5. Run success requires every required stage to succeed or be validly skipped.
6. Failure records retain the stage-specific failure taxonomy.
7. The run records all supplied information and intervention; hidden hints or
   repairs are prohibited.
8. Pipeline and schema versions are frozen for controlled evaluation.
9. A pipeline-run ID may be allocated before attempts begin. Released packages
   contain a terminal run record whose attempt references all resolve;
   transient running state is not accepted as final research evidence.
10. Validation of the terminal pipeline-run record is external to that record
    and must not appear as a forward self-validation reference.

## 22. `benchmark-case.schema.json`

### 22.1 Purpose

A benchmark-case record stores manually reviewed ground truth and dataset
membership separately from automated pipeline outputs.

Proposed canonical identity:

```text
urn:dacn:schema:benchmark-case:1.0.0
```

### 22.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `benchmark-case`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `benchmark-case` kind. |
| `created_at` | UTC timestamp | Required | Ground-truth record creation time. |
| `created_by` | actor identity | Required | Curator or curation system. |
| `dataset_name` | non-empty string | Required | Benchmark dataset identity. |
| `dataset_version` | semantic version | Required | Immutable release version. |
| `case_id` | stable entity ID | Required | Stable benchmark case identity. |
| `case_manifest_id` | record ID | Required | Exact case-manifest version reviewed as ground truth. |
| `split` | enum | Required | `development`, `validation`, or `held_out`. |
| `eligibility` | eligibility object | Required | Disclosure, retrievability, platform, and scope checks. |
| `ground_truth` | ground-truth object | Required | Human-reviewed vulnerable/fixed facts. |
| `reference_replay` | reference-replay object | Optional | Known-good minimal replay package or artifact. |
| `limitations` | array of non-empty strings | Required | May be empty but must be explicit. |
| `review` | review object | Required | Reviewers, method, dates, and disposition. |
| `selection_metadata` | selection object | Required | Sampling dimensions and inclusion rationale. |
| `provenance` | provenance event | Required | Curation inputs and method. |
| `supersedes_benchmark_case_id` | record ID | Optional | Prior ground-truth revision. |
| `extensions` | object | Optional | Controlled dataset extensions. |

### 22.3 Ground truth and review

The `eligibility` object records publicly disclosed status, usable fix evidence,
open-source and license status, Linux compatibility, historical-source
retrievability, safety review, and exclusion reasons.

The `ground-truth` object contains:

- primary vulnerability identifier;
- vulnerable revision and justification;
- patched revision and justification;
- patch/fixed-version evidence;
- vulnerability class;
- root-cause statement and evidence;
- expected observable signal;
- required code/state evidence;
- known prerequisites;
- expected patched behavior;
- required negative controls;
- environment constraints.

Each substantive ground-truth statement has evidence references and a
classification. Ground truth may be manually reviewed, but it still requires
public evidence.

The `review` object contains pseudonymous reviewer IDs, independence
requirements, review rounds, completed timestamp, status (`approved`,
`changes_required`, `rejected`, or `retired`), and notes artifact.

`selection metadata` records project, language, vulnerability class,
complexity stratum, build difficulty, observable type, inclusion rationale,
and sampling weight when applicable.

### 22.4 Conditional and semantic rules

1. Only approved, eligible cases enter released benchmark splits.
2. Held-out ground truth is access-controlled from evaluated pipelines even
   though the underlying vulnerability is public.
3. Curation intervention is recorded but does not count as baseline execution
   intervention.
4. Split assignment is stable within a dataset version.
5. Dataset updates create a new dataset version and retain removed or retired
   case history.
6. Ground truth cannot be inferred solely from an automated pipeline verdict.
7. Selection metadata supports diversity and bias analysis across projects,
   languages, classes, and difficulty.

## 23. `experiment-manifest.schema.json`

### 23.1 Purpose

An experiment manifest freezes the design of a Phase 1 research experiment
before evaluation begins.

Proposed canonical identity:

```text
urn:dacn:schema:experiment-manifest:1.0.0
```

### 23.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `experiment-manifest`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `experiment` kind. |
| `created_at` | UTC timestamp | Required | Manifest freeze time. |
| `created_by` | actor identity | Required | Experiment owner. |
| `name` | non-empty string | Required | Experiment name. |
| `research_questions` | array of non-empty strings | Required | At least one RQ identifier or statement. |
| `hypotheses` | array of hypothesis objects | Required | May be empty for descriptive studies. |
| `dataset` | dataset-selection object | Required | Benchmark name, version, splits, cases, and exclusions. |
| `conditions` | array of experiment-condition objects | Required | At least one evaluated pipeline condition. |
| `information_policy` | information-policy object | Required | Sources and hints available to each condition. |
| `intervention_policy` | intervention-policy object | Required | Allowed human or model involvement. |
| `budgets` | experiment-budget object | Required | Comparable limits by condition. |
| `metrics` | array of metric-definition objects | Required | Primary and secondary metrics. |
| `exclusion_policy` | exclusion-policy object | Required | Predeclared exclusion reasons and handling. |
| `determinism` | determinism object | Required | Seeds, ordering, retries, and frozen versions. |
| `reporting_policy` | reporting-policy object | Required | Denominators, missing data, and failure reporting. |
| `registered_at` | UTC timestamp | Required | Time the design was frozen. |
| `provenance` | provenance event | Required | Design sources and authorship. |
| `supersedes_experiment_id` | record ID | Optional | Earlier preregistration revision; prohibited after runs begin except correction with disclosure. |
| `extensions` | object | Optional | Controlled research extensions. |

### 23.3 Experimental configuration

`dataset selection` identifies exact benchmark version, included splits and
case IDs, ordered or randomized evaluation sequence, and pre-run exclusions.

Each `experiment condition` contains condition ID, name, pipeline identity,
schema-version map, configuration artifacts, enabled stages, instrumentation,
and whether the condition is the non-agentic baseline.

`information policy` enumerates allowed source roles, patch visibility,
ground-truth visibility, reference-artifact visibility, and prohibited hidden
hints for every condition.

`intervention policy` enumerates allowed intervention levels, who may perform
them, whether intervention invalidates a case, and how it is counted.

Each `metric definition` contains metric ID, name, unit of analysis, numerator,
denominator, direction, aggregation, missing-data treatment, and primary/secondary
designation.

### 23.4 Conditional and semantic rules

1. The manifest is immutable after the first associated pipeline run starts.
2. Conditions use the same benchmark split and comparable budgets unless a
   declared experimental factor intentionally differs.
3. Pipeline, schemas, configurations, and supplied information are frozen.
4. Development and held-out cases cannot overlap.
5. Exclusions and missing-data treatment are declared before outcomes are seen.
6. Metrics include environment success, CVE-specific reproduction success,
   oracle false-positive rate, time, repairs, resources, and intervention.
7. Human ground truth is not exposed to conditions unless explicitly part of
   the research design.

## 24. `experiment-result.schema.json`

### 24.1 Purpose

An experiment result aggregates immutable per-case outcomes under one frozen
experiment manifest while preserving denominators, exclusions, failures, and
resource costs.

Proposed canonical identity:

```text
urn:dacn:schema:experiment-result:1.0.0
```

### 24.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `experiment-result`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `experiment-result` kind. |
| `created_at` | UTC timestamp | Required | Result creation time. |
| `created_by` | actor identity | Required | Analysis pipeline or analyst. |
| `experiment_id` | record ID | Required | Frozen experiment manifest. |
| `status` | enum | Required | `complete`, `partial`, `invalid`, or `superseded`. |
| `started_at` | UTC timestamp | Required | Experiment execution start. |
| `completed_at` | UTC timestamp | Required | Experiment execution end. |
| `condition_results` | array of condition-result objects | Required | One per manifest condition. |
| `case_results` | array of case-result references | Required | Every included case-condition unit. |
| `exclusions` | array of exclusion-result objects | Required | May be empty but explicit. |
| `metrics` | array of metric-result objects | Required | Results for every declared metric. |
| `failure_distribution` | array of failure-count objects | Required | Counts and denominators by failure class. |
| `resource_summary` | resource-summary object | Required | Time, compute, storage, and monetary totals. |
| `intervention_summary` | intervention-summary object | Required | Counts and rates by intervention level. |
| `missing_data` | array of missing-data objects | Required | May be empty but explicit. |
| `limitations` | array of non-empty strings | Required | May be empty but explicit. |
| `analysis_artifacts` | array of artifact references | Required | Tables, scripts, and derived analysis outputs. |
| `validation_result_ids` | array of record IDs | Required | Validation of aggregation inputs consumed by this result; excludes validation of this result itself. |
| `provenance` | provenance event | Required | Analysis method and inputs. |
| `supersedes_result_id` | record ID | Optional | Corrected prior result. |
| `extensions` | object | Optional | Controlled analysis extensions. |

### 24.3 Result units and metrics

Each `case-result reference` contains condition ID, benchmark-case ID,
pipeline-run ID, current verification-result ID, inclusion status, final
verdict, environment status, elapsed times, resource use, repair count, and
intervention level.

Each `metric result` contains metric ID, numerator count, denominator count,
computed value, optional confidence interval and method, condition ID, and
contributing case-result IDs.

Each exclusion records benchmark case, condition where applicable, predeclared
reason code, explanation, decision time, actor, and whether it changes the
primary denominator.

### 24.4 Conditional and semantic rules

1. Every manifest case-condition unit appears as included, excluded, or missing;
   none may disappear silently.
2. Numerators and denominators recompute from referenced per-case results.
3. `INCONCLUSIVE` and `INVALID_ENVIRONMENT` never count as reproduced.
4. Patched/control false positives are reported explicitly.
5. Exclusions conform to the preregistered policy; post-outcome exclusions are
   separately disclosed.
6. Failures, retries, and missing data remain in aggregate reporting.
7. Condition comparisons use the declared unit of analysis and comparable
   budgets.
8. Analysis artifacts and scripts are hashed and replayable.
9. Validation of the experiment-result record is external and cannot be
   referenced by the same immutable result.

## 25. `case-report.schema.json`

### 25.1 Purpose

A case report is a concise, derived presentation of one case outcome. It is not
primary evidence and must reference the records and artifacts supporting every
material statement.

Proposed canonical identity:

```text
urn:dacn:schema:case-report:1.0.0
```

### 25.2 Top-level fields

| Field | Type | Presence | Constraints and meaning |
|---|---|---|---|
| `schema_name` | string | Required | Constant `case-report`. |
| `schema_version` | semantic version | Required | Constant `1.0.0`. |
| `record_id` | record ID | Required | Must use the `case-report` kind. |
| `created_at` | UTC timestamp | Required | Report generation time. |
| `created_by` | actor identity | Required | Reporting tool or author. |
| `case_id` | stable entity ID | Required | Stable reported case identity. |
| `case_manifest_id` | record ID | Required | Exact case-manifest version summarized. |
| `verification_result_id` | record ID | Required | Authoritative verdict source. |
| `title` | non-empty string | Required | Case title. |
| `summary` | non-empty string | Required | Concise outcome without overstating evidence. |
| `environment_status` | report section | Required | Reconstruction and comparability summary. |
| `trigger_status` | report section | Required | Candidate artifact and harness summary. |
| `vulnerable_execution` | execution-summary section | Required | Observed vulnerable behavior. |
| `patched_execution` | execution-summary section | Required | Observed patched behavior. |
| `negative_controls` | array of execution-summary sections | Required | At least one when the policy requires controls. |
| `code_region_evidence` | report section | Required | Static and dynamic target-region evidence. |
| `root_cause_assessment` | report section | Required | Patch consistency and attribution. |
| `verdict` | verification verdict | Required | Must match the referenced verification result. |
| `confirmed_facts` | array of report statements | Required | May be empty but explicit. |
| `strong_inferences` | array of report statements | Required | May be empty. |
| `hypotheses` | array of report statements | Required | May be empty. |
| `unknowns` | array of report statements | Required | May be empty. |
| `remaining_uncertainty` | array of uncertainty items | Required | May be empty. |
| `replay` | replay summary | Required | Entry point, prerequisites, and expected outputs. |
| `artifact_index` | array of artifact references | Required | Material evidence only, not necessarily every package artifact. |
| `limitations` | array of non-empty strings | Required | May be empty but explicit. |
| `provenance` | provenance event | Required | Report-generation inputs and method. |
| `extensions` | object | Optional | Controlled presentation extensions. |

### 25.3 Report sections and statements

A `report section` contains status, summary, evidence references, and optional
limitations. An `execution-summary section` additionally contains execution ID,
role, exit/signal/timeout summary, matched signals, reachability summary, and
raw output artifact references.

Each `report statement` contains text and at least one evidence reference. Its
classification is determined by the array containing it and cannot be
overridden inside the statement.

The `replay summary` contains replay entry-point artifact, environment-spec IDs,
argument array, expected duration range, expected artifact outputs, and a
warning that the replay must run only in the project-controlled Docker
environment.

### 25.4 Conditional and semantic rules

1. Verdict and all execution summaries agree with referenced records.
2. Report statements cannot introduce evidence absent from the package.
3. Confirmed facts, inferences, hypotheses, and unknowns remain visibly
   separated.
4. Failure and inconclusive cases receive the same required sections as
   successful cases.
5. Raw logs are linked as artifacts, not embedded in full.
6. Replay instructions are case-relative and contain no host credentials or
   public target addresses.
7. A report cannot upgrade a verification verdict or omit failed controls.

## 26. Complete Schema Coverage

The field-design document now covers the complete planned Phase 1 schema
family:

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

The dependency direction remains Phase 1-oriented:

```text
evidence and metadata
    -> revision and patch understanding
    -> environment and build observations
    -> bounded execution evidence
    -> independent verification
    -> replayable case package
    -> benchmark and experiment reporting
```

These schemas define data contracts only. They do not add Phase 2 agents,
autonomous test generation, or model-dependent verification.
