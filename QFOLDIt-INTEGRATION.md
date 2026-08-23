# qFoldIT Integration

`Protein-Design-MCP` is a domain adapter / scientific capability source for qFoldIT.

Canonical destination for new cross-domain contracts:

- `qfoldit/UEFN-QFOLDIT/crates/qfoldit-core`
- `qfoldit/UEFN-QFOLDIT/crates/scientific-mcp`
- `qfoldit/UEFN-QFOLDIT/crates/protein-adapter`

This repository should not define a parallel mission, provenance, UAG, or Scientific Action Envelope model.

## Rule

Protein-specific computation stays here or in its scientific upstream dependencies; qFoldIT orchestration, permissions, mission semantics and runtime contracts belong to the Rust workspace.
