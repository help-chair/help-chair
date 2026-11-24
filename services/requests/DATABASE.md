# Base de datos de Requests

El servicio de Peticiones utiliza **PostgreSQL** como base de datos principal (`postgres:16-alpine`).

Cada servicio de Help Chair maneja su propia base de datos aislada (`database per service`), por lo que Requests no comparte directamente sus tablas ni llaves foráneas con otros servicios.

## Configuración local

- Puerto local de aplicación: `8003`
- Puerto local de PostgreSQL: `5443`
- Variable de entorno: `DATABASE_URL=postgres://requests:requests@localhost:5443/requests`

Para levantar solo la base de datos de este servicio desde `services/requests/`:

```bash
podman compose up -d
```

Si `DATABASE_URL` no está definida, Django usa SQLite local para ejecutar pruebas rápidas (`pytest`).
