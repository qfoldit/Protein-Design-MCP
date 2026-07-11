# Contributing to qFoldIT Skills

Thanks for considering a contribution. This repository packages Claude
skills as a marketplace (`.claude-plugin/marketplace.json` +
`.claude-plugin/plugin.json`) — each skill lives in `skills/<name>/` with
its own `SKILL.md`, `README.md`, `scripts/`, `references/`, and (where
applicable) `evals/eval_set.json`.

## Ground rules

1. **Every claim of "implemented" must be backed by real, runnable code
   and a real test.** If a capability isn't implemented, say so explicitly
   in the skill's "What is NOT implemented" section rather than describing
   it as if it were — see `skills/bionemo-agent-toolkit/SKILL.md` and
   `skills/quantum/references/model_documentation.md` for the pattern this
   repo follows: implemented vs. planned/not-implemented is always
   explicit, and known limitations (even inconvenient ones) are documented
   rather than hidden.
2. **Cite your sources for any external API, model, or scientific claim.**
   When wrapping a third-party API (an NVIDIA NIM, an MCP server, a
   published algorithm), link the exact documentation page or paper you
   verified the details against. If you couldn't verify something,
   say so and hedge accordingly rather than guessing a plausible-looking
   schema.
3. **Don't duplicate an existing official/community bridge.** If a tool
   already has its own MCP server (e.g. unity-mcp for Unity, UnrealClaude
   for Unreal, `alphafold3_mcp` for AlphaFold3), document how to connect
   to and use it rather than reimplementing its functionality here.
4. **Every new skill needs, at minimum:** `SKILL.md` (frontmatter +
   scope/limits/usage), `README.md` (quick-start usage example), and if it
   has runnable code, real tests you've actually run (not just described).
   If your skill references `evals/eval_set.json`, `references/*.md`, or
   `scripts/*.py`, make sure those files actually exist before opening a
   PR — a broken reference is treated as a bug, not a placeholder.
5. **Run existing tests before submitting.** e.g. for the quantum skill:
   `cd skills/quantum/scripts && python3 test_cvar_vqe.py`; for
   bionemo-agent-toolkit: `cd skills/bionemo-agent-toolkit/scripts &&
   python3 smoke_test.py`.

## Reporting a broken reference or inaccurate claim

Open an issue with the file path and what's wrong. Given this repo's own
rule above, these are treated as real bugs and prioritized accordingly —
please don't hesitate to report one even if it seems minor.

## License

By contributing, you agree your contribution is licensed under this
repository's MIT license (see `LICENSE`).
