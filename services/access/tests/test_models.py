"""Pruebas de los modelos: departamento, rol, usuario y perfil."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from core.models import Departamento, EstadoUsuario, Perfil, Permiso, Rol

CLAVE = "clave-de-prueba-123"
Usuario = get_user_model()


@pytest.fixture
def rol_administrador(db):
    return Rol.objects.create(
        id=Rol.ADMINISTRADOR,
        nombre="Administrador",
        permisos=[Permiso.USUARIOS_ADMINISTRAR, Permiso.EMPRESA_CONFIGURAR],
    )


@pytest.mark.django_db
def test_el_departamento_se_muestra_por_su_nombre():
    departamento = Departamento.objects.create(nombre="Sistemas")

    assert str(departamento) == "Sistemas"


@pytest.mark.django_db
def test_no_se_repiten_los_nombres_de_departamento():
    Departamento.objects.create(nombre="Sistemas")

    with pytest.raises(IntegrityError):
        Departamento.objects.create(nombre="Sistemas")


@pytest.mark.django_db
def test_el_rol_sabe_que_permisos_tiene(rol_administrador):
    assert rol_administrador.tiene_permiso(Permiso.USUARIOS_ADMINISTRAR)
    assert not rol_administrador.tiene_permiso(Permiso.TICKETS_ESCALAR)


@pytest.mark.django_db
def test_un_usuario_con_contrasena_queda_activo():
    usuario = Usuario.objects.create_user(correo="ana@empresa-demo.mx", password=CLAVE)

    assert usuario.estado == EstadoUsuario.ACTIVO
    assert usuario.is_active


@pytest.mark.django_db
def test_un_usuario_sin_contrasena_queda_invitado():
    usuario = Usuario.objects.create_user(correo="nuevo@empresa-demo.mx")

    assert usuario.estado == EstadoUsuario.INVITADO
    assert not usuario.is_active


@pytest.mark.django_db
def test_el_correo_es_obligatorio():
    with pytest.raises(ValueError):
        Usuario.objects.create_user(correo="", password=CLAVE)


@pytest.mark.django_db
def test_no_se_repiten_los_correos():
    Usuario.objects.create_user(correo="ana@empresa-demo.mx", password=CLAVE)

    with pytest.raises(IntegrityError):
        Usuario.objects.create_user(correo="ana@empresa-demo.mx", password=CLAVE)


@pytest.mark.django_db
def test_los_permisos_del_usuario_vienen_de_su_rol(rol_administrador):
    usuario = Usuario.objects.create_user(
        correo="jefa@empresa-demo.mx", password=CLAVE, rol=rol_administrador
    )

    assert usuario.tiene_permiso(Permiso.USUARIOS_ADMINISTRAR)
    assert not usuario.tiene_permiso(Permiso.TICKETS_ESCALAR)


@pytest.mark.django_db
def test_un_usuario_sin_rol_no_tiene_permisos():
    usuario = Usuario.objects.create_user(correo="ana@empresa-demo.mx", password=CLAVE)

    assert usuario.permisos == []


@pytest.mark.django_db
def test_la_cuenta_se_bloquea_al_quinto_intento_fallido():
    usuario = Usuario.objects.create_user(correo="ana@empresa-demo.mx", password=CLAVE)

    bloqueos = [usuario.registrar_intento_fallido(limite=5) for _ in range(5)]

    assert bloqueos == [False, False, False, False, True]
    assert usuario.estado == EstadoUsuario.BLOQUEADO
    assert not usuario.is_active


@pytest.mark.django_db
def test_desbloquear_deja_entrar_de_nuevo():
    usuario = Usuario.objects.create_user(correo="ana@empresa-demo.mx", password=CLAVE)
    for _ in range(5):
        usuario.registrar_intento_fallido(limite=5)

    usuario.desbloquear()

    assert usuario.estado == EstadoUsuario.ACTIVO
    assert usuario.intentos_fallidos == 0
    assert usuario.is_active


@pytest.mark.django_db
def test_el_superusuario_queda_activo_y_con_acceso_al_admin():
    usuario = Usuario.objects.create_superuser(correo="admin@empresa-demo.mx", password=CLAVE)

    assert usuario.is_staff
    assert usuario.is_superuser
    assert usuario.estado == EstadoUsuario.ACTIVO


@pytest.mark.django_db
def test_el_perfil_pertenece_a_un_usuario():
    usuario = Usuario.objects.create_user(correo="ana@empresa-demo.mx", password=CLAVE)

    perfil = Perfil.objects.create(usuario=usuario, puesto="Analista")

    assert usuario.perfil == perfil
    assert not perfil.onboarding_completado
    assert str(perfil) == "Perfil de ana@empresa-demo.mx"


@pytest.mark.django_db
def test_el_usuario_puede_pertenecer_a_un_departamento():
    departamento = Departamento.objects.create(nombre="Sistemas")

    usuario = Usuario.objects.create_user(
        correo="ana@empresa-demo.mx", password=CLAVE, departamento=departamento
    )

    assert usuario.departamento == departamento
    assert list(departamento.usuarios.all()) == [usuario]
