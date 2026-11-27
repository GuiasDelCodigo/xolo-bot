# `services/db` (PostgreSQL + Redis + Alembic)

Infraestructura local de datos para desarrollo y migraciones centralizadas.

## Requisitos

- Docker Desktop en ejecución.
- Archivo `services/db/.env` creado a partir de `.env.example`.

## Levantar los contenedores

Desde la raíz del repositorio:

```powershell
docker compose -f services/db/docker-compose.yml up -d
```

Ver estado y salud:

```powershell
docker compose -f services/db/docker-compose.yml ps
```

Ver logs:

```powershell
docker compose -f services/db/docker-compose.yml logs -f db
docker compose -f services/db/docker-compose.yml logs -f redis
```

Detener (conserva datos):

```powershell
docker compose -f services/db/docker-compose.yml down
```

Detener y borrar volúmenes/datos locales (**destructivo**):

```powershell
docker compose -f services/db/docker-compose.yml down -v
```

## Migraciones (Alembic)

Alembic lee `DATABASE_URL` del entorno de la terminal (no carga `.env` automáticamente). En PowerShell:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://xolo:change_me@127.0.0.1:5432/xolo"
.\.venv\Scripts\alembic.exe -c services\db\alembic.ini upgrade head
.\.venv\Scripts\alembic.exe -c services\db\alembic.ini current
```

(Ajusta la URL si cambiaste usuario, contraseña o base en `.env`.)

## Notas

- Usa imágenes oficiales `postgres:17` y `redis:7` (no se construye una imagen propia para la base de datos).
- Las migraciones modifican el esquema/datos dentro del volumen `pgdata`; no requieren reconstruir ni recrear la imagen/contenedor de Postgres.
- `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_DB` solo se aplican al inicializar un volumen vacío. Si los cambias después, actualiza también `DATABASE_URL` y, en desarrollo local, suele ser necesario recrear con `down -v` (borra datos) o cambiar credenciales manualmente.
- La revisión `v3_job_offers_sync` agrega `url_hash`, `published_at` y `synced_at` a `job_offers` para deduplicar los refrescos de JSearch. Es obligatoria para `services/work`; `alembic upgrade head` aplica v1, v2 y v3. En AWS se ejecuta el mismo comando contra el endpoint privado de RDS.
