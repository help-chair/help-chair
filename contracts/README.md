# contracts/

**ES:** Único punto de acuerdo entre equipos. Cada servicio publica aquí su API (`<servicio>/openapi.yaml`) y los mensajes compartidos viven en `messages/` (esquemas JSON, sobre de evento común). Un cambio incompatible exige subir `MAJOR` y avisar a los equipos consumidores en el PR.

**EN:** The single agreement point between teams. Each service publishes its API here (`<service>/openapi.yaml`); shared messages live in `messages/` (JSON schemas, common event envelope). A breaking change requires a `MAJOR` bump and notifying consuming teams in the PR.

```
contracts/
├── events/ access/ requests/ incidents/ problems/ knowledge/   # OpenAPI por servicio
└── messages/                                                    # esquemas de mensajes del broker
```
