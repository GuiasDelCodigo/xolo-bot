import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Objeto de configuración de Alembic (lee alembic.ini).
config = context.config

# Configura el logging según alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# La URL se toma del entorno; no se hardcodea en alembic.ini ni en el repo.
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError(
        "DATABASE_URL no está definida. "
        "Ejemplo: postgresql+psycopg://xolo:change_me@127.0.0.1:5432/xolo"
    )
config.set_main_option("sqlalchemy.url", database_url)

# Sin autogenerate: el SQL se escribe a mano en las revisiones.
target_metadata = None


def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo 'offline' (genera SQL sin conectar)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="public",
        include_schemas=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta migraciones en modo 'online' (conecta a la BD)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="public",
            include_schemas=True,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
