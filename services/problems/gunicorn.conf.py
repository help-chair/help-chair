"""Una configuración de servidor para la imagen y los comandos de Compose."""

from config.environment import positive_integer
from config.logging import logging_config

bind = f"0.0.0.0:{positive_integer('PORT', 8005, 65535)}"
workers = positive_integer("WEB_CONCURRENCY", 2)
graceful_timeout = positive_integer("GRACEFUL_TIMEOUT", 30)
accesslog = "-"
errorlog = "-"
# No registrar URL, query, cookies, cabeceras o cuerpos de peticiones.
access_log_format = "%(m)s %(s)s %(L)s"
logconfig_dict = logging_config()
