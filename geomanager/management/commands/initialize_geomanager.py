import logging

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError

from geomanager.settings import geomanager_settings

logger = logging.getLogger(__name__)


def ensure_pg_service_schema_exists(schema):
    if schema is not None:
        with connection.cursor() as cursor:
            try:
                schema_sql = f"""DO
                                    $do$
                                    BEGIN
                                        CREATE SCHEMA IF NOT EXISTS {schema};
                                    END
                                    $do$;"""
                cursor.execute(schema_sql)
            except OperationalError:
                # If the schema already exists, do nothing
                pass


class Command(BaseCommand):
    help = "Initialize GeoManager Vector Database Schema"

    def handle(self, *args, **options):
        # Create GeoManager vector database schema
        logger.info('[GEOMANAGER]: Creating GeoManager vector database schema...')

        vector_db_schema = geomanager_settings.get("vector_db_schema")

        ensure_pg_service_schema_exists(vector_db_schema)

        logger.info('[GEOMANAGER]: GeoManager vector database schema created.')
