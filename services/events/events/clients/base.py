"""Cliente HTTP base para los servicios destino (timeout, reintentos y JWT)."""

import logging
import threading
import time
from dataclasses import dataclass, field

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class DestinationError(Exception):
    """Falló la entrega. `retryable` indica si tiene sentido volver a intentarlo."""

    def __init__(self, message, *, retryable=False, status_code=None):
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code


class DestinationNotConfigured(DestinationError):
    """Falta una variable de entorno. Es recuperable: se corrige la config y se reintenta."""

    def __init__(self, message):
        super().__init__(message, retryable=True)


@dataclass(frozen=True)
class RemoteResult:
    remote_id: str
    raw: dict = field(default_factory=dict)


class ServiceTokenProvider:
    """JWT con el que Eventos llama a los demás servicios.

    - SERVICE_JWT: token fijo (pruebas o desarrollo).
    - Si no, inicia sesión en Accesos con SERVICE_ACCOUNT_EMAIL / SERVICE_ACCOUNT_PASSWORD
      y guarda el token hasta poco antes de que expire.
    """

    LOGIN_PATH = "/api/access/v1/login"

    def __init__(
        self,
        *,
        static_token="",
        access_url="",
        email="",
        password="",
        timeout=5.0,
        transport=None,
        clock=time.monotonic,
    ):
        self.static_token = static_token
        self.access_url = access_url.rstrip("/")
        self.email = email
        self.password = password
        self.timeout = timeout
        self.transport = transport
        self._clock = clock
        self._lock = threading.Lock()
        self._token = None
        self._expires_at = 0.0

    def get_token(self) -> str:
        if self.static_token:
            return self.static_token
        with self._lock:
            if self._token and self._clock() < self._expires_at - 30:
                return self._token
            self._token, ttl = self._login()
            self._expires_at = self._clock() + ttl
            return self._token

    def invalidate(self) -> None:
        with self._lock:
            self._token = None

    def _login(self):
        if not (self.access_url and self.email and self.password):
            raise DestinationNotConfigured(
                "Define SERVICE_JWT o ACCESS_URL + SERVICE_ACCOUNT_EMAIL + SERVICE_ACCOUNT_PASSWORD"
            )
        try:
            with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
                resp = client.post(
                    self.access_url + self.LOGIN_PATH,
                    json={"correo": self.email, "password": self.password},
                )
        except httpx.TransportError as exc:
            raise DestinationError(
                f"Login en Accesos: {type(exc).__name__}", retryable=True
            ) from exc
        if not resp.is_success:
            raise DestinationError(
                f"Login en Accesos: HTTP {resp.status_code}",
                retryable=resp.status_code >= 500,
                status_code=resp.status_code,
            )
        data = resp.json()
        return data["acceso"], float(data.get("expira_en", 300))


class BaseClient:
    destination = ""  # valor de events.models.Destination
    path = ""
    id_field = "id"

    def __init__(
        self,
        *,
        token_provider,
        base_url=None,
        timeout=None,
        retries=None,
        backoff=None,
        transport=None,
        sleep=time.sleep,
    ):
        urls = getattr(settings, "DESTINATION_URLS", {})
        self.base_url = (
            base_url if base_url is not None else urls.get(self.destination, "")
        ).rstrip("/")
        self.timeout = timeout if timeout is not None else settings.DESTINATION_TIMEOUT
        self.retries = retries if retries is not None else settings.DESTINATION_RETRIES
        self.backoff = backoff if backoff is not None else settings.DESTINATION_BACKOFF
        self.tokens = token_provider
        self.transport = transport
        self.sleep = sleep

    def build_payload(self, event, rule_code: str) -> dict:
        raise NotImplementedError

    def create(self, event, *, rule_code: str) -> RemoteResult:
        payload = self.build_payload(event, rule_code)
        resp = self._post(payload, idempotency_key=str(event.pk))
        try:
            data = resp.json()
        except ValueError:
            raise DestinationError(
                "La respuesta no es JSON", status_code=resp.status_code
            ) from None
        remote_id = data.get(self.id_field) if isinstance(data, dict) else None
        if remote_id in (None, ""):
            raise DestinationError(
                "La respuesta no incluye el ID remoto", status_code=resp.status_code
            )
        return RemoteResult(remote_id=str(remote_id), raw=data)

    def _post(self, payload, *, idempotency_key):
        if not self.base_url:
            raise DestinationNotConfigured(
                f"Falta la URL de {self.destination} (variable de entorno)"
            )
        url = self.base_url + self.path
        attempt = 0
        auth_retried = False
        while True:
            attempt += 1
            headers = {
                "Authorization": f"Bearer {self.tokens.get_token()}",
                "Idempotency-Key": idempotency_key,
                "Accept": "application/json",
            }
            try:
                with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
                    resp = client.post(url, json=payload, headers=headers)
            except httpx.TransportError as exc:
                error = DestinationError(f"{type(exc).__name__}: {exc}", retryable=True)
            else:
                if resp.is_success:
                    return resp
                if resp.status_code == 401 and not auth_retried:
                    auth_retried = True
                    self.tokens.invalidate()  # el token pudo expirar: se pide uno nuevo
                    continue
                error = DestinationError(
                    f"HTTP {resp.status_code}: {resp.text[:200]}",
                    retryable=resp.status_code >= 500 or resp.status_code == 429,
                    status_code=resp.status_code,
                )
            if not error.retryable or attempt > self.retries:
                raise error
            logger.warning(
                "destination_retry",
                extra={"destination": self.destination, "attempt": attempt, "error": str(error)},
            )
            self.sleep(self.backoff * 2 ** (attempt - 1))
