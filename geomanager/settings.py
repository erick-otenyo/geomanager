from django.conf import settings

geomanager_settings = {
    "vector_db_schema": getattr(settings, "GEOMANAGER_VECTOR_DB_SCHEMA", "vectordata"),
    "auto_ingest_raster_data_dir": getattr(settings, "GEOMANAGER_AUTO_INGEST_RASTER_DATA_DIR", None)
}
