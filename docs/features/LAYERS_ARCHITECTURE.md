# Layers Architecture - ForgeWorks Frontend

> **Status:** Concept / Discovery Phase
> **Component:** Frontend Dashboard (Next.js)
> **Priority:** Planned Feature

---

## Executive Summary

A revolutionary front-end architecture concept for **ForgeWorks** that replaces traditional **tab-based navigation** with **layer-based composition** - similar to how Figma handles design layers. This approach solves the screen real-estate crisis that DevOps/Platform engineers face daily while also delivering significant performance benefits.

### ForgeWorks Integration

ForgeWorks currently has "Frontend dashboard" as a **planned** component. This Layers concept defines how that dashboard should be built:

| ForgeWorks Component | Layer Representation |
|---------------------|---------------------|
| Service Catalog | Services Layer - health, ownership, metrics |
| Golden Path Templates | Templates Layer - available blueprints |
| ML Recommender | Recommendations Layer - suggestions overlay |
| Anomaly Detection | Anomalies Layer - alerts, patterns |
| External Integrations | Pipeline Layer (GitHub), Deployment Layer (ArgoCD) |

The "Glue" concept aligns perfectly with ForgeWorks' **API Glue Layer** architecture.

---

## The Problem Statement

### Current Reality for Platform Engineers

**Physical Setup:**
- Engineers typically use 2-4 monitors
- Each monitor has 5-15+ browser tabs open
- Total context: 20-50+ simultaneous views

**What They're Juggling:**
- CI/CD pipelines (GitLab, GitHub Actions, Jenkins)
- Cloud consoles (AWS, GCP, Azure)
- Infrastructure state (Terraform, CloudFormation)
- Container orchestration (Kubernetes dashboards, ArgoCD)
- Observability (Grafana, Prometheus, Datadog)
- Logs (CloudWatch, ELK, Loki)
- Documentation (Confluence, Notion, internal wikis)
- Communication (Slack, Teams)
- Code editors (VSCode, IDE)

**The Pain:**
```
Tab Hell = Context Switching Hell
         = Lost Productivity
         = Missed Connections
         = Cognitive Overload
```

Even with 4 monitors, engineers constantly ask:
- "Which tab had that pipeline?"
- "Where did I see that error?"
- "What was the ARN for that resource?"

**Key Insight:** The problem isn't screen count - it's the **mental model**. Tabs are **flat and disconnected**. Infrastructure is **hierarchical and connected**.

---

## The Solution: Layers Instead of Tabs

### Core Concept

**Tabs = Horizontal context switching** (lost, buried, forgotten)

**Layers = Vertical composition** (stacked, visible, relational)

### The Figma Analogy

In Figma, designers work with layers:
```
[Layer Panel]
 👁 Background
 👁 Navigation
 👁 Hero Section
    Components (hidden)
 👁 Footer
```

They can:
- Toggle visibility per layer
- See multiple layers simultaneously
- Understand relationships spatially
- Group and organize logically
- Lock layers while working on others

### Applied to ForgeWorks

```
[ForgeWorks - Layer Panel]
 👁 [Layer] Services           ← Service Catalog health, ownership
 👁 [Layer] Templates          ← Golden Path blueprints
 👁 [Layer] Recommendations    ← ML suggestions overlay
    [Layer] Anomalies          ← hidden, but available
 👁 [Layer] Pipeline           ← GitHub Actions, deployments
 👁 [Layer] Metrics            ← Service performance data
    [Layer] Cost Analysis      ← hidden
```

**Key Differentiator:** Layers don't just DISPLAY data - they VISUALIZE what already exists and surface the **raw values (the glue)** that connect everything.

---

## The "Glue" Concept - Raw Values That Matter

### What is "The Glue"?

The glue represents the **connection points** between layers - the identifiers, references, and values that link disparate systems together.

### Examples of Glue Values in ForgeWorks

| Source Layer | Glue Value | Connected To |
|--------------|------------|--------------|
| Services | `service_id` | Templates, Metrics, Anomalies |
| Pipeline | `commit_sha` | Services, Deployments |
| Templates | `template_id` | Services, Recommendations |
| Anomalies | `service_id`, `timestamp` | Services, Metrics |
| Deployment | `release_version` | Pipeline, Services |

