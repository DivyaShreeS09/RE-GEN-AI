# System Flowcharts

All diagrams use [Mermaid](https://mermaid.js.org/) syntax and render natively on GitHub.

---

## 1. High-Level System Architecture

```mermaid
graph TD
    User["👤 User (Browser)"] --> Hero["HeroSection\n'Launch Campus Intelligence Scan'"]
    Hero -->|"Promise.all"| API["FastAPI Backend :8000"]

    API --> WA["💧 Water Leakage Agent\nwater_usage.csv"]
    API --> EA["⚡ Energy Optimization Agent\nenergy_usage.csv"]
    API --> WsA["♻️ Waste-to-Wealth Agent\nwaste_knowledge_base.json"]

    WA  --> IA["🌿 Pollution & Impact Agent"]
    EA  --> IA
    WsA --> IA

    IA  --> DA["🧠 Decision Engine Agent"]
    DA  --> SA["🏆 RE:GEN Score Agent\ncore/scoring.py"]
    SA  --> RA["📋 Report Agent"]

    RA  -->|"JSON"| FE["React Frontend\n14 interactive sections"]
```

---

## 2. Request Sequence

```mermaid
sequenceDiagram
    participant U  as User
    participant R  as React (App.jsx)
    participant F  as FastAPI
    participant W  as Water Agent
    participant E  as Energy Agent
    participant I  as Impact Agent
    participant D  as Decision Engine
    participant S  as Score Agent
    participant Rp as Report Agent

    U->>R: Click "Launch Campus Intelligence Scan"
    R->>R: Show Mission Control Overlay (8-step)

    par 5 parallel requests
        R->>F: GET /dashboard/summary
        R->>F: GET /analyze/water
        R->>F: GET /analyze/energy
        R->>F: GET /agent-war-room
        R->>F: POST /generate/action-plan
    end

    F->>W: analyze_water()
    W-->>F: anomaly_events, severity, confidence=0.89

    F->>E: analyze_energy()
    E-->>F: wasted_kwh, severity, confidence=0.91

    F->>I: analyze_impact(water_L, energy_kWh, waste_INR)
    I-->>F: co2_saved, sdg_alignment, confidence=0.87

    F->>D: generate_decisions(water, energy, waste?)
    D-->>F: ranked_actions, confidence=0.90

    F->>S: compute_regen_score(water, energy, impact, decision)
    S-->>F: before_score, after_score, confidence=0.88

    F->>Rp: generate_report(all_results)
    Rp-->>F: executive_summary, action_plan, traces

    F-->>R: JSON (all 5 endpoints resolve)
    R->>R: Dismiss overlay (2 s delay)
    R->>U: Render Dashboard + 11 sections
```

---

## 3. Data Flow

```mermaid
graph LR
    subgraph "Simulation Layer"
        WC["water_usage.csv\n168 rows"]
        EC["energy_usage.csv\n168 rows"]
        KB["waste_knowledge_base.json\n30 materials"]
    end

    subgraph "simulation.py"
        LW["load_water_data()"]
        LE["load_energy_data()"]
        LK["load_waste_kb() — cached"]
    end

    subgraph "Agent Pipeline"
        WAgent["Water Agent"]
        EAgent["Energy Agent"]
        WsAgent["Waste Agent"]
        IAgent["Impact Agent"]
        DAgent["Decision Engine"]
        SAgent["Score Agent"]
        RAgent["Report Agent"]
    end

    WC --> LW --> WAgent
    EC --> LE --> EAgent
    KB --> LK --> WsAgent

    WAgent  --> IAgent
    EAgent  --> IAgent
    WsAgent --> IAgent
    IAgent  --> DAgent
    DAgent  --> SAgent
    SAgent  --> RAgent
    RAgent  -->|"JSON"| FastAPI["FastAPI Endpoints"]
    FastAPI -->|"axios"| React["React Dashboard"]
```

---

## 4. Complete Request Flow

```mermaid
flowchart TD
    A["User triggers scan"] --> B["Promise.all — 5 requests"]
    B --> C["/dashboard/summary"]
    B --> D["/analyze/water"]
    B --> E["/analyze/energy"]
    B --> F["/agent-war-room"]
    B --> G["POST /generate/action-plan"]

    C --> H["CSV loaders"]
    H --> I["Water Agent → severity"]
    H --> J["Energy Agent → wasted kWh"]
    I & J --> K["Impact Agent → CO₂, SDGs"]
    K --> L["Decision Engine → ranked actions"]
    L --> M["Score Agent → before/after score"]
    M --> N["Report Agent → summary + plan"]
    N --> O["JSON → React"]

    D --> P["Water Agent (standalone) → hourly chart"]
    E --> Q["Energy Agent (standalone) → hourly chart"]
    F --> R["7-agent War Room status"]
    G --> S["Full pipeline + reasoning traces"]

    O --> T["Overlay dismissed → Dashboard rendered"]
```

---

## 5. React Component Architecture

```mermaid
graph LR
    subgraph "App.jsx (orchestrator)"
        App --> Hero["HeroSection"]
        App --> Dash["CommandCenterDashboard"]
        App --> Twin["DigitalTwinCampus"]
        App --> Waste["WasteAnalyzer"]
        App --> Water["WaterPanel"]
        App --> Energy["EnergyPanel"]
        App --> Heat["ResourceLossHeatmap"]
        App --> Proj["ImpactProjection"]
        App --> Sim["InterventionSimulator"]
        App --> Ach["SustainabilityAchievements"]
        App --> War["AgentWarRoom"]
        App --> Plan["ActionPlan"]
        App --> Why["WhyThisMatters"]
        App --> Cap["CapstoneMappingSection"]
    end

    subgraph "Backend"
        Main["main.py (7 routes)"]
        Main --> Agents["agents/*.py (7 agents)"]
        Agents --> Core["core/scoring.py\ncore/guardrails.py\ncore/simulation.py"]
    end

    App -->|"axios /api proxy"| Main
```

---

*See also: [ARCHITECTURE.md](ARCHITECTURE.md) · [AGENTS.md](AGENTS.md)*
