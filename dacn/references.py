"""Schema-owned reference locations; arbitrary source/claim values are not links."""

from dataclasses import dataclass
from typing import Iterator

from .contracts import Record, pointer


@dataclass(frozen=True)
class Reference:
    path: str
    identifier: str
    schema: str | None
    sha256: str | None = None


# '*' traverses array items or named object members, but only at declared paths.
RECORD_LINKS = {
    "source-record": (),
    "artifact-record": (),
    "vulnerability-record": (("sources/*", "source-record"), ("claims/*/source_id", "source-record")),
    "environment-spec": (),
    "build-record": (("environment_id", "environment-spec"),),
    "execution-record": (("build_id", "build-record"),),
    "verification-result": (
        ("executions/vulnerable", "execution-record"), ("executions/patched", "execution-record"),
        ("executions/negative_controls/*", "execution-record"),
    ),
    "case-manifest": (
        ("vulnerability_id", "vulnerability-record"), ("source_ids/*", "source-record"),
        ("environment_id", "environment-spec"), ("builds/*", "build-record"),
        ("artifact_ids/*", "artifact-record"), ("verification_result_id", "verification-result"),
        ("executions/vulnerable", "execution-record"), ("executions/patched", "execution-record"),
        ("executions/negative_controls/*", "execution-record"),
    ),
}
ARTIFACT_LINKS = {
    "source-record": ("content", "error/evidence/*"),
    "artifact-record": ("derived_from/*",),
    "vulnerability-record": (
        "claims/*/evidence/*", "failure/evidence/*", "patch/diff", "patch/evidence/*",
        "patch/static_context/reachability/evidence/*",
    ),
    "environment-spec": ("dependencies/manifests/*", "dependencies/locks/*"),
    "build-record": (
        "commands/*/stdout", "commands/*/stderr", "outputs/*", "failure/evidence/*",
        "dependency_resolution/inventory", "dependency_inventory", "repairs/*/artifact",
    ),
    "execution-record": (
        "executable", "input", "stdout", "stderr", "sanitizer_report", "stack_trace",
        "coverage_summary", "generated_outputs/*", "failure/evidence/*",
    ),
    "verification-result": (
        "evidence/*", "checks/*/evidence/*", "oracle/adapter/implementation", "oracle/case_definition",
    ),
    "case-manifest": ("failure/evidence/*", "replay/entry_point"),
}


def _values(value, route: tuple[str, ...], location: tuple = ()):
    if not route:
        yield pointer(location), value
    elif route[0] == "*":
        items = value.items() if isinstance(value, dict) else enumerate(value)
        for key, child in items:
            yield from _values(child, route[1:], (*location, key))
    elif isinstance(value, dict) and route[0] in value:
        yield from _values(value[route[0]], route[1:], (*location, route[0]))


def references(record: Record) -> Iterator[Reference]:
    """Call only after structural validation."""
    schema = record["schema"]
    links = (("provenance/inputs/*", None), *RECORD_LINKS[schema])
    for route, expected in links:
        for path, identifier in _values(record, tuple(route.split("/"))):
            yield Reference(path, identifier, expected)
    for route in ARTIFACT_LINKS[schema]:
        for path, value in _values(record, tuple(route.split("/"))):
            yield Reference(path, value["id"], "artifact-record", value["sha256"])
    if schema == "artifact-record" and "producer" in record:
        producer = record["producer"]
        yield Reference("/producer", producer["id"], producer["schema"])
