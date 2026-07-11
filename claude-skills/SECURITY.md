# Security Policy

## Reporting a Vulnerability

If you find a security issue in this repository (e.g. in the smoke-test
scripts, HTTP clients in `skills/bionemo-agent-toolkit/scripts/`, or
anywhere else code executes), please report it privately rather than
opening a public issue:

- Open a [GitHub Security Advisory](https://github.com/qfoldit/skills/security/advisories/new)
  for this repository, or
- Email the contact listed in this repository's `README.md`.

Please include:
- A description of the issue and its potential impact.
- Steps to reproduce, if possible.
- Which skill(s)/file(s) are affected.

## Scope notes

- Several skills in this repository (`bionemo-agent-toolkit`, `nanover`)
  make outbound network requests to services the user runs themselves
  (self-hosted NVIDIA NIM containers, a NanoVer server) or to third-party
  cloud APIs the user has explicitly configured credentials for. None of
  this repository's code phones home to a qFoldIT-controlled server, and
  no API keys or credentials are bundled, logged, or transmitted anywhere
  other than the documented third-party endpoint for that specific call.
- This repository does not currently have a formal security audit. Treat
  all `scripts/*.py` as you would any third-party client library you're
  integrating: review before running with real credentials against
  production infrastructure.

## Supported Versions

This project does not yet maintain multiple concurrent release branches;
security fixes are made against the latest `main`.
