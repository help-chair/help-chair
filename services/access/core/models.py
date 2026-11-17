"""Modelos del servicio access: departamentos, roles, usuarios y perfiles.

La empresa no es un modelo. Cada empresa corre su propio stack con su propia
base de datos, así que la empresa es configuración del despliegue
(``settings.EMPRESA_ID``) y no una columna repetida en cada tabla.

Los identificadores de rol y de permiso son los mismos que declara
``contracts/access/openapi.yaml``: lo que viaja en el token es exactamente lo
que los demás equipos leen del contrato.
"""

import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


class Permiso(models.TextChoices):
    """Permisos efectivos de un rol. El frontend dibuja la navegación con esto."""

    TICKETS_VER = "tickets:ver", "Ver tickets"
    TICKETS_ATENDER = "tickets:atender", "Atender tickets"
    TICKETS_ESCALAR = "tickets:escalar", "Escalar tickets"
    EMPRESA_CONFIGURAR = "empresa:configurar", "Configurar la empresa"
    USUARIOS_ADMINISTRAR = "usuarios:administrar", "Administrar usuarios"


class EstadoUsuario(models.TextChoices):
    ACTIVO = "activo", "Activo"
    INVITADO = "invitado", "Invitado"
    BLOQUEADO = "bloqueado", "Bloqueado"
    SUSPENDIDO = "suspendido", "Suspendido"


class Departamento(models.Model):
    """Área de la empresa a la que pertenece un usuario."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "departamento"
        verbose_name_plural = "departamentos"

    def __str__(self) -> str:
        return self.nombre


class Rol(models.Model):
    """Catálogo de roles. Son fijos en la v1 y se cargan con ``make seed``.

    El identificador es el texto que viaja en el claim ``rol`` del token, por
    eso es la llave primaria y no un número.
    """

    ADMINISTRADOR = "administrador"
    AGENTE_N2 = "agente_n2"
    AGENTE_N1 = "agente_n1"
    USUARIO_FINAL = "usuario_final"

    id = models.SlugField(primary_key=True, max_length=30)
    nombre = models.CharField(max_length=60)
    descripcion = models.TextField(blank=True)
    permisos = models.JSONField(
        default=list,
        help_text="Lista de permisos del rol, con los valores de Permiso.",
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "rol"
        verbose_name_plural = "roles"

    def __str__(self) -> str:
        return self.nombre or self.id

    def tiene_permiso(self, permiso: str) -> bool:
        return permiso in (self.permisos or [])


class UsuarioManager(BaseUserManager):
    """Crea usuarios identificados por su correo.

    Un usuario creado sin contraseña queda ``invitado``: existe, pero no puede
    entrar hasta que active su cuenta. Uno creado con contraseña queda activo.
    """

    use_in_migrations = True

    def create_user(self, correo, password=None, **extra):
        if not correo:
            raise ValueError("El usuario necesita un correo.")
        extra.setdefault(
            "estado",
            EstadoUsuario.ACTIVO if password else EstadoUsuario.INVITADO,
        )
        usuario = self.model(correo=self.normalize_email(correo), **extra)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, correo, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("estado", EstadoUsuario.ACTIVO)
        if extra.get("is_staff") is not True:
            raise ValueError("Un superusuario debe tener is_staff=True.")
        if extra.get("is_superuser") is not True:
            raise ValueError("Un superusuario debe tener is_superuser=True.")
        return self.create_user(correo, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Persona que entra al help desk de esta empresa."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    correo = models.EmailField(unique=True)
    nombre = models.CharField(max_length=120, blank=True)
    rol = models.ForeignKey(
        Rol,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="usuarios",
    )
    departamento = models.ForeignKey(
        Departamento,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="usuarios",
    )
    estado = models.CharField(
        max_length=12,
        choices=EstadoUsuario.choices,
        default=EstadoUsuario.INVITADO,
    )
    intentos_fallidos = models.PositiveSmallIntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UsuarioManager()

    USERNAME_FIELD = "correo"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["correo"]
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self) -> str:
        return self.correo

    @property
    def is_active(self) -> bool:
        """Solo un usuario activo puede autenticarse.

        Django lo consulta al validar las credenciales, así que un invitado,
        un bloqueado o un suspendido no obtienen token.
        """
        return self.estado == EstadoUsuario.ACTIVO

    @property
    def permisos(self) -> list[str]:
        """Permisos efectivos del usuario, tomados de su rol."""
        return list(self.rol.permisos) if self.rol else []

    def tiene_permiso(self, permiso: str) -> bool:
        return permiso in self.permisos

    def registrar_intento_fallido(self, limite: int = 5) -> bool:
        """Suma un intento fallido y bloquea la cuenta al llegar al límite.

        Devuelve True si este intento provocó el bloqueo.
        """
        self.intentos_fallidos += 1
        if self.intentos_fallidos >= limite:
            self.estado = EstadoUsuario.BLOQUEADO
            self.save(update_fields=["intentos_fallidos", "estado"])
            return True
        self.save(update_fields=["intentos_fallidos"])
        return False

    def registrar_acceso(self) -> None:
        """Limpia el contador de intentos tras un inicio de sesión correcto."""
        if self.intentos_fallidos:
            self.intentos_fallidos = 0
            self.save(update_fields=["intentos_fallidos"])

    def desbloquear(self) -> None:
        self.intentos_fallidos = 0
        self.bloqueado_hasta = None
        self.estado = EstadoUsuario.ACTIVO
        self.save(update_fields=["intentos_fallidos", "bloqueado_hasta", "estado"])


class Perfil(models.Model):
    """Datos de la persona que no hacen falta para autenticarla."""

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="perfil",
        primary_key=True,
    )
    puesto = models.CharField(max_length=120, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    zona_horaria = models.CharField(max_length=60, default="America/Mexico_City")
    onboarding_completado = models.BooleanField(default=False)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "perfil"
        verbose_name_plural = "perfiles"

    def __str__(self) -> str:
        return f"Perfil de {self.usuario.correo}"
