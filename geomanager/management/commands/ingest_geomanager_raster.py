import logging

from django.core.management.base import BaseCommand

from geomanager.utils.ingest import ingest_raster_file

logger = logging.getLogger(__name__)

ALLOWED_FILE_EVENTS = ["created", "moved"]


class Command(BaseCommand):
    help = 'Ingest single geotiff file to raster file'

    def add_arguments(self, parser):
        parser.add_argument('event_type', type=str, help='WatchDog File Event type')
        parser.add_argument('src', type=str, help='File source path')
        parser.add_argument('--dst', type=str, help='File destination path for moved events')
        parser.add_argument('--overwrite', action='store_true', default=False, help='Overwrite existing raster file')
        parser.add_argument('--clip', action='store_true', default=False, help='Clip raster to county boundary')

    def handle(self, *args, **options):
        event_type = options['event_type']
        src_path = options['src']
        dst_path = options['dst']
        overwrite = options['overwrite']
        clip = options['clip']

        logger.info('[GEOMANAGER_AUTO_INGEST]: Starting auto ingest execution...')

        logger.info(f'[GEOMANAGER_AUTO_INGEST]: Event Type: {event_type}')

        # Check if event type is allowed
        if event_type not in ALLOWED_FILE_EVENTS:
            logger.warning(f'[GEOMANAGER_AUTO_INGEST]: Event Type: {event_type} not in allowed file events.')
            return

        # If event type is moved, use destination path
        if event_type == "moved" and dst_path is not None:
            src_path = dst_path

        ingest_raster_file(src_path, overwrite, clip)

        logger.info(f'[GEOMANAGER_AUTO_INGEST]: {src_path} done...')
