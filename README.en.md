# Help Chair

[Versión en español → README.md](README.md)

> **Multi-tenant help desk** platform, 100 % aligned with **ITIL v4**, built as **microservices** and deployed as an **isolated stack per company**. All the code lives in this **monorepo**.

Academic-professional project developed at the **Centro de Enseñanza Técnica Industrial (CETI)**.

---

## 📌 What is Help Chair?

Help Chair is a help desk template that companies subscribe to as a service. The life cycle is:

1. A company lands on the **public site** (`help-chair.com`), learns about the product and chooses **Register my company**.
2. It completes a **minimal sign-up** (company, subdomain and administrator), verifies its email and gets its own **subdomain** (e.g. `company12.help-chair.com`).
3. The system creates a **new, empty stack** (dedicated containers and databases) just for that company.
4. The administrator activates the account, sets a password and configures the help desk through an *onboarding* wizard (services, priorities, SLAs, departments, users and roles).
5. From then on the help desk works with events, requests, incidents and problems, with **no contact with other companies' stacks**.

> A paid licence will be added later; for now sign-up is free (a `plan` field is reserved in the directory).

## 🧭 Architecture at a glance

![Multi-tenant view](docs/diagrams/architecture-multitenant.png)

![Single company stack](docs/diagrams/architecture-stack.png)

![Company sign-up](docs/diagrams/registration-flow.png)

More detail in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and, for company sign-up, in [`docs/REGISTRO-EMPRESA.md`](docs/REGISTRO-EMPRESA.md) *(Spanish; summary in English at the end)*.

## 🗂️ Monorepo structure

```
help-chair/
├── services/
│   ├── events/        # Team 1 · Event Management
│   ├── access/        # Team 2 · Access Management
│   ├── requests/      # Team 3 · Request Management
│   ├── incidents/     # Team 4 · Incident Management
│   ├── problems/      # Team 5 · Problem Management
│   └── knowledge/     # Team 5 · Knowledge Base
├── frontend/          # Team 6 · Public site + Service Desk (one SPA)
├── platform/
│   ├── gateway/       # Team 7 · Subdomain gateway, company sign-up + companies DB
│   └── deploy/        # Team 7 · Kubernetes, Helm, docker-compose
├── contracts/         # APIs (OpenAPI) and inter-service messages
├── docs/              # Architecture, ITIL, decisions
├── scripts/           # Repository automation
└── .github/           # CODEOWNERS, templates, workflows
```

## 👥 Teams and folders

| # | Team | ITIL v4 practice | Folder |
|---|------|------------------|--------|
| 1 | Event Management | Monitoring and Event Management | `services/events` |
| 2 | Access Management | Service Request Mgmt + Information Security Mgmt | `services/access` |
| 3 | Request Management | Service Request Management | `services/requests` |
| 4 | Incident Management | Incident Management | `services/incidents` |
| 5 | Problem Management | Problem Management + Knowledge Management | `services/problems`, `services/knowledge` |
| 6 | Frontend | Service Desk + public site and sign-up | `frontend` |
| 7 | Platform | Technical enablement (gateway, company sign-up, tenants, K8s) | `platform/gateway`, `platform/deploy` |

> Each team **owns** its folder (via `CODEOWNERS`), its database and its language/framework. A monorepo is **not** a monolith: every service is still an independent container with its own DB. Teams coordinate **only through contracts** (`contracts/`).

## 📚 ITIL v4 as the guide

The design uses ITIL v4 vocabulary (**practices**, not processes). The full mapping between practices, services and teams is in [`docs/ITIL-MAPPING.md`](docs/ITIL-MAPPING.md).

## 🧱 Design principles

- **Full isolation per company:** one Kubernetes namespace per stack; no stack talks to another.
- **Database per service:** every service has its own database; nobody reads another team's DB.
- **Contracts first:** APIs (OpenAPI) and messages (broker) are defined and versioned in `contracts/`.
- **Independence inside the monorepo:** each folder has its own path-filtered CI, its own image and its own versioning.
- **Resource efficiency:** small images, declared CPU/RAM limits and hibernating idle stacks.

## ✅ Minimum service contract

Every service, whatever the language, must:

- Ship a `Dockerfile` and run as a **non-root** user.
- Expose `GET /health/live` and `GET /health/ready`.
- Be configured **only through environment variables** (no secrets in the repo; provide `.env.example`).
- Write **JSON logs** to stdout/stderr.
- Document its API with **OpenAPI** in `contracts/<service>/` and publish events as defined in `contracts/messages/`.
- Publish its image as `ghcr.io/help-chair/hc-<service>:<semver>`.
- Declare resource `requests`/`limits` in its deployment.
- Shut down gracefully (`SIGTERM`).
- Have its CI workflow **filtered to its own folder**.

## 🚀 Getting started

1. Read the [contributing guide](CONTRIBUTING.en.md) (branching, commits, PRs and monorepo rules).
2. Clone the repository and branch off `develop`:
   ```bash
   git clone https://github.com/help-chair/help-chair.git
   cd help-chair
   git switch develop && git switch -c feature/<area>/<n>-<description>
   ```
3. Work **only inside your team's folder**.
4. Bring up the local environment with `platform/deploy` *(under construction)*.

## 🛠️ Tech stack

| Area | Technology |
|---|---|
| Backend (all services) | Python + Django + Django REST Framework, OpenAPI with `drf-spectacular` |
| Database | DB selected by the team in a container, one per service |
| Frontend | React + Vite + TypeScript (one image for the public site and the Service Desk) |
| Containers | Podman (OCI images) |
| Orchestration | Kubernetes + Helm |
| CI/CD | Jenkins (one `Jenkinsfile` per service) |
| Cloud | Azure, AWS or Google Cloud *(to be decided)* |

## 🗺️ Phase plan

The project is delivered in 5 phases of 5 days each (13 November – 7 December 2026). Full detail, deliverables per team and fallbacks are in [`docs/ROADMAP.md`](docs/ROADMAP.md) *(Spanish; English version pending; includes the public site and company sign-up)*.

| Phase | Dates | Goal |
|---|---|---|
| 1 · Foundations | Nov 13 – 17 | Every service runs in Podman with its DB; contracts v0 |
| 2 · Service core | Nov 18 – 22 | Each service works on its own; CI/CD publishes images; contracts v1 frozen (includes company sign-up) |
| 3 · Integration and testing deployment | Nov 23 – 27 | Full flow deployed in the cloud (testing) with CD; public site and sign-up working |
| 4 · Multi-tenancy and hardening | Nov 28 – Dec 2 | Sign-up from the landing page → isolated stack; security, load and accessibility |
| 5 · Stabilisation and delivery | Dec 3 – 7 | Production, documentation, demo and `v1.0.0` |

## 📄 License

To be defined. Until then, all rights reserved.

## 🏫 Institution

Centro de Enseñanza Técnica Industrial (CETI).
