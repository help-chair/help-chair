# Cómo validar el token de Accesos en tu servicio

Para los equipos de Eventos, Peticiones, Incidencias, Problemas y Base de Conocimiento.

Tu servicio **no llama a Accesos para validar un token**. Se descarga una vez la llave pública y valida por su cuenta, en memoria. Si Accesos se cae, tu servicio sigue autenticando.

Tampoco necesitas una tabla de usuarios ni un `AUTH_USER_MODEL`: todo lo que hace falta para autorizar viene dentro del token.

## Lo que trae el token

| Claim | Qué es | Ejemplo |
|---|---|---|
| `sub` | Identificador del usuario | `"3f9a…"` |
| `empresa` | Empresa dueña del stack | `"empresa-demo"` |
| `rol` | Uno de cuatro | `"agente_n1"` |
| `permisos` | Lista de permisos | `["tickets:ver", "tickets:atender"]` |
| `iss` | Quién lo emitió | `"help-chair-access"` |
| `iat`, `exp` | Emisión y vencimiento | — |

**Pregunta por permiso, no por rol.** Los cinco permisos son `tickets:ver`, `tickets:atender`, `tickets:escalar`, `empresa:configurar` y `usuarios:administrar`. Si mañana cambian los roles, tu código no se entera.

## Paso 1: la dependencia

RS256 necesita `cryptography`, que llega con el extra `crypto` de PyJWT:

```bash
cd services/<tu-servicio>
uv add "pyjwt[crypto]>=2.9"
```

## Paso 2: la configuración

En tu `config/settings.py`:

```python
SIMPLE_JWT = {
    "ALGORITHM": "RS256",
    # De aquí se baja la llave pública. No pongas SIGNING_KEY ni VERIFYING_KEY:
    # tu servicio no firma tokens, solo los verifica.
    "JWK_URL": env(
        "JWKS_URL",
        default="http://access:8002/api/access/v1/.well-known/jwks.json",
    ),
    "ISSUER": "help-chair-access",
    # Accesos nombra `sub` al identificador del usuario, no `user_id`.
    "USER_ID_CLAIM": "sub",
}

REST_FRAMEWORK = {
    # ...lo que ya tengas...
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTStatelessUserAuthentication",
    ],
}
```

La clase importa. La de siempre, `JWTAuthentication`, busca al usuario en **tu** base y truena porque ahí no existe. `JWTStatelessUserAuthentication` arma un `TokenUser` en memoria a partir de los claims, sin tocar la base, que es justo lo que quieres. En guías viejas aparece como `JWTTokenUserAuthentication`; ese nombre sigue sirviendo, pero usa el nuevo.

Y en tu `.env.example`:

```
JWKS_URL=http://access:8002/api/access/v1/.well-known/jwks.json
```

En el compose local el nombre del servicio es `access` y el puerto el `8002`. En testing cambia el host; la variable está para eso.

## Paso 3: exigir un permiso

Copia esto a tu servicio, por ejemplo en `<tu_app>/permissions.py`:

```python
from rest_framework.permissions import BasePermission


def permisos_de(request) -> set[str]:
    """Los permisos que vienen dentro del token."""
    token = getattr(request, "auth", None)
    if token is None:
        return set()
    try:
        return set(token["permisos"] or [])
    except (KeyError, TypeError):
        return set()


def requiere(*permisos_necesarios: str) -> type[BasePermission]:
    """Permite el paso si el token trae al menos uno de los permisos."""
    necesarios = {str(p) for p in permisos_necesarios}

    class PermisoRequerido(BasePermission):
        message = "Tu rol no tiene permiso para esta operación."

        def has_permission(self, request, view) -> bool:
            usuario = getattr(request, "user", None)
            if usuario is None or not usuario.is_authenticated:
                return False
            return bool(permisos_de(request) & necesarios)

    return PermisoRequerido
```

Y en la vista:

```python
from .permissions import requiere


class IncidentesView(APIView):
    permission_classes = [requiere("tickets:ver", "tickets:atender")]
```

Varios permisos significan «cualquiera de estos», no «todos».

Para saber de qué empresa es quien llama: `request.auth["empresa"]`.

## Paso 4: comprobarlo

Con el compose arriba, pide un token a Accesos y úsalo contra tu endpoint:

```bash
TOKEN=$(curl -s -X POST http://localhost:8002/api/access/v1/login \
  -H 'Content-Type: application/json' \
  -d '{"correo":"admin@empresa-demo.mx","password":"tu-clave"}' | jq -r .acceso)

curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8004/api/incidents/v1/incidentes
```

Si quieres ver qué trae el token sin validarlo:

```bash
echo "$TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | jq
```

Y la llave pública, para confirmar que la alcanzas desde tu contenedor:

```bash
curl -s http://localhost:8002/api/access/v1/.well-known/jwks.json | jq
```

## Rotación de llaves

Cada llave tiene un `kid`, que es su huella, y los tokens lo llevan en la cabecera. Tu servicio pide el JWKS, lo guarda en memoria y escoge la llave por ese `kid`. Cuando Accesos rote, publicará la nueva **antes** de empezar a firmar con ella, así que no tienes que hacer nada.

## Errores comunes

| Qué ves | Qué pasa |
|---|---|
| `Token is invalid` y nada más | Falta `"ALGORITHM": "RS256"`; por omisión SimpleJWT usa HS256 |
| Error de usuario inexistente | Estás usando `JWTAuthentication` en vez de `JWTStatelessUserAuthentication` |
| `request.auth` llega vacío | Falta el `DEFAULT_AUTHENTICATION_CLASSES` o la cabecera `Authorization: Bearer` |
| Falla al bajar el JWKS | Tu contenedor no alcanza a `access`; revisa el nombre del servicio y la red del compose |
| `Invalid issuer` | El `ISSUER` no coincide con `help-chair-access` |

## Lo que no hay que hacer

**No llames a Accesos en cada petición** para preguntar si un token es válido. Ese es justo el acoplamiento que la llave pública evita, y convierte a Accesos en el punto único de falla de todo el sistema.

**No pidas el `SECRET_KEY` de Accesos.** Con esa llave no solo verificarías tokens: podrías fabricarlos. Por eso la firma es RS256 y no HS256.

**No guardes el JWKS en el repositorio.** Se baja en caliente; si lo congelas, una rotación te deja fuera.

Si algo de esto no te funciona siguiendo solo la guía, dime y la corrijo: esa es la prueba de que está terminada.
