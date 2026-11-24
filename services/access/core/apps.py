from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        # SimpleJWT no escribe el `kid` en la cabecera del token y sin él los
        # demás servicios no saben qué llave del JWKS aplicar. Se instala aquí
        # porque toca a SimpleJWT, que no puede importarse desde settings.
        from django.conf import settings

        from config.llaves import instalar_kid_en_la_cabecera

        instalar_kid_en_la_cabecera(settings.JWT_KID)
