watchmedo shell-command --patterns="*.nc;*.tif" --ignore-directories --recursive \
  --command='python manage.py ingest_geomanager_raster "${watch_event_type}" "${watch_src_path}" --dst "${watch_dest_path}" --overwrite' \
  /path/to/direcory/to/watch
