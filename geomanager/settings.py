from django.conf import settings

SETTINGS = getattr(settings, "GEOMANAGER_SETTINGS", {})

geomanager_settings = {
    "vector_db_schema": SETTINGS.get("VECTOR_DB_SCHEMA", "vectordata")
}
