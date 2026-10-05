# DACN

Research infrastructure for replayable, evidence-based reproduction of disclosed
1-day vulnerabilities. Read [AGENTS.md](AGENTS.md) before starting work.

The current implementation includes versioned JSON Schemas, immutable case-local
artifact storage, and an offline semantic package validator. Docker builders,
the execution harness, and the CVE-specific verification oracle remain planned.

- [Documentation index](docs/README.md)
- [Package storage, validation API, and CLI](docs/package-foundation.md)
- [Schema usage](docs/schema-usage-guide.md) and [compatibility](docs/schema-compatibility.md)
- [Verification and execution contract](docs/verification-contract.md)
- [Docker-only test workflow](tests/schema/README.md)

Package validity establishes integrity and consistency. It does not establish
successful vulnerability reproduction.
