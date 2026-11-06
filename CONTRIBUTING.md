# Guía de contribución — Help Chair (monorepo)

[English version → CONTRIBUTING.en.md](CONTRIBUTING.en.md)

Siete equipos trabajan en un mismo repositorio. Esta guía existe para que cualquiera pueda trabajar una rama, subir cambios y fusionarlos **sin pisar el trabajo de los demás**.

## 0. Reglas de oro del monorepo

1. **Trabaja solo dentro de la carpeta de tu equipo.** `CODEOWNERS` exige la aprobación del dueño de cada carpeta.
2. **Cambios que cruzan carpetas:** sepáralos en PRs distintos o pide la aprobación de ambos equipos.
3. **Los equipos se comunican por contratos** (`contracts/`), nunca importando código ni leyendo la BD de otro servicio.
4. **PR pequeños y frecuentes.** Con 7 equipos sobre `develop`, un PR grande y viejo = conflictos.
5. **Cada carpeta tiene su propio CI** filtrado por ruta: tu CI solo corre cuando cambias tu carpeta.

## 1. Modelo de ramas

| Rama | Propósito | Quién escribe | Protegida |
|---|---|---|---|
| `main` | Estable, lista para desplegar. | Solo por PR desde `develop` o `hotfix/*` | ✅ |
| `develop` | Integración de todos los equipos. Rama por defecto. | Solo por PR desde ramas de trabajo | ✅ |
| `feature/<area>/<n>-<slug>` | Nueva funcionalidad. Sale de `develop`. | Quien la desarrolla | ❌ |
| `fix/<area>/<n>-<slug>` | Corrección de bug en `develop`. | Quien la corrige | ❌ |
| `hotfix/<area>/<n>-<slug>` | Corrección urgente sobre `main`. | Quien la corrige | ❌ |
| `docs/<slug>`, `chore/<slug>`, `refactor/<area>/<slug>` | Documentación, mantenimiento, refactor. | Quien lo hace | ❌ |

- `<area>` = `events`, `access`, `requests`, `incidents`, `problems`, `knowledge`, `frontend`, `gateway`, `deploy` o `contracts`.
- `<n>` = número del issue; `<slug>` = descripción corta en minúsculas con guiones.
- Ejemplo: `feature/events/42-clasificacion-informativos`.

**Reglas:** ramas **cortas** (idealmente < 1 semana), se borran al fusionar y **nunca** hay push directo a `main` ni `develop`.

## 2. Flujo de trabajo diario

```bash
# 1. Sincroniza y crea tu rama
git switch develop
git pull origin develop
git switch -c feature/events/42-clasificacion-informativos

# 2. Trabaja en tu carpeta con commits pequeños (ver sección 3)
git add services/events
git commit -m "feat(events): agrega regla de eventos informativos"

# 3. Actualiza tu rama con develop con frecuencia (al menos a diario)
git fetch origin
git rebase origin/develop       # o: git merge origin/develop

# 4. Sube tu rama y abre el Pull Request hacia develop
git push -u origin feature/events/42-clasificacion-informativos
```

> Si ya compartiste tu rama con otras personas, usa `merge` en lugar de `rebase` y nunca fuerces el push.
> Truco: usa `git add <tu-carpeta>` en vez de `git add .` para no subir archivos de otras áreas por accidente.

## 3. Commits — Conventional Commits con *scope* obligatorio

Formato: `tipo(scope): descripción en imperativo`

| Tipo | Uso |
|---|---|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Documentación |
| `style` | Formato (sin cambio de lógica) |
| `refactor` | Cambio interno sin cambiar comportamiento |
| `perf` | Mejora de rendimiento |
| `test` | Pruebas |
| `build` / `ci` | Dependencias, Dockerfile, pipelines |
| `chore` | Mantenimiento |
| `revert` | Revertir un commit |

**Scopes permitidos** (uno por carpeta): `events`, `access`, `requests`, `incidents`, `problems`, `knowledge`, `frontend`, `gateway`, `deploy`, `contracts`, `docs`, `ci`, `repo`.

