def create_boundary_dataset(tiles_url):
    dataset_id = "political-boundaries"
    name = "Political Boundaries"
    source_layer = "default"

    dataset = {
        "id": dataset_id,
        "dataset": dataset_id,
        "name": name,
        "layer": dataset_id,
        "isBoundary": True,
        "public": True,
        "layers": []
    }

    layer = {
        "id": dataset_id,
        "isBoundary": True,
        "analysisEndpoint": "admin",
        "name": name,
        "default": True,
        "layerConfig": {
            "type": "vector",
            "source": {
                "type": "vector",
                "tiles": [tiles_url],
            },
            "render": {
                "layers": [
                    {
                        "filter": ["==", "level", 0],
                        "maxzoom": 3,
                        "paint": {
                            "fill-color": "#ffffff",
                            "fill-opacity": 0,
                        },
                        "source-layer": source_layer,
                        "type": "fill",
                    },
                    {
                        "filter": ["==", "level", 1],
                        "maxzoom": 6,
                        "minzoom": 3,
                        "paint": {
                            "fill-color": "#ffffff",
                            "fill-opacity": 0,
                        },
                        "source-layer": source_layer,
                        "type": "fill",
                    },
                    {
                        "filter": ["==", "level", 2],
                        "minzoom": 6,
                        "paint": {
                            "fill-color": "#ffffff",
                            "fill-opacity": 0,
                        },
                        "source-layer": source_layer,
                        "type": "fill",
                    },
                    {
                        "filter": ["==", "level", 0],
                        "paint": {
                            "line-color": "#C0FF24",
                            "line-width": 1,
                            "line-offset": 1,
                        },
                        "source-layer": source_layer,
                        "type": "line",
                    },
                    {
                        "filter": ["==", "level", 0],
                        "paint": {
                            "line-color": "#000",
                            "line-width": 1.5,
                        },
                        "source-layer": source_layer,
                        "type": "line",
                    },
                    {
                        "filter": ["==", "level", 1],
                        "maxzoom": 6,
                        "minzoom": 3,
                        "paint": {
                            "line-color": "#8b8b8b",
                            "line-width": 1,
                        },
                        "source-layer": source_layer,
                        "type": "line",
                    },
                    {
                        "filter": ["==", "level", 2],
                        "minzoom": 6,
                        "paint": {
                            "line-color": "#444444",
                            "line-dasharray": [2, 4],
                            "line-width": 0.7,
                        },
                        "source-layer": source_layer,
                        "type": "line",
                    },
                ],
            },
        },
        "interactionConfig": {
            "output": [
                {
                    "column": "gid_0",
                    "property": "ISO",
                    'type': "string",
                },
                {
                    "column": "gid_1",

                    "property": "admin1",
                    "type": "string",
                },
                {
                    "column": "gid_2",
                    "property": "admin2",
                    "type": "string",
                },
                {
                    "column": "name_0",
                    "property": "Country",
                    "type": "string",
                },
                {
                    "column": "name_1",
                    "property": "Region",
                    "type": "string",
                },
                {
                    "column": "name_2",
                    "property": "Sub Region",
                    "type": "string",
                },
                {
                    "column": "level",
                    "property": "Admin Level",
                    "type": "number",
                },
                {
                    "column": "area",
                    "format": "0a",
                    "property": "Area",
                    "suffix": "ha",
                    "type": "number",
                },
                {
                    "column": "gid",
                    "hidden": True,
                    "property": "gid",
                    "type": "number",
                },
            ],
            "type": "intersection",
        },
    }

    dataset["layers"].append(layer)

    return dataset
