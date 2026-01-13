# Architecture Diagrams

This directory contains architecture diagrams for the ForgeWorks platform.

## Available Diagrams

All diagrams are in **[SYSTEM_DIAGRAMS.md](./SYSTEM_DIAGRAMS.md)** using Mermaid format.

| # | Diagram | C4 Level | Status |
|---|---------|----------|--------|
| 1 | System Context | L1 | Complete |
| 2 | Container Diagram | L2 | Complete |
| 3 | Component - Backend | L3 | Complete |
| 4 | Component - Frontend | L3 | Complete |
| 5 | Data Flow Diagram | - | Complete |
| 6 | Deployment Diagram | - | Complete |
| 7 | Sequence Diagrams | - | Complete |
| 8 | Entity Relationship | - | Complete |
| 9 | Layer Architecture | - | Complete |
| 10 | Adapter Pattern | - | Complete |

## Diagram Standards

- Use [Mermaid](https://mermaid.js.org/) for version-controlled diagrams
- Follow [C4 Model](https://c4model.com/) conventions for architecture diagrams
- Include diagram source in commit for easy updates

## Viewing Diagrams

### In GitHub

GitHub natively renders Mermaid diagrams in Markdown files. Simply open `SYSTEM_DIAGRAMS.md` in GitHub.

### In VS Code

Install the [Markdown Preview Mermaid Support](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid) extension.

### Mermaid Live Editor

For editing and PNG export:
1. Go to [mermaid.live](https://mermaid.live/)
2. Copy the diagram code from SYSTEM_DIAGRAMS.md
3. Edit visually and export as PNG

## Tools

- **Mermaid Live Editor**: https://mermaid.live/
- **Draw.io**: https://app.diagrams.net/
- **Excalidraw**: https://excalidraw.com/

## Related Documentation

- [Architecture Overview](../architecture.md)
- [API Documentation](../API.md)
- [Layers Architecture](../features/LAYERS_ARCHITECTURE.md)
