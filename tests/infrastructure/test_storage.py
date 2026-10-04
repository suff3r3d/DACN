from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from dacn.contracts import ContractError, SchemaCatalog, canonical_json
from dacn.storage import CaseStore, StorageError, open_case_file
from .fixtures import PROVENANCE


ROOT = Path(__file__).resolve().parents[2]


class StorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = SchemaCatalog(ROOT / "schemas")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "case"
        self.store = CaseStore(self.root, self.catalog)

    def put(self, data=b"original bytes\x00\xff", identifier="artifact-log", store=None, **extra):
        return (store or self.store).put_bytes(
            data, identifier=identifier, case_id="case-001", kind="stdout",
            provenance=deepcopy(PROVENANCE), **extra,
        )

    def test_round_trip_preserves_exact_raw_bytes_and_provenance(self):
        data = b"raw\r\n\x00\xff"
        artifact = self.put(data)
        self.assertEqual(hashlib.sha256(data).hexdigest(), artifact.reference.sha256)
        self.assertEqual(len(data), artifact.size_bytes)
        self.assertEqual(PROVENANCE, self.store.load_records()[0]["provenance"])
        with open_case_file(self.root, artifact.path) as stream:
            self.assertEqual(data, stream.read())

    def test_empty_output_is_an_actual_hashed_artifact(self):
        artifact = self.put(b"")
        self.assertEqual(hashlib.sha256(b"").hexdigest(), artifact.reference.sha256)
        self.assertEqual(0, artifact.size_bytes)

    def test_same_record_is_idempotent_but_changed_id_content_is_rejected(self):
        first = self.put()
        self.assertEqual(first, self.put())
        with self.assertRaisesRegex(StorageError, "immutable record ID"):
            self.put(b"different")
        self.assertEqual([first.record], self.store.load_records())
        self.assertEqual(b"original bytes\x00\xff", (self.root / first.path).read_bytes())

    def test_derived_artifact_keeps_original_and_parent_reference(self):
        original = self.put()
        derived = self.put(b"redacted", "artifact-redacted", derived_from=(original.reference,))
        self.assertEqual([original.reference.to_dict()], derived.record["derived_from"])
        self.assertNotEqual(original.path, derived.path)
        self.assertEqual(b"original bytes\x00\xff", (self.root / original.path).read_bytes())

    def test_duplicate_bytes_share_blob_but_keep_distinct_records(self):
        first, second = self.put(), self.put(identifier="artifact-copy")
        self.assertEqual(first.path, second.path)
        self.assertEqual(2, len(self.store.load_records()))

    def test_stream_failure_never_publishes_partial_evidence(self):
        class Interrupted:
            calls = 0

            def read(self, size):
                self.calls += 1
                if self.calls == 1:
                    return b"partial"
                raise OSError("interrupted source")

        with self.assertRaises(OSError):
            self.store.put_artifact(Interrupted(), identifier="broken", case_id="case-001",
                                    kind="log", provenance=PROVENANCE)
        self.assertEqual([], self.store.load_records())
        self.assertEqual([], list((self.root / "artifacts" / "sha256").iterdir()))
        self.put(b"complete", "broken")
        self.assertEqual(1, len(self.store.load_records()))

    def test_size_limit_stops_without_publishing(self):
        small = CaseStore(self.root, self.catalog, max_artifact_bytes=3)
        with self.assertRaises(StorageError) as caught:
            self.put(b"four", store=small)
        self.assertEqual("size_limit", caught.exception.code)
        self.assertEqual([], small.load_records())
        self.put(b"abc", store=small)

    def test_nonbinary_or_nonblocking_input_is_not_silent_eof(self):
        for source in (io.StringIO("text"), unittest.mock.Mock(read=lambda size: None)):
            with self.subTest(source=type(source)), self.assertRaises(StorageError):
                self.store.put_artifact(source, identifier="broken", case_id="case-001",
                                        kind="log", provenance=PROVENANCE)

    def test_failed_record_publication_leaves_only_complete_reusable_blob(self):
        with patch.object(self.store, "put_record", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.put(b"complete")
        self.assertEqual([], self.store.load_records())
        blob = next((self.root / "artifacts" / "sha256").iterdir())
        self.assertEqual(b"complete", blob.read_bytes())
        self.put(b"complete")
        self.assertEqual(1, len(self.store.load_records()))

    def test_corrupt_existing_blob_is_not_reused_or_overwritten(self):
        artifact = self.put()
        path = self.root / artifact.path
        path.chmod(0o600)
        path.write_bytes(b"tampered")
        with self.assertRaises(StorageError) as caught:
            self.put()
        self.assertEqual("artifact_conflict", caught.exception.code)
        self.assertEqual(b"tampered", path.read_bytes())

    def test_concurrent_conflicting_ids_have_one_winner(self):
        def attempt(data):
            try:
                return self.put(data)
            except StorageError as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, [b"first", b"second"]))
        self.assertEqual(1, sum(isinstance(value, StorageError) for value in results))
        self.assertEqual(1, len(self.store.load_records()))

    def test_symlinked_store_directory_is_rejected(self):
        self.root.mkdir()
        (self.root / "artifacts").symlink_to(Path(self.temporary.name), target_is_directory=True)
        with self.assertRaises(OSError):
            self.put()
        self.assertFalse((Path(self.temporary.name) / "sha256").exists())

    def test_paths_cannot_escape_or_follow_links_or_read_fifo(self):
        artifact = self.put()
        (self.root / "alias").symlink_to(self.root / "artifacts", target_is_directory=True)
        (self.root / "linked").symlink_to(self.root / artifact.path)
        os.mkfifo(self.root / "pipe")
        paths = ["../outside", "/etc/passwd", "C:/outside", "C:\\outside", "./linked", "linked",
                 "alias/sha256/" + artifact.reference.sha256, "pipe"]
        for path in paths:
            with self.subTest(path=path), self.assertRaises((OSError, StorageError)):
                with open_case_file(self.root, path) as stream:
                    stream.read()

    def test_invalid_record_never_published(self):
        with self.assertRaises(ContractError):
            self.store.put_record({"schema": "artifact-record", "schema_version": "0.3.0"})
        self.assertFalse(self.root.exists())

    def test_available_artifact_cannot_be_registered_before_valid_bytes(self):
        original = self.put()
        record = deepcopy(original.record)
        record.update(id="artifact-unwritten", path="artifacts/not-present")
        with self.assertRaises(OSError):
            self.store.put_record(record)
        record["path"] = original.path
        record["sha256"] = "f" * 64
        with self.assertRaises(StorageError) as caught:
            self.store.put_record(record)
        self.assertEqual("artifact_integrity", caught.exception.code)
        self.assertEqual([original.record], self.store.load_records())

    def test_record_loader_rejects_malformed_duplicate_and_oversized_metadata(self):
        artifact = self.put()
        record_path = self.root / self.store.record_path(artifact.reference.id)
        for data in (b"{", b'{"id":"a","id":"b"}', b'{"value":NaN}'):
            record_path.chmod(0o600)
            record_path.write_bytes(data)
            with self.subTest(data=data), self.assertRaises(StorageError):
                self.store.load_records()
        record_path.write_bytes(canonical_json(artifact.record))
        small = CaseStore(self.root, self.catalog, max_record_bytes=16)
        with self.assertRaises(StorageError):
            small.load_records()

    def test_record_filename_and_count_are_checked(self):
        artifact = self.put()
        path = self.root / self.store.record_path(artifact.reference.id)
        path.rename(path.with_name("incorrect.json"))
        with self.assertRaises(StorageError) as caught:
            self.store.load_records()
        self.assertEqual("record_identity_mismatch", caught.exception.code)
        path.with_name("incorrect.json").rename(path)
        self.put(b"another", "artifact-two")
        with self.assertRaises(StorageError) as caught:
            self.store.load_records(max_records=1)
        self.assertEqual("record_count_limit", caught.exception.code)

    def test_pending_metadata_from_crash_is_ignored_not_promoted(self):
        artifact = self.put()
        (self.root / "records" / ".pending-interrupted").write_bytes(b'{"partial":')
        self.assertEqual([artifact.record], self.store.load_records())
