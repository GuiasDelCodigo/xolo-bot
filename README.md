# 🐕 xoloBot 

> El guía oficial de nuestra comunidad Guias del Código. Este bot está diseñado para guiar a los miembros, mantener el orden en el servidor y automatizar tareas clave de la comunidad.

## 🚀 Características Principales

XoloBot

*   🎵 **Music:** Sistema de música integrado para armar playlists colectivas durante las sesiones de *Pair Programming* o estudio.
*   🛡️ **Moderación:** Escaneo de mensajes sospechosos, filtrado de spam y sistema automático de advertencias (`warns`).
*   💼 **Cazador de Vacantes:** Un *scraper* automatizado que busca puestos de trabajo para **Interns** y **Trainees** en el sector tecnológico y los publica en el canal correspondiente.
*   🐙 **Notificador de GitHub (Webhooks):** Conexión directa con nuestro repositorio. El bot celebrará y notificará en tiempo real cada vez que un Pull Request sea aprobado o mergeado. ¡Tu código merece ser reconocido!

## 🛠️ Tecnologías y Librerías

El corazón de xoloBot está construido con el siguiente stack:

*   **Entorno:** [Python](https://www.python.org/) (v3.12)
*   **Librería Principal:** [discord.py (v2.7)](https://discordpy.readthedocs.io/)
*   **Base de datos:** PostgreSQL 17, SQLAlchemy 2.0 y `psycopg[binary]`
*   **Migraciones:** Alembic con SQL, centralizado en `services/db`

## 📦 Instalación y Configuración

Sigue estos pasos para clonar el proyecto y correr a xoloBot de forma local:

### 1. Clonar el repositorio
```bash
git clone [https://github.com/TU_USUARIO/xoloBot.git](https://github.com/TU_USUARIO/xoloBot.git)
cd xoloBot
```

## API de empleos (RapidAPI)

`services/work` contiene una API FastAPI independiente del bot:

- `GET /jobs`: busca y filtra vacantes guardadas en `job_offers`.
- `GET /jobs/{offer_id}`: detalle de una vacante.
- `POST /jobs/refresh`: consulta JSearch y actualiza la BD; protegido con `X-Refresh-Token`.
- `GET /health`: chequeo para RapidAPI y para un balanceador en AWS.

Ver `services/work/README.md` para variables de entorno, comandos y despliegue.

## Comandos de Discord para vacantes

El cog `services/core/app/cogs/jobs.py` publica ofertas en un canal fijo configurado con `DISCORD_JOBS_CHANNEL_ID`:

- `/ofertas`: muestra las vacantes guardadas; si no hay ninguna, consulta JSearch y guarda antes de publicar.
- `/ofertas_recientes`: consulta JSearch siempre, guarda las ofertas y publica el resultado.

Ambos publican un único embed con hasta `JOBS_EMBED_LIMIT` ofertas (5 por defecto). Requieren la API levantada en `JOBS_API_BASE_URL` (`http://127.0.0.1:8000` por defecto) y `REFRESH_TOKEN` en `.env`.

Para probar en local, levantar la API y el bot en terminales distintas:

```bash
python -m services.work.main
python -m services.core.app.main
```
