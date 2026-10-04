"""Read-only package validation CLI; stdout is a persistable JSON report."""

import argparse
from pathlib import Path
import sys

from .contracts import ContractError, Diagnostic, SchemaCatalog, canonical_json, utc_now
from .storage import CaseStore, DEFAULT_MAX_ARTIFACT_BYTES, DEFAULT_MAX_RECORD_BYTES, StorageError
from .validation import PackageValidator, ValidationReport


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check package integrity; does not execute targets or derive CVE verdicts.")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--root", type=Path, required=True)
    validate.add_argument("--schemas", type=Path, required=True)
    validate.add_argument("--manifest-id", required=True)
    validate.add_argument("--max-artifact-bytes", type=int, default=DEFAULT_MAX_ARTIFACT_BYTES)
    validate.add_argument("--max-record-bytes", type=int, default=DEFAULT_MAX_RECORD_BYTES)
    validate.add_argument("--max-records", type=int, default=10000)
    args = parser.parse_args(argv)
    try:
        catalog = SchemaCatalog(args.schemas)
        store = CaseStore(args.root, catalog, max_artifact_bytes=args.max_artifact_bytes,
                          max_record_bytes=args.max_record_bytes)
        records = store.load_records(max_records=args.max_records)
        report = PackageValidator(catalog, max_artifact_bytes=args.max_artifact_bytes,
                                  max_records=args.max_records).validate(args.root, args.manifest_id, records)
        status = 0 if report.valid else 1
    except ContractError as error:
        report = ValidationReport(args.manifest_id, utc_now(), error.diagnostics, {})
        status = 2
    except StorageError as error:
        report = ValidationReport(args.manifest_id, utc_now(), (
            Diagnostic(error.code, error.failure_class, str(error)),
        ), {})
        status = 2
    except (OSError, ValueError, RecursionError):
        report = ValidationReport(args.manifest_id, utc_now(), (
            Diagnostic("validation_unavailable", "configuration_failure",
                       "Cannot load the declared package/schema inputs or validation limits."),
        ), {})
        status = 2
    sys.stdout.buffer.write(canonical_json(report.to_dict()))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