### How Glue Works in Layers

```
┌─────────────────────────────────────────────────────┐
│ [Services Layer]                                    │
│   payment-api → healthy → team: payments            │
│        │                                            │
│ ───────┼─────────────────────────────────────────── │
│ [Pipeline Layer]                                    │
│   Build #1234 → commit: abc123 → image: v2.1.0     │
│                    │                                │
│ ───────────────────┼─────────────────────────────── │
│ [Anomalies Layer]                                   │
│   ⚠️ High deploy frequency (5 deploys today)        │
│             └──────────────────────────────────────→│
└─────────────────────────────────────────────────────┘
```

**The glue (service_id, commit SHA) flows through layers, creating visible connections.**

---

## Performance Architecture

### Why Layers Outperform Tabs

| Aspect | Tabs (Current) | Layers (Proposed) |
|--------|----------------|-------------------|
| **Memory** | All tabs loaded | Only visible layers rendered |
| **CPU** | Each tab = isolated process | Shared rendering context |
| **Network** | 40 tabs = 40 separate API calls | Shared data bus, fetch once |
| **Updates** | Full page refresh per tab | Incremental layer updates |
| **State** | No relationship awareness | Cross-layer state sharing |
| **Startup** | All tabs initialize | Lazy load on visibility |

### Performance Strategies

#### 1. Lazy Rendering
```
Hidden Layer = Zero GPU/CPU cost
Visible Layer = Active rendering
Collapsed Layer = Minimal memory footprint
```

#### 2. Shared Data Context
```javascript
// Instead of each "tab" fetching independently:
Services Tab → fetch(/api/v1/services)
Anomalies Tab → fetch(/api/v1/services)  // duplicate!

// Layers share a data bus:
DataBus.fetch('services')
  → Services Layer: uses service data
  → Anomalies Layer: uses same data (cached)
  → Templates Layer: subscribes to same context
```

#### 3. Selective Subscriptions
```
WebSocket connections only for VISIBLE layers
Hidden layer? → Unsubscribe (save bandwidth)
Layer becomes visible? → Re-subscribe
```

#### 4. Layer-Level Caching
```
Each layer manages its own cache lifecycle:
- Services Layer: 30s cache (fast-moving health checks)
- Templates Layer: 5min cache (slower changes)
- Anomalies Layer: 1min cache (near real-time)
```

#### 5. Parallel Hydration
```
Layers load CONCURRENTLY, not sequentially
Services loading...    ████████░░ 80%
Templates loading...   ██████████ 100% ✓
Anomalies loading...   ██░░░░░░░░ 20%
```

---

## Competitive Analysis

### What Exists Today

| Product | Approach | Limitation |
|---------|----------|------------|
| **Backstage** | Portal / Catalog | Tab-based, no visual composition |
| **Port** | Developer Portal | Widget-based, limited relationships |
| **Grafana** | Dashboards | Panel-based, not layered |
| **Lens** | K8s IDE | Single-domain focus |
| **VS Code** | Editor + Extensions | Still tab-based |

### What's Missing

**NO PRODUCT offers:**
- True layer-based composition
- Cross-domain relationship visualization
- The "glue" concept surfaced
- Figma-like spatial organization for infrastructure

**This differentiates ForgeWorks from all existing IDPs.**

---

## Use Cases

### Use Case 1: Service Health Investigation
```
Visible Layers:
 👁 [Services] → See degraded service
 👁 [Anomalies] → Check for patterns
 👁 [Pipeline] → Recent deployments?
 👁 [Metrics] → Performance data

Glue: service_id, deployment_id
```

### Use Case 2: New Service Creation
```
Visible Layers:
 👁 [Templates] → Browse Golden Paths
 👁 [Recommendations] → ML suggestions
 👁 [Services] → See similar services

Glue: template_id, workload_type
```

### Use Case 3: Anomaly Triage
```
Visible Layers:
 👁 [Anomalies] → List of issues
 👁 [Services] → Affected services
 👁 [Pipeline] → Correlated deployments

Glue: service_id, timestamp, deployment_id
```

---

## Technical Implementation

