# Schema contract tests

The suite validates the complete `0.1.0` MVP registry without network access.
It checks Draft 2020-12 validity, duplicate JSON keys, every `$ref`, the exact
schema inventory, and one explicit valid and targeted invalid record per
persisted schema.

Run from the repository root:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```
