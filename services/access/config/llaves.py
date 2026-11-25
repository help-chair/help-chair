"""Llaves con las que se firma el token, y su publicación como JWKS.

El token se firma con RS256: la llave privada vive solo aquí y los demás
servicios validan con la pública, que se publica en
``/api/access/v1/.well-known/jwks.json``. Con HS256 habría que repartir el
``SECRET_KEY``, y quien lo tenga no solo verifica tokens: los fabrica.

La llave se toma de ``JWT_PRIVATE_KEY``. En desarrollo y en las pruebas, si no
está definida se genera una y se guarda en ``build/jwt-dev.pem``, que no se
versiona. Se guarda en disco a propósito: generar una por proceso daría llaves
distintas en cada worker de gunicorn y un token firmado por uno no valdría en
el otro. Fuera de desarrollo, si falta la variable el servicio no arranca.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from functools import lru_cache
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.core.exceptions import ImproperlyConfigured

registro = logging.getLogger(__name__)

ALGORITMO = "RS256"
TAMANO_DE_LLAVE = 2048


def _b64url(datos: bytes) -> str:
    """Base64 de URL sin relleno, como lo pide el RFC 7515."""
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode("ascii")


def _a_bytes(numero: int) -> bytes:
    return numero.to_bytes((numero.bit_length() + 7) // 8, "big")


def generar_llave_privada() -> str:
    """Un par RSA nuevo, devuelto como PEM PKCS#8 sin contraseña."""
    llave = rsa.generate_private_key(public_exponent=65537, key_size=TAMANO_DE_LLAVE)
    return llave.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")


def cargar_llave_privada(
    pem_del_entorno: str,
    *,
    es_desarrollo: bool,
    ruta_de_desarrollo: Path,
) -> str:
    """La llave privada en PEM, de la variable de entorno o la de desarrollo."""
    if pem_del_entorno:
        # Una variable de entorno de una sola linea trae los saltos escapados.
        return pem_del_entorno.replace("\\n", "\n").strip() + "\n"

    if not es_desarrollo:
        raise ImproperlyConfigured(
            "Falta JWT_PRIVATE_KEY. Genérala con `make llaves` y ponla en el entorno; "
            "sin ella el servicio no puede firmar tokens (ver .env.example)."
        )

    if ruta_de_desarrollo.exists():
        return ruta_de_desarrollo.read_text(encoding="ascii")

    pem = generar_llave_privada()
    ruta_de_desarrollo.parent.mkdir(parents=True, exist_ok=True)
    ruta_de_desarrollo.write_text(pem, encoding="ascii")
    ruta_de_desarrollo.chmod(0o600)
    registro.warning(
        "JWT_PRIVATE_KEY no está definida: se generó una llave de desarrollo en %s. "
        "No sirve para producción.",
        ruta_de_desarrollo,
    )
    return pem


@lru_cache(maxsize=4)
def llave_publica(privada_pem: str) -> str:
    """La parte pública de la llave, en PEM."""
    privada = serialization.load_pem_private_key(privada_pem.encode("ascii"), password=None)
    return (
        privada.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
    )


@lru_cache(maxsize=4)
def jwk_publica(privada_pem: str) -> dict[str, str]:
    """La llave pública como JWK, con la forma que declara el contrato."""
    privada = serialization.load_pem_private_key(privada_pem.encode("ascii"), password=None)
    numeros = privada.public_key().public_numbers()
    n = _b64url(_a_bytes(numeros.n))
    e = _b64url(_a_bytes(numeros.e))
    return {
        "kty": "RSA",
        "kid": calcular_kid(n, e),
        "use": "sig",
        "alg": ALGORITMO,
        "n": n,
        "e": e,
    }


def calcular_kid(n: str, e: str) -> str:
    """Huella de la llave según el RFC 7638, para nombrarla igual en todos lados."""
    canonico = json.dumps({"e": e, "kty": "RSA", "n": n}, separators=(",", ":"), sort_keys=True)
    return _b64url(hashlib.sha256(canonico.encode("ascii")).digest())


def instalar_kid_en_la_cabecera(kid: str) -> None:
    """Hace que SimpleJWT escriba el `kid` en la cabecera de los tokens que firma.

    SimpleJWT llama a ``jwt.encode`` sin el argumento ``headers``, así que los
    tokens salen sin ``kid``. Sin él, el ``PyJWKClient`` que usan los demás
    servicios no sabe cuál de las llaves publicadas aplicar y falla en cuanto
    haya más de una, que es justo lo que pasa al rotar.

    En vez de reescribir ``TokenBackend.encode``, que cambiaría entre versiones,
    se sustituye el nombre ``jwt`` dentro del módulo de SimpleJWT por un envoltorio
    que añade la cabecera y delega todo lo demás en PyJWT. No toca a PyJWT en
    general: solo a cómo lo ve ese módulo.
    """
    from rest_framework_simplejwt import backends

    if isinstance(backends.jwt, _PyjwtConKid):
        return
    backends.jwt = _PyjwtConKid(backends.jwt, kid)


class _PyjwtConKid:
    """Envoltorio de PyJWT que firma poniendo el `kid` en la cabecera."""

    def __init__(self, pyjwt, kid: str):
        self._pyjwt = pyjwt
        self._kid = kid

    def __getattr__(self, nombre: str):
        return getattr(self._pyjwt, nombre)

    def encode(self, payload, key, algorithm=None, headers=None, **resto):
        cabeceras = {"kid": self._kid}
        cabeceras.update(headers or {})
        return self._pyjwt.encode(payload, key, algorithm=algorithm, headers=cabeceras, **resto)
