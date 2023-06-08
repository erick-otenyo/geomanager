from django.apps import AppConfig
from django.db import connection
from django.db.utils import OperationalError

from .settings import geomanager_settings


class GeomanagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'geomanager'

    def ready(self):
        vector_db_schema = geomanager_settings.get("vector_db_schema")
        ensure_pg_service_schema_exists(vector_db_schema)


def ensure_pg_service_schema_exists(schema):
    if schema is not None:
        with connection.cursor() as cursor:
            try:
                schema_sql = f"""DO
                                    $do$
                                    BEGIN
                                        CREATE EXTENSION IF NOT EXISTS postgis;
                                        CREATE SCHEMA IF NOT EXISTS {schema};
                                    END
                                    $do$;"""
                cursor.execute(schema_sql)
            except OperationalError:
                # If the schema already exists, do nothing
                pass
