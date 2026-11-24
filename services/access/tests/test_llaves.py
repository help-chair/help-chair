"""Pruebas de la firma RS256 y del JWKS.

Lo que importa aquí no es que el endpoint responda, sino que **otro servicio**
pueda validar un token nuestro teniendo solo la llave pública, sin conocer la
privada y sin llamarnos en cada petición. Eso es lo que pide el #187.
"""

import jwt
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

from core.models import Permiso, Rol

JWKS = "/api/access/v1/.well-known/jwks.json"
LOGIN = "/api/access/v1/login"
CORREO = "beto@empresa-demo.mx"
CLAVE = "clave-de-prueba-123"

Usuario = get_user_model()


@pytest.fixture
def usuario(db):
    rol = Rol.objects.create(
        id=Rol.ADMINISTRADOR, nombre="Administrador", permisos=[Permiso.USUARIOS_ADMINISTRAR]
    )
    return Usuario.objects.create_user(correo=CORREO, password=CLAVE, nombre="Beto Lara", rol=rol)


def _token_de_acceso(client):
    respuesta = client.post(
        LOGIN, {"correo": CORREO, "password": CLAVE}, content_type="application/json"
    )
    assert respuesta.status_code == 200, respuesta.content
    return respuesta.json()["acceso"]


def _llave_del_jwks(jwks: dict, kid: str):
    """Lo que haría otro servicio: escoger la llave por el `kid` del token."""
    elegida = next(llave for llave in jwks["keys"] if llave["kid"] == kid)
    return jwt.PyJWK.from_dict(elegida).key


def test_el_jwks_se_sirve_sin_credenciales(client):
    respuesta = client.get(JWKS)
    assert respuesta.status_code == 200
    assert respuesta.json()["keys"]


def test_el_jwk_trae_los_campos_que_declara_el_contrato(client):
    llave = client.get(JWKS).json()["keys"][0]
    assert sorted(llave) == ["alg", "e", "kid", "kty", "n", "use"]
    assert llave["kty"] == "RSA"
    assert llave["use"] == "sig"
    assert llave["alg"] == "RS256"


def test_el_jwks_no_expone_la_llave_privada(client):
    cuerpo = client.get(JWKS).content.decode()
    assert "PRIVATE" not in cuerpo
    # `d` es el exponente privado: si apareciera, estaríamos regalando la llave.
    assert "d" not in client.get(JWKS).json()["keys"][0]


def test_el_token_se_firma_con_rs256_y_lleva_el_kid_publicado(client, usuario):
    token = _token_de_acceso(client)
    cabecera = jwt.get_unverified_header(token)
    assert cabecera["alg"] == "RS256"
    assert cabecera["kid"] == client.get(JWKS).json()["keys"][0]["kid"]


def test_otro_servicio_valida_el_token_solo_con_el_jwks(client, usuario):
    token = _token_de_acceso(client)
    jwks = client.get(JWKS).json()

    # De aquí en adelante, nadie toca la llave privada.
    publica = _llave_del_jwks(jwks, jwt.get_unverified_header(token)["kid"])
    claims = jwt.decode(
        token,
        publica,
        algorithms=["RS256"],
        issuer=settings.SIMPLE_JWT["ISSUER"],
        options={"verify_aud": False},
    )

    assert claims["sub"] == str(usuario.id)
    assert claims["rol"] == Rol.ADMINISTRADOR
    assert Permiso.USUARIOS_ADMINISTRAR in claims["permisos"]


def test_un_token_firmado_con_otra_llave_no_pasa(client):
    from config.llaves import generar_llave_privada

    intruso = jwt.encode({"sub": "intruso"}, generar_llave_privada(), algorithm="RS256")
    publica = _llave_del_jwks(client.get(JWKS).json(), settings.JWT_KID)

    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(intruso, publica, algorithms=["RS256"])
