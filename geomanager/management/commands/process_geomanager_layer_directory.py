import glob
import logging
import os

from django.core.management.base import BaseCommand

from geomanager.settings import geomanager_settings
from geomanager.utils.ingest import is_valid_uuid, ingest_raster_file

logger = logging.getLogger(__name__)

ALLOWED_FILE_EVENTS = ["created", "moved"]


class Command(BaseCommand):
    help = 'Process a raster file layer directory'

    def add_arguments(self, parser):
        parser.add_argument('layer_id', type=str, help="Layer ID")
        parser.add_argument('--overwrite', action='store_true', default=False, help='Overwrite existing raster file')
        parser.add_argument('--clip', action='store_true', default=False, help='Clip raster to county boundary')

    def handle(self, *args, **options):
        layer_id = options['layer_id']
        overwrite = options['overwrite']
        clip = options['clip']

        auto_ingest_raster_data_dir = geomanager_settings.get("auto_ingest_raster_data_dir", None)

        if not auto_ingest_raster_data_dir:
            logger.error("Auto ingest raster data directory not configured.")
            return

        if not is_valid_uuid(layer_id):
            logger.error(f"Layer ID: {layer_id} is not a valid UUID.")
            return

        logger.debug('[GEOMANAGER_INGEST] Starting auto ingest execution...')

        directory = os.path.join(auto_ingest_raster_data_dir, layer_id)

        if not os.path.isdir(directory):
            logger.error(f"Directory: {directory} does not exist.")
            return

        geotiff_files = glob.glob(directory + "/*.tif")

        if not geotiff_files:
            logger.error(f"No GeoTIFF files found in directory: {directory}")
            return

        for file in geotiff_files:
            logger.info(f'[GEOMANAGER_INGEST] Processing file: {file}')
            ingest_raster_file(file, overwrite, clip)
