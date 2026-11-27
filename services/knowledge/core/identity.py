"""Verificación explícita de tokens de Accesos; no activa autenticación global."""

from dataclasses import dataclass
from uuid import UUID

import jwt
from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from core.jwks import KID, key_cache

PERMISSIONS = frozenset(
    {
        "tickets:ver",
        "tickets:atender",
        "tickets:escalar",
        "empresa:configurar",
        "usuarios:administrar",
    }
)
ROLES = frozenset({"administrador", "agente_n1", "agente_n2", "usuario_final"})


@dataclass(frozen=True)
class Identity:
    id: str
    company: str
    role: str
    permissions: frozenset[str]
    is_authenticated: bool = True
    is_anonymous: bool = False

    @property
    def pk(self):
        return self.id


class AccessAuthentication(BaseAuthentication):
    def authenticate_header(self, request):
        return "Bearer"

    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header:
            return None
        try:
            if len(header) != 2 or header[0].lower() != b"bearer" or len(header[1]) > 16384:
                raise ValueError
            token = header[1]
            metadata = jwt.get_unverified_header(token)
            kid = metadata.get("kid")
            if (
                metadata.get("alg") != "RS256"
                or not isinstance(kid, str)
                or not KID.fullmatch(kid)
                or any(name in metadata for name in ("jku", "jwk", "x5u", "crit", "b64"))
            ):
                raise ValueError
            config = settings.ACCESS_IDENTITY
            claims = jwt.decode(
                token,
                key_cache(config["url"]).key(kid),
                algorithms=["RS256"],
                issuer=config["issuer"],
                options={
                    "require": [
                        "sub",
                        "exp",
                        "iat",
                        "iss",
                        "empresa",
                        "rol",
                        "permisos",
                        "token_type",
                    ],
                },
            )
            permissions = claims["permisos"]
            if (
                claims["token_type"] != "access"
                or claims["empresa"] != config["company"]
                or not isinstance(claims["rol"], str)
                or claims["rol"] not in ROLES
                or type(claims["exp"]) is not int
                or type(claims["iat"]) is not int
                or claims["exp"] <= claims["iat"]
                or not isinstance(permissions, list)
                or len(permissions) > len(PERMISSIONS)
                or any(not isinstance(p, str) or p not in PERMISSIONS for p in permissions)
                or len(set(permissions)) != len(permissions)
            ):
                raise ValueError
            subject = str(UUID(claims["sub"]))
            identity = Identity(subject, claims["empresa"], claims["rol"], frozenset(permissions))
            return identity, claims
        except (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            RecursionError,
            OverflowError,
            jwt.PyJWTError,
        ):
            raise AuthenticationFailed("Identidad de Accesos no válida.") from None


class AccessAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "core.identity.AccessAuthentication"
    name = "bearerAuth"

    def get_security_definition(self, auto_schema):
        return {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
