def create_stations_geomanager_dataset(station_settings, request=None):
    sub_category = station_settings.geomanager_subcategory

    if not sub_category:
        return None

    title = station_settings.layer_title
    metadata = station_settings.geomanager_layer_metadata
    popup_fields = station_settings.station_popup_columns_list

    dataset_id = "country_stations"

    dataset = {
        "id": dataset_id,
        "dataset": dataset_id,
        "name": title,
        "layer": dataset_id,
        "category": sub_category.category.pk,
        "sub_category": sub_category.pk,
        "public": True,
        "layers": [

        ]
    }
    if metadata:
        dataset.update({"metadata": metadata.pk})

    station_tiles_url = station_settings.stations_vector_tiles_url

    if request:
        station_tiles_url = request.scheme + '://' + request.get_host() + station_tiles_url

    layer = {
        "id": dataset_id,
        "name": title,
        "layerConfig": {
            "type": "vector",
            "source": {
                "type": "vector",
                "tiles": [station_tiles_url],
            },
            "render": {
                "layers": [
                    {
                        "type": "circle",
                        "source-layer": "default",
                        'paint': {
                            "circle-color": "#adefd1",
                            "circle-radius": 8,
                            "circle-stroke-width": 4,
                            "circle-stroke-color": "#00203F",
                        }}
                ]
            }
        },
        "legendConfig": {}
    }

    if popup_fields:
        interactionConfig = {
            "output": []
        }
        for field in popup_fields:
            interactionConfig["output"].append({
                "column": field.get("name"),
                "property": field.get("label"),
                "type": "string"
            })

        layer.update({"interactionConfig": interactionConfig})

    dataset["layers"].append(layer)

    return dataset
