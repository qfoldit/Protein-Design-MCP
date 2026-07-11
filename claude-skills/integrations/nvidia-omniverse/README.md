# qFoldIT + NVIDIA Omniverse (index page)

This is a short architecture-index page, not the authoritative
documentation. For the real, maintained integration details — the
official NVIDIA-Omniverse/kit-usd-agents MCP servers, exactly which tools
they expose, and the important distinction that these are USD/Kit
API-assistant tools rather than a live scene-control bridge — see
[`skills/openusd-architect/SKILL.md`](../../skills/openusd-architect/SKILL.md).

## Architecture (unchanged, accurate)

```
Claude / MCP Client
        |
        +-- qFoldIT MCP
        |      |
        |      +-- Digital Twin
        |      +-- Scene Plan
        |
        +-- NVIDIA Omniverse Kit/USD Agents (kit-usd-agents)
               |
               +-- USD API/doc lookup tools
               +-- (live scene editing happens via Chat USD, inside Kit
                    itself -- not exposed over MCP to external clients)
```

qFoldIT remains the scientific data layer (molecular digital twin JSON,
scene plans); the Omniverse MCP/agent implementation is maintained by
NVIDIA and installed separately per `skills/openusd-architect/SKILL.md`.
