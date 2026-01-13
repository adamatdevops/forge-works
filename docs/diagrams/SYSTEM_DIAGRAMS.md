# ForgeWorks Architecture Diagrams

Comprehensive architecture diagrams following [C4 Model](https://c4model.com/) conventions using Mermaid.

---

## 1. System Context Diagram (C4 Level 1)

Shows ForgeWorks and its relationships with external systems and users.

```mermaid
flowchart TB
    subgraph users["Users"]
        PE[/"Platform Engineer"/]
        DEV[/"Developer"/]
        SRE[/"SRE/DevOps"/]
    end

    FW[["ForgeWorks<br/>Internal Developer Platform"]]

    subgraph external["External Systems"]
        GH["GitHub<br/>Source Control & CI"]
        ARGO["ArgoCD<br/>GitOps Deployments"]
        K8S["Kubernetes<br/>Container Orchestration"]
        SLACK["Slack<br/>Notifications"]
        PROM["Prometheus<br/>Metrics"]
    end

    PE -->|"Manages platform,<br/>templates, teams"| FW
    DEV -->|"Creates services,<br/>views health"| FW
    SRE -->|"Monitors anomalies,<br/>views metrics"| FW

    FW -->|"Reads repos,<br/>workflow status"| GH
    FW -->|"Reads deployments,<br/>sync status"| ARGO
    FW -->|"Future:<br/>direct k8s access"| K8S
    FW -->|"Sends alerts"| SLACK
    FW -->|"Reads metrics"| PROM

    style FW fill:#1168bd,stroke:#0b4884,color:#fff
    style PE fill:#08427b,stroke:#052e56,color:#fff
    style DEV fill:#08427b,stroke:#052e56,color:#fff
    style SRE fill:#08427b,stroke:#052e56,color:#fff
```

---

## 2. Container Diagram (C4 Level 2)

Shows the high-level technical architecture and main containers.

```mermaid
flowchart TB
    subgraph users["Users"]
        USER[/"Platform Engineer<br/>Developer<br/>SRE"/]
    end

    subgraph fw["ForgeWorks Platform"]
        subgraph frontend["Frontend Container"]
            NEXT["Next.js 14<br/>React Dashboard"]
        end

        subgraph backend["Backend Container"]
            API["FastAPI<br/>REST API"]
        end

        subgraph data["Data Layer"]
            PG[("PostgreSQL<br/>Primary Database")]
            REDIS[("Redis<br/>Cache (Planned)")]
        end
    end

    subgraph adapters["External Adapters"]
        GH_ADAPT["GitHub Adapter"]
        ARGO_ADAPT["ArgoCD Adapter"]
    end

    subgraph external["External Systems"]
        GH["GitHub API"]
        ARGO["ArgoCD API"]
    end

    USER -->|"HTTPS"| NEXT
    NEXT -->|"REST API<br/>/api/v1/*"| API
    API -->|"SQLAlchemy<br/>Async"| PG
    API -.->|"Future"| REDIS
    API --> GH_ADAPT
    API --> ARGO_ADAPT
    GH_ADAPT -->|"REST"| GH
    ARGO_ADAPT -->|"REST"| ARGO

    style NEXT fill:#438dd5,stroke:#2e6295,color:#fff
    style API fill:#438dd5,stroke:#2e6295,color:#fff
    style PG fill:#438dd5,stroke:#2e6295,color:#fff
    style REDIS fill:#999,stroke:#666,color:#fff
```

---

## 3. Component Diagram - Backend (C4 Level 3)

Detailed view of backend components.

```mermaid
flowchart TB
    subgraph api["API Layer"]
        HEALTH["/health"]
        SERVICES["/api/v1/services"]
        TEMPLATES["/api/v1/templates"]
        ANOMALIES["/api/v1/anomalies"]
        METRICS["/api/v1/metrics"]
    end

    subgraph business["Business Logic Layer"]
        SVC_CRUD["ServiceCRUD"]
        TPL_CRUD["TemplateCRUD"]
        ANO_CRUD["AnomalyCRUD"]
        RECOMMEND["ML Recommender"]
        METRICS_AGG["Metrics Aggregator"]
    end

    subgraph schemas["Validation Layer"]
        SVC_SCHEMA["ServiceSchema"]
        TPL_SCHEMA["TemplateSchema"]
        ANO_SCHEMA["AnomalySchema"]
        METRICS_SCHEMA["MetricsSchema"]
    end

    subgraph adapters["Adapter Layer"]
        GH_LIVE["GitHubLiveAdapter"]
        GH_MOCK["GitHubMockAdapter"]
        ARGO_LIVE["ArgoCDLiveAdapter"]
        ARGO_MOCK["ArgoCDMockAdapter"]
    end

    subgraph data["Data Access Layer"]
        MODELS["SQLAlchemy Models"]
        DB[("PostgreSQL")]
    end

    SERVICES --> SVC_CRUD
    TEMPLATES --> TPL_CRUD
    TEMPLATES --> RECOMMEND
    ANOMALIES --> ANO_CRUD
    METRICS --> METRICS_AGG

    SVC_CRUD --> SVC_SCHEMA
    TPL_CRUD --> TPL_SCHEMA
    ANO_CRUD --> ANO_SCHEMA
    METRICS_AGG --> METRICS_SCHEMA

    SVC_CRUD --> GH_LIVE
    SVC_CRUD --> ARGO_LIVE

    SVC_CRUD --> MODELS
    TPL_CRUD --> MODELS
    ANO_CRUD --> MODELS
    METRICS_AGG --> MODELS

    MODELS --> DB

    style api fill:#85c1e9,stroke:#5499c7
    style business fill:#82e0aa,stroke:#58d68d
    style adapters fill:#f8c471,stroke:#f39c12
    style data fill:#bb8fce,stroke:#8e44ad
```

---

## 4. Component Diagram - Frontend

Detailed view of frontend layer architecture.

```mermaid
flowchart TB
    subgraph layout["App Layout"]
        SHELL["AppShell"]
        NAV["Navigation"]
        HEADER["Header"]
    end

    subgraph layers["Layer System"]
        PANEL["LayerPanel<br/>Toggle visibility"]
        RENDERER["LayerRenderer<br/>Compose layers"]

        subgraph layerComponents["Layer Components"]
            SVC_LAYER["ServicesLayer"]
            TPL_LAYER["TemplatesLayer"]
            ANO_LAYER["AnomaliesLayer"]
            PIPE_LAYER["PipelineLayer"]
            METRICS_LAYER["MetricsLayer"]
        end
    end

    subgraph state["State Management"]
        ZUSTAND["Zustand Store"]
        GLUE["GlueBus<br/>Cross-layer events"]
    end

    subgraph data["Data Fetching"]
        RQ["TanStack Query"]
        API_CLIENT["API Client"]
    end

    subgraph ui["UI Components"]
        SHADCN["shadcn/ui"]
        CHARTS["Recharts"]
    end

    SHELL --> NAV
    SHELL --> HEADER
    SHELL --> PANEL
    SHELL --> RENDERER

    PANEL --> ZUSTAND
    RENDERER --> layerComponents

    layerComponents --> RQ
    layerComponents --> GLUE
    RQ --> API_CLIENT

    layerComponents --> SHADCN
    METRICS_LAYER --> CHARTS

    ZUSTAND --> GLUE

    style layers fill:#a9dfbf,stroke:#27ae60
    style state fill:#f9e79f,stroke:#f1c40f
    style data fill:#aed6f1,stroke:#3498db
```

---

## 5. Data Flow Diagram

Shows how data flows through the system.

```mermaid
flowchart LR
    subgraph sources["Data Sources"]
        GH["GitHub"]
        ARGO["ArgoCD"]
        DB[("PostgreSQL")]
    end

    subgraph backend["Backend Processing"]
        ADAPTERS["Adapters<br/>(Mock/Live)"]
        CRUD["CRUD Layer"]
        AGG["Aggregation"]
    end

    subgraph api["API Endpoints"]
        REST["REST API<br/>/api/v1/*"]
    end

    subgraph frontend["Frontend"]
        QUERY["TanStack Query<br/>(Cache + Dedup)"]
        STORE["Zustand Store"]
        LAYERS["Layer Components"]
        GLUE["GlueBus"]
    end

    subgraph output["User Interface"]
        UI["Dashboard UI"]
    end

    GH -->|"Repository info<br/>Workflow runs"| ADAPTERS
    ARGO -->|"App status<br/>Sync state"| ADAPTERS
    DB -->|"Services<br/>Templates<br/>Anomalies"| CRUD

    ADAPTERS --> CRUD
    CRUD --> AGG
    AGG --> REST

    REST -->|"JSON Responses"| QUERY
    QUERY --> STORE
    STORE --> LAYERS
    LAYERS --> GLUE
    GLUE -->|"Cross-layer<br/>events"| LAYERS

    LAYERS --> UI
```

---

## 6. Deployment Diagram

Shows the deployment architecture for development and production.

### Local Development

```mermaid
flowchart TB
    subgraph docker["Docker Compose"]
        subgraph fe["Frontend"]
            NEXT["Next.js<br/>:3000"]
        end

        subgraph be["Backend"]
            FASTAPI["FastAPI<br/>:8000"]
        end

        subgraph db["Database"]
            PG["PostgreSQL<br/>:5432"]
        end
    end

    DEV[/"Developer"/] -->|"localhost:3000"| NEXT
    NEXT -->|"localhost:8000/api"| FASTAPI
    FASTAPI --> PG

    style docker fill:#e8f6f3,stroke:#1abc9c
```

### Production (Target)

```mermaid
flowchart TB
    subgraph internet["Internet"]
        USERS[/"Users"/]
    end

    subgraph k8s["Kubernetes Cluster"]
        INGRESS["Ingress Controller<br/>(nginx)"]

        subgraph frontend["Frontend Deployment"]
            FE1["Next.js Pod 1"]
            FE2["Next.js Pod 2"]
        end

        subgraph backend["Backend Deployment"]
            BE1["FastAPI Pod 1"]
            BE2["FastAPI Pod 2"]
            BE3["FastAPI Pod 3"]
        end

        subgraph data["Data Layer"]
            PG[("PostgreSQL<br/>StatefulSet")]
            REDIS[("Redis<br/>StatefulSet")]
        end

        subgraph gitops["GitOps"]
            ARGO["ArgoCD"]
        end
    end

    subgraph external["External"]
        GH["GitHub"]
    end

    USERS -->|"HTTPS"| INGRESS
    INGRESS -->|"/app/*"| FE1 & FE2
    INGRESS -->|"/api/*"| BE1 & BE2 & BE3

    BE1 & BE2 & BE3 --> PG
    BE1 & BE2 & BE3 --> REDIS

    ARGO -->|"Sync"| k8s
    GH -->|"Webhook"| ARGO

    style k8s fill:#fef9e7,stroke:#f39c12
    style data fill:#fadbd8,stroke:#e74c3c
```

---

## 7. Sequence Diagrams

### Service Creation Flow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as FastAPI
    participant DB as PostgreSQL
    participant GH as GitHub Adapter

    U->>FE: Click "Create Service"
    FE->>FE: Open creation modal
    U->>FE: Fill form & submit
    FE->>API: POST /api/v1/services

    API->>API: Validate request (Pydantic)
    API->>API: Generate slug from name
    API->>DB: Check team exists
    DB-->>API: Team found
    API->>DB: Check template exists
    DB-->>API: Template found

    API->>GH: Verify repository access
    GH-->>API: Repository info

    API->>DB: INSERT service
    DB-->>API: Service created

    API-->>FE: 201 ServiceResponse
    FE->>FE: Invalidate cache
    FE->>FE: Update UI
    FE-->>U: Show success toast
```

### Anomaly Detection Flow

```mermaid
sequenceDiagram
    participant CRON as Scheduler
    participant API as FastAPI
    participant DB as PostgreSQL
    participant GH as GitHub Adapter
    participant WS as WebSocket
    participant FE as Frontend

    CRON->>API: Trigger anomaly scan

    loop For each service
        API->>DB: Get service stats
        API->>GH: Get deploy frequency
        GH-->>API: Deploy data

        API->>API: Apply detection rules

        alt Anomaly detected
            API->>DB: INSERT anomaly
            DB-->>API: Anomaly created
            API->>WS: Broadcast anomaly event
            WS->>FE: Push notification
            FE->>FE: Update Anomalies Layer
        end
    end

    API-->>CRON: Scan complete
```

### Template Recommendation Flow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as FastAPI
    participant ML as ML Recommender
    participant DB as PostgreSQL

    U->>FE: Select workload type & language
    FE->>API: GET /api/v1/templates/recommend?workload=api&lang=python

    API->>DB: Query active templates
    DB-->>API: Template list

    API->>ML: Score templates

    loop For each template
        ML->>ML: Calculate workload match (40pts)
        ML->>ML: Calculate language match (30pts)
        ML->>ML: Calculate capability overlap (20pts)
        ML->>ML: Calculate ideal_for match (10pts)
    end

    ML-->>API: Scored templates
    API->>API: Sort by score DESC
    API-->>FE: RecommendationResponse

    FE->>FE: Display ranked templates
    FE-->>U: Show recommendations
```

---

## 8. Entity Relationship Diagram

```mermaid
erDiagram
    TEAM ||--o{ SERVICE : owns
    TEMPLATE ||--o{ SERVICE : scaffolds
    SERVICE ||--o{ ANOMALY : has

    TEAM {
        uuid id PK
        string name
        string slug UK
        string email
        string slack_channel
        timestamp created_at
    }

    SERVICE {
        uuid id PK
        string name
        string slug UK
        string description
        uuid team_id FK
        uuid template_id FK
        enum status
        enum tier
        string repository_url
        string repository_branch
        string namespace
        string argocd_app_name
        int deploys_today
        int rollbacks_this_week
        timestamp last_deploy_at
        array tags
        json metadata
        timestamp created_at
        timestamp updated_at
    }

    TEMPLATE {
        uuid id PK
        string name
        string slug UK
        string description
        enum workload_type
        string language
        string framework
        string repository_url
        string documentation_url
        boolean is_active
        int usage_count
        timestamp last_used_at
        timestamp created_at
    }

    ANOMALY {
        uuid id PK
        uuid service_id FK
        enum type
        enum severity
        string title
        string description
        string suggestion
        string detected_value
        string expected_value
        string detection_rule
        json context
        boolean is_active
        boolean is_acknowledged
        string acknowledged_by
        timestamp acknowledged_at
        boolean is_resolved
        timestamp resolved_at
        string resolution_note
        timestamp detected_at
        timestamp created_at
    }
```

---

## 9. Layer Architecture Diagram

ForgeWorks unique layer-based UI composition.

```mermaid
flowchart TB
    subgraph panel["Layer Panel (Left Sidebar)"]
        direction TB
        TOGGLE["Toggle Controls"]
        L1["Services Layer"]
        L2["Templates Layer"]
        L3["Anomalies Layer"]
        L4["Pipeline Layer"]
        L5["Metrics Layer"]
    end

    subgraph renderer["Layer Renderer (Main Area)"]
        direction TB

        subgraph visible["Visible Layers (Stacked)"]
            SVC_VIS["Services<br/>Health, Status, Actions"]
            TPL_VIS["Templates<br/>Blueprints, Usage"]
            METRICS_VIS["Metrics<br/>DORA, Health Score"]
        end

        subgraph hidden["Hidden Layers"]
            ANO_HID["Anomalies (hidden)"]
            PIPE_HID["Pipeline (hidden)"]
        end
    end

    subgraph glue["GlueBus (Event System)"]
        direction LR
        SVC_ID["service_id"]
        TPL_ID["template_id"]
        TEAM_ID["team_id"]
    end

    TOGGLE -->|"visibility toggle"| visible
    TOGGLE -->|"visibility toggle"| hidden

    SVC_VIS -->|"publish"| SVC_ID
    SVC_ID -->|"subscribe"| METRICS_VIS
    SVC_ID -->|"subscribe"| ANO_HID

    TPL_VIS -->|"publish"| TPL_ID
    TPL_ID -->|"subscribe"| SVC_VIS

    style visible fill:#d5f5e3,stroke:#27ae60
    style hidden fill:#fadbd8,stroke:#e74c3c
    style glue fill:#fef9e7,stroke:#f1c40f
```

---

## 10. Adapter Pattern Diagram

Shows the Mock/Live adapter switching pattern.

```mermaid
flowchart TB
    subgraph config["Configuration"]
        ENV["Environment Variables<br/>GITHUB_MOCK_MODE=true/false<br/>ARGOCD_MOCK_MODE=true/false"]
    end

    subgraph factory["Adapter Factory"]
        FACTORY["get_adapter()"]
    end

    subgraph adapters["Adapter Implementations"]
        subgraph github["GitHub Adapters"]
            GH_BASE["GitHubAdapter (Base)"]
            GH_MOCK["GitHubMockAdapter"]
            GH_LIVE["GitHubLiveAdapter"]
        end

        subgraph argocd["ArgoCD Adapters"]
            ARGO_BASE["ArgoCDAdapter (Base)"]
            ARGO_MOCK["ArgoCDMockAdapter"]
            ARGO_LIVE["ArgoCDLiveAdapter"]
        end
    end

    subgraph consumers["Consumers"]
        SVC_CRUD["ServiceCRUD"]
        METRICS["MetricsAggregator"]
    end

    ENV --> FACTORY
    FACTORY -->|"mock=true"| GH_MOCK
    FACTORY -->|"mock=false"| GH_LIVE
    FACTORY -->|"mock=true"| ARGO_MOCK
    FACTORY -->|"mock=false"| ARGO_LIVE

    GH_MOCK --> GH_BASE
    GH_LIVE --> GH_BASE
    ARGO_MOCK --> ARGO_BASE
    ARGO_LIVE --> ARGO_BASE

    GH_BASE --> SVC_CRUD
    ARGO_BASE --> SVC_CRUD
    GH_BASE --> METRICS
    ARGO_BASE --> METRICS

    style factory fill:#aed6f1,stroke:#3498db
    style GH_MOCK fill:#fef9e7,stroke:#f39c12
    style ARGO_MOCK fill:#fef9e7,stroke:#f39c12
    style GH_LIVE fill:#d5f5e3,stroke:#27ae60
    style ARGO_LIVE fill:#d5f5e3,stroke:#27ae60
```

---

## Diagram Index

| # | Diagram | C4 Level | Description |
|---|---------|----------|-------------|
| 1 | System Context | L1 | High-level system and external actors |
| 2 | Container | L2 | Technical containers (Frontend, Backend, DB) |
| 3 | Component - Backend | L3 | Backend internal components |
| 4 | Component - Frontend | L3 | Frontend layer architecture |
| 5 | Data Flow | - | How data moves through the system |
| 6 | Deployment | - | Local and production deployment |
| 7 | Sequence | - | Key interaction flows |
| 8 | ERD | - | Database entity relationships |
| 9 | Layer Architecture | - | ForgeWorks unique UI pattern |
| 10 | Adapter Pattern | - | Mock/Live switching mechanism |

---

## Viewing Diagrams

### In GitHub

GitHub natively renders Mermaid diagrams in Markdown files.

### In VS Code

Install the [Markdown Preview Mermaid Support](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid) extension.

### Mermaid Live Editor

Copy diagrams to [mermaid.live](https://mermaid.live/) for editing and PNG export.

---

*Last Updated: January 2025*
*Format: Mermaid Diagrams (C4 Model)*
