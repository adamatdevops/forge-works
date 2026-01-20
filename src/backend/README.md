# ForgeWorks Backend

**Internal Developer Platform - Golden Path Orchestrator + "The Glue"**

ForgeWorks serves as "The Glue" between various DevOps tools—not replacing them, but bridging the gaps where they can't communicate directly. External tools (GitHub, Kubernetes, Terraform, etc.) are "customers" that ForgeWorks serves through Forge Adapters.

## Core Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      ForgeWorks Core ("The Glue")                   │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │              Python Casting/Converting Layer                │  │
│   └─────────────────────────────────────────────────────────────┘  │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                 Shared State (Smart Log)                    │  │
│   └─────────────────────────────────────────────────────────────┘  │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    ML Analysis Layer                        │  │
│   └─────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │  Forge   │    │  Forge   │    │  Forge   │    ...∞
        │ Adapter  │    │ Adapter  │    │ Adapter  │  potential
        └────┬─────┘    └────┬─────┘    └────┬─────┘  customers
             ▼               ▼               ▼
        [GitHub]        [K8s/EKS]      [Terraform]
```

## Key Concepts

- **Shared Data**: Common identifiers (commit SHA, workflow ID, resource ARN) across systems
- **Shared State**: Unified view of multi-tool workflows in a Smart Log
- **Shared Language**: Normalized events for ML analysis regardless of source tool

## Documentation

- [Architecture Overview](../../docs/architecture.md)
- [Vision & Glue Architecture](../../planning/VISION.md)
- [ADR-007: Glue Architecture](../../adr/007-glue-architecture.md)
