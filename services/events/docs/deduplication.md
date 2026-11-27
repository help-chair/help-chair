# Deduplicación de eventos / Event deduplication

*Español primero, English summary al final.*

> Servicio: `services/events` · Práctica ITIL v4: Monitoring and Event Management
> Código: `events/services/{fingerprint,similarity,deduplication,registration}.py`

## 1. Qué problema resuelve

Los eventos repetidos saturan el sistema y ocultan el problema real. Cuando llega un evento que
ya está abierto no se crea otro registro: se **incrementa su contador** y se guarda la ocurrencia.

## 2. Cómo funciona

```
POST /events
   │
   ├─ 1. Clasifica el tipo (INFORMATION / WARNING / EXCEPTION)
   ├─ 2. Calcula la huella  = tipo + origen + fuente + servicio + título y mensaje NORMALIZADOS
   ├─ 3. ¿Hay un evento ABIERTO con esa huella?  ── sí ──► suma ocurrencia (200)         [etapa 1]
   ├─ 4. (opcional) ¿hay uno abierto CASI idéntico? ─ sí ─► suma ocurrencia, auditada (200) [etapa 2]
   └─ 5. no ──► crea el evento (201) y su primera ocurrencia
```

### Etapa 1 · huella exacta sobre texto normalizado (siempre activa)

`normalize_text` pasa a minúsculas, colapsa espacios y reemplaza los **datos volátiles** por
marcadores, para que dos ocurrencias del mismo problema (**duplicados parciales**) coincidan:

| Dato | Ejemplo | Marcador |
|---|---|---|
| UUID | `7c9e6679-7425-…` | `<uuid>` |
| Fecha y hora | `2026-11-20T10:00:00Z`, `2026-11-21`, `10:45` | `<ts>` `<date>` `<time>` |
| IPv4 (con puerto) | `10.0.0.12:5432` | `<ip>` |
| Hexadecimales | `0x7ffd5c3a`, `deadbeef01` | `<hex>` |
| Cantidades con unidad | `5003 ms`, `95%`, `12.5 GB` | `<qty>` |
| Números largos (≥ 5 dígitos) | `1234567` | `<num>` |

**Los números cortos se conservan** (`status 500` ≠ `status 404`): fusionarlos sería un
*over-merge*. Con `EVENT_MASK_SHORT_NUMBERS=true` también se enmascaran (más fusiones, más riesgo).
El `payload` **no** entra en la huella. Versión de la huella: `v2` (`FINGERPRINT_VERSION`).

### Etapa 2 · similitud Jaro-Winkler (opcional, apagada por defecto)

Pensada para erratas y variaciones mínimas de redacción. Jaro-Winkler solo fusionaría de más
(dos mensajes largos que difieren en una palabra puntúan ~0.99), así que `compare_messages` exige:

1. mismo tipo, origen, categoría, fuente y servicio, y evento **abierto** visto dentro de la ventana T;
2. solo tipos configurados (`WARNING` e `INFORMATION`) y **nunca** categoría `SECURITY`;
3. mensajes de al menos 20 caracteres y **el mismo número de palabras**;
4. a lo sumo **1 palabra** distinta, que no contenga dígitos y que sea ella misma una errata
   (Jaro-Winkler de la palabra ≥ 0.88: `primay`≈`primary` sí; `primary`↔`replica` no);
5. Jaro-Winkler del mensaje completo ≥ 0.95.

Cada fusión por similitud deja una ocurrencia `FUZZY` con su puntaje y una fila en el historial
(`actor_ref = "dedup"`), para auditar y detectar *over-merges*.

## 3. Ventana T y `n_eventos_similares`

- **Mientras un evento esté abierto, la misma huella es el mismo evento**, sea cual sea su edad
  (así se respeta `uq_event_open_fingerprint`: un solo abierto por huella).
- `similar_event_count(event)` = ocurrencias con la huella del evento dentro de **T días**.
  Cuenta también las de eventos anteriores ya cerrados: un patrón repetido lo es aunque cada vez
  se haya cerrado. **T** sale de la `RecurrencePolicy` aplicable (o de `EVENT_RECURRENCE_DEFAULT`).
- La regla 3 usa ese conteo (alerta una sola vez al cruzar el umbral).

## 4. Concurrencia