- Cambio que rompe compatibilidad: añade `!` (`feat(contracts)!: …`) y explica con `BREAKING CHANGE:` en el cuerpo.
- Referencia el issue: `Closes #42`.

## 4. Pull Requests

1. **Destino:** `develop` (o `main` si es `hotfix/*`).
2. **Título:** Conventional Commits con scope (un workflow lo valida; se usa como mensaje del *squash*).
3. Completa la plantilla (qué, por qué, área afectada, cómo probar, checklist).
4. **Tamaño:** preferentemente < 400 líneas. Si es más grande, divídelo.
5. **Revisión:** mínimo **1 aprobación de un code owner** de las carpetas tocadas. Quien abre el PR no lo aprueba.
6. Conversaciones resueltas y checks de CI en verde.
7. Si cambias un contrato, **menciona a los equipos consumidores** (`@help-chair/team-…`) en el PR y espera su visto bueno.

## 5. Estrategia de merge

| Origen → Destino | Método | Motivo |
|---|---|---|
| rama de trabajo → `develop` | **Squash and merge** | 1 commit por cambio; historial legible con 7 equipos |
| `develop` → `main` | **Merge commit** | Conserva el historial de integración |
| `hotfix/*` → `main` | **Merge commit** | Trazabilidad del arreglo urgente |
| `main` → `develop` (tras un hotfix) | **Merge commit** | Evitar que el arreglo se pierda |

No se usa *rebase and merge* en la interfaz de GitHub.

## 6. Versionado y publicación (por servicio)

- **SemVer por servicio**, no por repositorio. Se etiqueta sobre `main` con `<carpeta>/vX.Y.Z`, por ejemplo `events/v1.2.0` o `platform-gateway/v0.3.1`.
- Cada etiqueta dispara (en el CI del equipo) la publicación de la imagen `ghcr.io/help-chair/hc-<servicio>:X.Y.Z`.
- Crea un GitHub Release por etiqueta con las notas del cambio.
- `contracts/` se versiona con el servicio que lo publica; un cambio incompatible exige `MAJOR`.
- Para publicar: PR `develop` → `main`, y tras el merge se crean las etiquetas de los servicios que cambiaron.

## 7. CI por carpeta

Cada equipo crea su workflow en `.github/workflows/<servicio>-ci.yml` (su carpeta, su lenguaje), filtrado por ruta. Ejemplo:

```yaml
name: events-ci
on:
  pull_request:
    paths: ['services/events/**', 'contracts/events/**', 'contracts/messages/**']
  push:
    branches: [develop]
    paths: ['services/events/**']
jobs:
  build-test:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: services/events } }
    steps:
      - uses: actions/checkout@v4
      # TODO: setup del lenguaje, pruebas y build de la imagen
```

> Los archivos de `.github/workflows/` son de Plataforma según `CODEOWNERS`; el PR de un workflow nuevo lo aprueba Plataforma.

## 8. Hotfix

```bash
git switch main && git pull origin main
git switch -c hotfix/access/57-corrige-login
# ...arreglo + commit...
# PR hacia main → merge → etiqueta access/vX.Y.(Z+1)
# Después, PR main → develop
```

## 9. Seguridad

- **Nunca** subas secretos, tokens, contraseñas ni `.env`. Usa `.env.example`.
- Si subes un secreto por error, **revócalo de inmediato** y avisa a los mantenedores (borrar el commit no basta).

## 10. Definición de "hecho"

- [ ] Solo toca la carpeta de mi equipo (o está justificado y aprobado).
- [ ] Cumple el *Contrato mínimo de servicio* (si aplica).
- [ ] Pruebas incluidas y pasando.
- [ ] Documentación y OpenAPI actualizadas.
- [ ] `contracts/` actualizado si cambian APIs o mensajes.
- [ ] Sin secretos ni datos reales.
- [ ] PR revisado y aprobado.

## 11. Reglas de protección configuradas

`main` y `develop`: PR obligatorio, 1 aprobación de code owner, aprobaciones obsoletas descartadas, conversaciones resueltas, sin force-push ni borrado.
