"""Modelos del servicio access: departamentos, roles, usuarios, perfiles y activación.

La empresa no es un modelo. Cada empresa corre su propio stack con su propia
base de datos, así que la empresa es configuración del despliegue
(``settings.EMPRESA_ID``) y no una columna repetida en cada tabla.

Los identificadores de rol y de permiso son los mismos que declara
``contracts/access/openapi.yaml``: lo que viaja en el token es exactamente lo
que los demás equipos leen del contrato.
"""

import hashlib
import secrets
import uuid
from datetime import timedelta

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

    def registrar_intento_fallido(self, limite: int = 3) -> bool:
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


class ActivationToken(models.Model):
    """Enlace de un solo uso con el que alguien define su contraseña por primera vez.

    Lo usan tanto el administrador inicial (`/internal/v1/bootstrap-admin`) como
    los usuarios invitados. Del token solo se guarda el hash: el valor en claro
    existe una vez, viaja por correo y no se puede recuperar desde la base.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "core.Usuario",
        on_delete=models.CASCADE,
        related_name="activation_tokens",
    )
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "token de activación"
        verbose_name_plural = "tokens de activación"

    def __str__(self) -> str:
        return f"Activación de {self.user_id}"

    @staticmethod
    def hash_of(raw_token: str) -> str:
        """SHA-256 del token.

        Basta un hash rápido porque el token es aleatorio de 256 bits: no hay
        nada que adivinar por fuerza bruta, a diferencia de una contraseña.
        """
        return hashlib.sha256(raw_token.encode()).hexdigest()

    @classmethod
    def issue(cls, user, horas: int) -> tuple["ActivationToken", str]:
        """Emite un token nuevo y devuelve (registro, token en claro).

        Los tokens anteriores del usuario se invalidan: si se reenvía la
        invitación, el enlace viejo deja de servir.
        """
        cls.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
        raw = secrets.token_urlsafe(32)
        registro = cls.objects.create(
            user=user,
            token_hash=cls.hash_of(raw),
            expires_at=timezone.now() + timedelta(hours=horas),
        )
        return registro, raw

    @property
    def is_usable(self) -> bool:
        return self.used_at is None and self.expires_at > timezone.now()

    def consume(self) -> None:
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])


class OutboxMessage(models.Model):
    """Mensaje pendiente de publicar en el broker (patrón *outbox*).

    El evento se guarda en la **misma transacción** que el cambio que lo
    provocó, así nunca hay un login registrado sin su evento ni al revés. Un
    publicador posterior lee las filas sin `published_at` y las manda al broker.

    `id` es también la clave de idempotencia del sobre
    (`contracts/messages/event-envelope.json`): si el publicador reintenta, el
    consumidor reconoce el duplicado.
    """

    ORIGIN = "access"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=80)
    version = models.PositiveSmallIntegerField(default=1)
    occurred_at = models.DateTimeField()
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["published_at", "created_at"])]
        verbose_name = "mensaje de salida"
        verbose_name_plural = "mensajes de salida"

    def __str__(self) -> str:
        return f"{self.type} ({self.id})"

    def as_envelope(self, published_at=None) -> dict:
        """Sobre común que espera el equipo de Eventos.

        `timestamp` es cuándo se publica y `occurred_at` cuándo pasó el hecho:
        no son lo mismo, y un mensaje que esperó en la cola los tiene distintos.
        """
        momento = published_at or timezone.now()
        return {
            "id": str(self.id),
            "type": self.type,
            "version": self.version,
            "origin": self.ORIGIN,
            "timestamp": momento.isoformat(),
            "occurred_at": self.occurred_at.isoformat(),
            "payload": self.payload,
        }