1. `SELECT … FOR UPDATE` sobre el evento abierto → los incrementos se serializan.
2. Si ninguna petición vio el evento, todas intentan el `INSERT`; la restricción única parcial
   `uq_event_open_fingerprint` deja pasar una y las demás reciben `IntegrityError`, que se atrapa
   en un *savepoint* y se cuenta como una ocurrencia más.

Prueba: `tests/test_deduplication_concurrency.py` (8 y 24 peticiones simultáneas; PostgreSQL).

## 5. Configuración

| Variable | Defecto | Efecto |
|---|---|---|
| `EVENT_FUZZY_ENABLED` | `false` | Activa la etapa 2 |
| `EVENT_FUZZY_THRESHOLD` | `0.95` | Jaro-Winkler mínimo del mensaje |
| `EVENT_FUZZY_TOKEN_THRESHOLD` | `0.88` | Jaro-Winkler mínimo de la palabra que cambia |
| `EVENT_FUZZY_MAX_DIFF_TOKENS` | `1` | Palabras que pueden diferir |
| `EVENT_FUZZY_MIN_LENGTH` | `20` | Largo mínimo para comparar |
| `EVENT_FUZZY_MAX_CANDIDATES` | `50` | Candidatos abiertos que se comparan |
| `EVENT_FUZZY_TYPES` | `WARNING,INFORMATION` | Tipos donde aplica la etapa 2 |
| `EVENT_MASK_SHORT_NUMBERS` | `false` | Enmascara también números cortos |
| `EVENT_RECURRENCE_DEFAULT` | `3` en `7` días | N y T cuando no hay `RecurrencePolicy` |

## 6. Límites y decisiones

- Cambiar la normalización o `FINGERPRINT_VERSION` hace que los eventos **ya abiertos** dejen de
  coincidir con los nuevos (se crea uno nuevo una vez). Hazlo con el sistema vacío o cierra los abiertos.
- La etapa 2 no puede protegerse con una restricción de BD: dos erratas simultáneas pueden
  crear dos eventos (se consideran eventos distintos; nunca se pierde información).
- Cada llegada escribe una fila en `event_occurrence`. Conviene retención y, con TimescaleDB,
  convertirla en *hypertable* (ver abajo) cuando el volumen lo justifique.
- Fuera de alcance: expirar eventos abiertos sin actividad (decisión del equipo).

### Opcional · *hypertable* (probar primero en TimescaleDB real)

`create_hypertable` exige que toda llave única incluya la columna de tiempo, así que la llave
primaria pasa a `(id, occurred_at)`. Va en una migración **aparte**, solo para PostgreSQL:

```python
from django.db import migrations


def to_hypertable(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute("ALTER TABLE event_occurrence DROP CONSTRAINT event_occurrence_pkey")
    schema_editor.execute("ALTER TABLE event_occurrence ADD PRIMARY KEY (id, occurred_at)")
    schema_editor.execute(
        "SELECT create_hypertable('event_occurrence', 'occurred_at', "
        "chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE, migrate_data => TRUE)"
    )


class Migration(migrations.Migration):
    dependencies = [("events", "<la migración que crea event_occurrence>")]
    operations = [migrations.RunPython(to_hypertable, migrations.RunPython.noop)]
```

## 7. Cómo probarlo

```bash
cd services/events
uv run pytest tests/test_similarity.py tests/test_fingerprint.py tests/test_deduplication.py -q
# Concurrencia (PostgreSQL / TimescaleDB del compose):
DATABASE_URL=postgres://events:events@localhost:5441/events \
  uv run pytest tests/test_deduplication_concurrency.py -q
```

---

## English summary

Repeated events are merged into the open event instead of creating new rows. **Stage 1 (always on):**
the fingerprint is `type + origin + source + service + normalized title + normalized message`;
volatile data (UUIDs, timestamps, IPs, hex ids, durations/sizes, long numbers) is masked so
*partial duplicates* collide; short numbers are kept to avoid over-merging (`500` ≠ `404`).
**Stage 2 (optional, off by default):** Jaro-Winkler similarity guarded against over-merging
(same type/source/service, no SECURITY, same word count, at most one differing word that is itself
a typo and contains no digits). **Window T** (from the recurrence policy) bounds
`similar_event_count`, the `n_eventos_similares` used by rules 3 and 7. **Concurrency:** row lock
plus the partial unique constraint `uq_event_open_fingerprint`, with the `IntegrityError` race
handled in a savepoint; covered by a threaded test on PostgreSQL.
