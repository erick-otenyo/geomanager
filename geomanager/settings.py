from django.conf import settings

DEFAULT_NC_TIME_DIMENSION_NAMES = [
    "time",
    "TIME",
    "XTIME",
    "xtime",
]

EXTRA_NC_TIME_DIMENSION_NAMES = getattr(settings, "GEOMANAGER_EXTRA_NC_TIME_DIMENSION_NAMES", [])

NC_TIME_DIMENSION_NAMES = DEFAULT_NC_TIME_DIMENSION_NAMES + EXTRA_NC_TIME_DIMENSION_NAMES

geomanager_settings = {
    "vector_db_schema": getattr(settings, "GEOMANAGER_VECTOR_DB_SCHEMA", "vectordata"),
    "auto_ingest_raster_data_dir": getattr(settings, "GEOMANAGER_AUTO_INGEST_RASTER_DATA_DIR", None),
    "nc_time_dimension_names": NC_TIME_DIMENSION_NAMES,
}