### Frontend Stack (Aligned with ForgeWorks)

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Framework** | Next.js 14+ | Already in ForgeWorks stack |
| **State** | Zustand | Lightweight, cross-layer state |
| **Styling** | Tailwind CSS | Already in ForgeWorks stack |
| **Data Fetching** | React Query | Caching + deduplication |
| **Real-time** | WebSocket | Live updates per layer |

### Data Architecture

```typescript
interface Layer {
  id: string;
  name: string;
  type: 'services' | 'templates' | 'anomalies' | 'pipeline' | 'metrics';
  visible: boolean;
  collapsed: boolean;
  zIndex: number;
  apiEndpoint: string;  // ForgeWorks API binding
  glueKeys: string[];   // What identifiers this layer exposes
  subscriptions: string[];  // What glue values it consumes
}

interface GlueBus {
  values: Map<string, any>;  // Shared identifiers
  subscribe: (key: string, callback: Function) => void;
  publish: (key: string, value: any) => void;
}
```

### Location in Codebase
```
forge-works/
└── src/
    └── frontend/
        └── components/
            └── layers/           # Layers Architecture
                ├── LayerPanel.tsx
                ├── LayerRenderer.tsx
                ├── GlueBus.ts
                └── layers/
                    ├── ServicesLayer.tsx
                    ├── TemplatesLayer.tsx
                    ├── AnomaliesLayer.tsx
                    ├── PipelineLayer.tsx
                    └── MetricsLayer.tsx
```

### Integration Points

| ForgeWorks API | Layer Consumer |
|----------------|----------------|
| `GET /api/v1/services` | Services Layer |
| `GET /api/v1/services/stats` | Services Layer (metrics) |
| `GET /api/v1/templates` | Templates Layer |
| `POST /api/v1/templates/recommend` | Recommendations Layer |
| Adapters (GitHub, ArgoCD) | Pipeline, Deployment Layers |

---

## Implementation Roadmap

### Phase 1: MVP (Core Layers)

| Feature | Priority | Effort |
|---------|----------|--------|
| Layer panel UI | P0 | Medium |
| Services Layer | P0 | Medium |
| Templates Layer | P0 | Medium |
| Anomalies Layer | P0 | Medium |
| Basic Glue Bus | P0 | Medium |
| Visibility toggle | P0 | Low |
| Layer persistence | P1 | Low |

### Phase 2: Enhanced Interactions

| Feature | Priority | Effort |
|---------|----------|--------|
| Pipeline Layer (GitHub adapter) | P1 | High |
| Metrics Layer | P1 | Medium |
| Cross-layer highlighting | P1 | Medium |
| Layer collapse/expand | P1 | Low |
| Keyboard shortcuts | P2 | Low |

### Phase 3: Advanced Features

| Feature | Priority | Effort |
|---------|----------|--------|
| AI-Assisted Layers ("Show relevant layers") | P2 | High |
| Custom user layers | P2 | High |
| Layer templates/presets | P2 | Medium |
| Collaborative shared layouts | P3 | High |
| Layer timeline/recordings | P3 | High |

---

## Summary

### What Makes This Unique

1. **Paradigm Shift:** Tabs → Layers (no other IDP does this)
2. **The Glue:** Surfacing connection points between ForgeWorks components
3. **Performance:** Lazy rendering, shared data, selective updates
4. **ForgeWorks Native:** Built on existing API Glue Layer
5. **Platform-First:** Designed for DevOps/Platform workflows

### Key Innovation Points

| Innovation | Value |
|------------|-------|
| Layer composition | Reduces cognitive load by 50%+ |
| Glue visualization | Makes service relationships explicit |
| Lazy rendering | 10x memory efficiency potential |
| API integration | Leverages existing ForgeWorks backend |
| Spatial memory | Users remember positions, not tabs |

---

## Conclusion

The "Layers" concept addresses a real, unsolved problem in the DevOps/Platform engineering space. By reimagining how engineers interact with ForgeWorks - moving from disconnected tabs to composed layers with visible connections - we can significantly reduce cognitive load while improving performance.

This is not an incremental improvement. This is a **paradigm shift** for the ForgeWorks frontend.

**No existing IDP offers this visualization approach.** This differentiates ForgeWorks from Backstage, Port, and other developer portals.

---

*Document Version: 1.0*
*Last Updated: January 2025*
*Status: Concept Ready for Frontend Implementation*
