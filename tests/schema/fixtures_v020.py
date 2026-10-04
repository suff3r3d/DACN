"""Synthetic structural examples, not complete packages or migration code."""

from copy import deepcopy

from .fixtures import VALID as LEGACY_VALID, artifact_ref


VALID = deepcopy(LEGACY_VALID)
for record in VALID.values():
    record["schema_version"] = "0.2.0"

CHECK_KEYS = tuple(VALID["verification-result"]["checks"])
for check in VALID["verification-result"]["checks"].values():
    del check["passed"]
    check["status"] = "passed"

VALID["verification-result"]["oracle"] = {
    "name": "fixture-oracle",
    "version": "0.2.0",
    "adapter": {
        "name": "synthetic-parser",
        "version": "1.0.0",
        "implementation": artifact_ref("artifact-adapter-source"),
    },
    "case_definition": artifact_ref("artifact-reviewed-case"),
}
VALID["case-manifest"]["artifact_ids"].extend([
    "artifact-adapter-source", "artifact-reviewed-case",
])


def check(status, summary, evidence_id=None, reason=None):
    value = {
        "status": status,
        "summary": summary,
        "evidence": [artifact_ref(evidence_id)] if evidence_id else [],
    }
    if reason is not None:
        value["reason"] = reason
    return value


def docker_unavailable():
    value = deepcopy(VALID["verification-result"])
    del value["executions"]
    value["provenance"]["inputs"] = ["artifact-docker-diagnostic"]
    value["verdict"] = "INVALID_ENVIRONMENT"
    value["failure_class"] = "configuration_failure"
    value["rationale"] = "Docker preflight failed; no target commands ran."
    value["evidence"] = [artifact_ref("artifact-docker-diagnostic")]
    value["checks"] = {
        name: check(
            "not_evaluated", "No execution observations exist.",
            reason="Docker preflight prevented builds and executions.",
        )
        for name in CHECK_KEYS
    }
    value["checks"]["environment_and_build_identity"] = check(
        "failed", "Docker daemon is unavailable.", "artifact-docker-diagnostic",
    )
    return value


def partial_manifest(status="draft"):
    value = deepcopy(VALID["case-manifest"])
    for key in ("vulnerability_id", "source_ids", "environment_id", "builds", "executions", "replay"):
        del value[key]
    value["status"] = status
    value["artifact_ids"] = ["artifact-docker-diagnostic"]
    value["failure"] = {
        "stage": "build",
        "class": "configuration_failure",
        "summary": "Docker preflight failed before any build command ran.",
        "evidence": [artifact_ref("artifact-docker-diagnostic")],
    }
    if status in ("draft", "buildable"):
        del value["verification_result_id"]
        value["provenance"]["inputs"] = ["artifact-docker-diagnostic"]
    return value


def non_success(verdict, check_name, failure_class):
    value = deepcopy(VALID["verification-result"])
    value["verdict"] = verdict
    value["failure_class"] = failure_class
    value["checks"][check_name] = check(
        "failed", "Observed fixture condition does not satisfy the check.",
        "artifact-comparison-observation",
    )
    value["rationale"] = "Synthetic observations support this non-success verdict."
    return value
