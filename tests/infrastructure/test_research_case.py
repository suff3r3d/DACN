"""Offline integration checks for the retained real-world intake draft."""
from copy import deepcopy
from pathlib import Path
import unittest

from dacn.contracts import SchemaCatalog
from dacn.storage import CaseStore
from dacn.validation import PackageValidator


class ResearchCaseTests(unittest.TestCase):
    def test_renderer_case_integrity_and_corrupt_reference(self):
        repo = Path(__file__).resolve().parents[2]
        root = repo / 'cases/CVE-2025-11539'
        catalog = SchemaCatalog(repo / 'schemas')
        records = CaseStore(root, catalog).load_records()
        manifest_id = 'manifest-cve-2025-11539-intake-001'
        validator = PackageValidator(catalog)
        report = validator.validate(root, manifest_id, records)
        self.assertTrue(report.valid, report.diagnostics)
        manifest = next(r for r in records if r['id'] == manifest_id)
        self.assertEqual(manifest['status'], 'draft')
        self.assertNotIn('verification_result_id', manifest)
        self.assertFalse(any(r['schema'] in ('execution-record', 'build-record') for r in records))
        vulnerability = next(r for r in records if r['schema'] == 'vulnerability-record')
        self.assertNotEqual(vulnerability['revisions']['vulnerable'], vulnerability['revisions']['patched'])
        broken = deepcopy(records)
        broken_vulnerability = next(r for r in broken if r['schema'] == 'vulnerability-record')
        broken_vulnerability['patch']['diff']['sha256'] = '0' * 64
        rejected = validator.validate(root, manifest_id, broken)
        self.assertFalse(rejected.valid)
        self.assertIn('reference_hash_mismatch', {d.code for d in rejected.diagnostics})

    def test_draft_integrity_and_missing_evidence(self):
        repo = Path(__file__).resolve().parents[2]
        root = repo / 'cases/CVE-2026-28381'
        catalog = SchemaCatalog(repo / 'schemas')
        records = CaseStore(root, catalog).load_records()
        manifest_id = 'manifest-cve-2026-28381-intake-001'
        validator = PackageValidator(catalog)
        report = validator.validate(root, manifest_id, records)
        self.assertTrue(report.valid, report.diagnostics)
        manifest = next(r for r in records if r['id'] == manifest_id)
        self.assertEqual(manifest['status'], 'draft')
        self.assertNotIn('verification_result_id', manifest)
        vulnerability = next(r for r in records if r['schema'] == 'vulnerability-record')
        self.assertEqual(vulnerability['revision_status'], 'ambiguous')
        self.assertNotIn('revisions', vulnerability)
        broken = deepcopy(records)
        broken = [r for r in broken if r['id'] != 'raw-cve']
        self.assertFalse(validator.validate(root, manifest_id, broken).valid)
