# qFoldIT Protein Design MCP Platform Integration

`Protein-Design-MCP` is a scientific capability provider in the qFoldIT Scientific Agent Mesh.

## Runtime boundary

```text
Agent / Mission
      -> MCP capability
      -> Protein design / prediction / scoring backend
      -> Scientific artifact
      -> Evidence / provenance
      -> qFoldIT Mission / CAMEO
```

The MCP server is a scientific capability surface. It does not own mission lifecycle, runtime world state or commercial reward policy.

## Contract family

Scientific outputs should be normalized into the qFoldIT evidence and scientific-state contracts where they cross the platform boundary:

- `qfoldit.scientific-state/1.0`
- `qfoldit.submission/1.0`
- `qfoldit.evidence/1.0`
- `qfoldit.event/1.0`

Engine/world export should target `qfoldit.uag/1.0` where supported.

## Capability classes

- generative protein design;
- structure prediction;
- structure scoring;
- molecular dynamics / relaxation;
- sequence design;
- quantum-assisted peptide folding;
- scientific artifact export.

## Provenance

This repository contains a mixed-license boundary: upstream MCP/server components retain their upstream license, while qFoldIT-authored `claude-skills/` material is separately licensed. Valuation and ownership records must preserve that distinction.

## Scientific authority

Tool execution produces scientific evidence candidates. Final mission acceptance remains governed by the selected qFoldIT scientific validation service and mission policy.
