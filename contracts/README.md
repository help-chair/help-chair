# contracts/

**ES:** Único punto de acuerdo entre equipos. Cada servicio publica aquí su API (`<servicio>/openapi.yaml`) y los mensajes compartidos viven en `messages/` (esquemas JSON, sobre de evento común). Un cambio incompatible exige subir `MAJOR` y avisar a los equipos consumidores en el PR.

**ES (registro):** `gateway/openapi.yaml` define la API pública de alta de empresas (dueño: Plataforma; consumidor: Frontend). Los endpoints de administrador inicial y activación los publica Accesos en `access/openapi.yaml` (ver `docs/REGISTRO-EMPRESA.md`).

**EN:** The single agreement point between teams. Each service publishes its API here (`<service>/openapi.yaml`); shared messages live in `messages/` (JSON schemas, common event envelope). A breaking change requires a `MAJOR` bump and notifying consuming teams in the PR.

```
contracts/
├── events/ access/ requests/ incidents/ problems/ knowledge/   # OpenAPI por servicio
├── gateway/                                                     # API pública de registro de empresas (Plataforma)
└── messages/                                                    # esquemas de mensajes del broker
```

**EN (sign-up):** `gateway/openapi.yaml` defines the public company sign-up API (owner: Platform; consumer: Frontend). The initial-administrator and activation endpoints are published by Access in `access/openapi.yaml` (see `docs/REGISTRO-EMPRESA.md`).
