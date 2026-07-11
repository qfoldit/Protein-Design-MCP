# AlphaFold3 via alphafold3_mcp — corrected integration note

**This corrects an earlier assumption in this skill.** AlphaFold3 is
accessed through [MacromNex/alphafold3_mcp](https://github.com/MacromNex/alphafold3_mcp),
which is **its own separate MCP server** — not something
qFoldIT's bionemo-agent-toolkit should reimplement a Docker-lifecycle
wrapper around. This is the same pattern qFoldIT uses elsewhere (unity-mcp,
UnrealClaude, kit-usd-agents): when an official/community MCP bridge
already exists for a tool, connect to it directly rather than duplicating
its functionality.

## What was verified this session

- The server is registered with Claude Code as a local Python process,
  e.g.:
  ```json
  {
    "mcpServers": {
      "alphafold3": {
        "command": "/path/to/alphafold3_mcp/env/bin/python",
        "args": ["/path/to/alphafold3_mcp/src/server.py"]
      }
    }
  }
  ```
  (source: a third-party MCP directory listing, not alphafold3_mcp's own
  README directly — re-confirm the exact `claude mcp add` command against
  the repo before relying on it.)
- Setup uses a `quick_setup.sh` script that creates a conda/mamba
  environment and prints the Claude Code configuration; manual setup is
  documented in the repo's `reports/step3_environment.md`.
- **Prerequisites**: an AlphaFold3 model-weights license from Google
  DeepMind ([google-deepmind/alphafold3](https://github.com/google-deepmind/alphafold3),
  CC-BY-NC-SA 4.0 terms), plus ~2TB of genetic databases, plus GPU compute
  (DeepMind's own reference setup recommends A100/H100-class GPUs for
  reasonable runtime on multi-chain complexes).

## What was NOT verified this session

The exact tool names and parameters `alphafold3_mcp`'s server exposes over
MCP were not independently confirmed (its `src/server.py` was not read in
this session). **Do not assume a tool name — introspect the connected
server's actual tool list** the same way qFoldIT treats every other
external bridge (unity-mcp, UnrealClaude, kit-usd-agents): the schemas are
visible to Claude automatically once the server is connected in the same
session.

## What this means for this skill

- `bionemo_client.py` in this skill only wraps NIMs that do **not** already
  have their own MCP server (AlphaFold2, DiffDock, MolMIM, Evo 2, Boltz-2
  — see `api_reference.md`).
- For AlphaFold3, install and connect `alphafold3_mcp` separately, then use
  its own tools directly in the same chat/session.
- The previously-planned `scripts/smoke_test_af3.py` and
  `scripts/smoke_test_pipeline.py` (testing a bespoke Docker-managed AF3
  lifecycle) have been removed for this reason — there is nothing of
  qFoldIT's own to smoke-test for AF3 once the separation of concerns
  above is applied. If a future contributor still wants an integration
  test, it should exercise calling `alphafold3_mcp`'s real tools (once
  their names are confirmed) followed by `bionemo_client.dock_ligand(...)`
  on the resulting structure — a genuine AF3 → DiffDock pipeline test.
