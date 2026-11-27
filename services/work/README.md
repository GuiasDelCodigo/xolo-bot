# Xolo Jobs API (`services/work`)

API REST independiente para buscar vacantes. No importa `discord.py` y no depende del bot para arrancar.

## Arquitectura

- `GET /jobs` y `GET /jobs/{offer_id}` leen la tabla `job_offers` de PostgreSQL.
- `POST /jobs/refresh` consulta JSearch en RapidAPI, normaliza los resultados y hace `upsert` en `job_offers`.
- La clave de JSearch se usa **solo** en el refresco; las búsquedas de RapidAPI no la necesitan.
- `GET /health` sirve para el balanceador/ALB y para comprobar la BD.

## Estructura

Todo el espacio de la API vive en `services/work` y tiene 10 archivos:

- `__init__.py`: exportaciones públicas del paquete.
- `models.py`: enums, tabla SQLAlchemy `job_offers` y contratos Pydantic.
- `storage.py`: engine async, sesiones, filtros, paginación y `upsert`.
- `jsearch.py`: cliente HTTP de JSearch y servicio de refresco.
- `api.py`: `Settings`, seguridad, dependencias, routers y `create_app`.
- `main.py`: entrypoint con uvicorn; carga `.env` antes de crear la app.
- `tests/test_api.py`: las 11 pruebas de la API.
- `requirements.txt`: dependencias propias de la API.
- `Dockerfile`: imagen de la API.
- `README.md`: esta guía.

Los módulos se reducen a 4 responsabilidades: `models.py` (datos), `storage.py` (BD), `jsearch.py` (fuente externa) y `api.py` (HTTP). Ese límite evita que la lógica se reparta entre muchas carpetas pequeñas.

## Configuración

Copia `.env.example` a `.env` en la raíz del repositorio. Nunca versiones `.env`.

Variables nuevas:

- `DATABASE_URL`: la misma que usa Alembic, `postgresql+psycopg://...`.
- `API_HOST` / `API_PORT`: por defecto `0.0.0.0:8000`.
- `JSEARCH_API_KEY`: clave de RapidAPI para JSearch. Se inyecta por entorno; no va en el código.
- `JSEARCH_API_HOST`: `jsearch.p.rapidapi.com`.
- `JSEARCH_TIMEOUT`: segundos por petición, por defecto `5.0`.
- `ENABLE_REFRESH`: `true` para exponer `POST /jobs/refresh`.
- `REFRESH_TOKEN`: token interno exigido en la cabecera `X-Refresh-Token`.
- `RAPIDAPI_KEY`: opcional; si se define, las rutas `/jobs` exigen `X-RapidAPI-Key`.
- `LOG_LEVEL`: `INFO` por defecto.

### Dónde poner la clave de JSearch

La clave real va **solo** en `.env` en la raíz del repositorio:

```powershell
cd "C:\Users\isacc\OneDrive\Desktop\PROYECTO JAVA\xolo-bot"
Copy-Item .env.example .env
notepad .env
```

Dentro de `.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://xolo:change_me@127.0.0.1:5432/xolo
JSEARCH_API_KEY=tu_nueva_clave_rotada
JSEARCH_API_HOST=jsearch.p.rapidapi.com
REFRESH_TOKEN=un_token_largo_local
```

No pegues la clave en `api.py`, `jsearch.py`, `.env.example`, Dockerfiles ni en el chat. `.env` está ignorado por Git. Rótala en RapidAPI antes de usarla porque la anterior quedó expuesta. `main.py:3` carga ese archivo y `api.py:69` lee `JSEARCH_API_KEY`; en Docker se pasa con `--env-file .env` y en AWS se inyecta desde Secrets Manager/SSM como variable de entorno.

## Arrancar

Desde la raíz del repositorio:

```powershell
pip install -r services\work\requirements.txt
docker compose -f services\db\docker-compose.yml up -d
$env:DATABASE_URL = "postgresql+psycopg://xolo:change_me@127.0.0.1:5432/xolo"
alembic -c services\db\alembic.ini upgrade head
python -m services.work.main
```

Documentación interactiva: `http://127.0.0.1:8000/docs`.

## Endpoints

- `GET /health`
- `GET /jobs?q=&category=&modality=&company=&source=&location=&min_salary=&max_salary=&limit=&offset=`
- `GET /jobs/{offer_id}`
- `POST /jobs/refresh` con cuerpo `{"query": "python trainee", "category": "DESARROLLO_SOFTWARE", "page": 1, "num_pages": 1}` y cabecera `X-Refresh-Token`.

Si JSearch falla, el endpoint ya no devuelve `500`: credencial rechazada → `502`, `429` de RapidAPI → `429`, servicio caído → `502`, cualquier otro error de JSearch → `502`.

## Pruebas

```powershell
python -m pytest services/work/tests -q
```

## Ejecución continua con Docker

Desde la raíz del repositorio (el contexto de build es `services`, no la raíz, para no meter `.env` en la imagen):

```powershell
docker build -f services\work\Dockerfile -t xolo-jobs-api services
docker run -d --name xolo-jobs-api --env-file .env -p 8000:8000 --restart unless-stopped xolo-jobs-api
```

La clave se pasa con `--env-file .env`; nunca se copia dentro de la imagen.

## AWS y Discord

- En AWS, la clave y `DATABASE_URL` se inyectan como variables de entorno desde Secrets Manager/SSM; la app no cambia.
- Para conectar Discord después, crear un cog que consulte esta API por HTTP o la misma BD. La API ya está aislada para que ese acoplamiento no rompa nada.
