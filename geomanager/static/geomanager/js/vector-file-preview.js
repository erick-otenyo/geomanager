$((async function () {
    // default map style
    const defaultStyle = {
        version: 8,
        sources: {
            "carto-light": {
                type: "raster",
                tiles: [
                    "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                    "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                    "https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                    "https://d.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                ],
            },
            wikimedia: {
                type: "raster",
                tiles: ["https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png"],
            },
        },
        layers: [
            {
                id: "carto-light-layer",
                source: "carto-light",
                type: "raster",
                minzoom: 0,
                maxzoom: 22,
            },
        ],
    };


    const mapColor = "blue";

    const paints = {
        "circle": {
            "circle-color": mapColor,
            "circle-radius": 3
        },
        "line": {
            "line-color": mapColor,
            "line-width": 1.5
        },
        "fill": {
            "fill-color": mapColor,
            "fill-outline-color": mapColor,
            "fill-opacity": 0.1
        }
    };

    const paintTypes = {
        "Point": "circle",
        "MultiPoint": "circle",
        "LineString": "line",
        "MultiLineString": "line",
        "Polygon": "fill",
        "MultiPolygon": "fill",
    };

    function getLayerSource(tileUrl) {
        return {
            "type": "vector",
            "tiles": [tileUrl],
        }
    }

    function getLayerId(id, gtype, paint) {
        return id + "." + gtype + "." + paint;
    }

    function getLayerConfig(id, gtype, paint) {
        return {
            "id": getLayerId(id, gtype, paint),
            "source": id,
            "source-layer": "default",
            "type": paint,
            "paint": paints[paint],
            "filter": ["match", ["geometry-type"], [gtype, "Multi" + gtype], true, false]
        }
    }

    function featureHtml(f) {
        const p = f.properties;
        let h = "<p>";
        for (let k in p) {
            if (k !== "geom") {
                h += "<b>" + k + ":</b> " + p[k] + "<br/>"
            }
        }
        h += "</p>";
        return h
    }

    function addLayerBehavior(id) {
        map.on('click', id, function (e) {
            new maplibregl.Popup()
                .setLngLat(e.lngLat)
                .setHTML(featureHtml(e.features[0]))
                .addTo(map);
        });


        map.on('mouseenter', id, function () {
            map.getCanvas().style.cursor = 'pointer';
        });


        map.on('mouseleave', id, function () {
            map.getCanvas().style.cursor = '';
        });
    }

    function addOneLayer(id, gtypeBasic) {
        map.addLayer(getLayerConfig(id, gtypeBasic, paintTypes[gtypeBasic]));
        addLayerBehavior(getLayerId(id, gtypeBasic, paintTypes[gtypeBasic]));

        if (gtypeBasic === "Polygon") {
            map.addLayer(getLayerConfig(id, gtypeBasic, "line"));
        }
    }

    function addLayers(id, gtype, tileUrl) {
        map.addSource(id, getLayerSource(tileUrl));
        const gtypeBasic = gtype.replace("Multi", "");
        const gTypes = ["Point", "LineString", "Polygon"];

        if (gTypes.includes(gtypeBasic)) {
            addOneLayer(id, gtypeBasic);
        } else {
            gTypes.forEach(gt => {
                addOneLayer(id, gt);
            });
        }

    }

    // initialize map
    const map = new maplibregl.Map({
        container: "preview-map",
        style: defaultStyle,
        center: [0, 0],
        zoom: 2,
        attributionControl: true,
    });

    // add navigation control. Zoom in,out
    const navControl = new maplibregl.NavigationControl({
        showCompass: false
    })

    map.addControl(navControl, 'bottom-right')

    // wait for map to load
    await new Promise((resolve) => map.on("load", resolve));

    // load icon images
    const iconImages = window.geomanager_opts.iconImages


    if (iconImages) {
        iconImages.forEach(iconImage => {
            map.loadImage(iconImage.url, (error, image) => {
                if (error) throw error;
                // Add the image to the map style.
                map.addImage(iconImage.name, image);
            })
        })
    }

    // map layer id. Also used as source id
    const mapVectorLayerId = "vectorLayer"

    let vectorTables = []

    /**
     * Fetches the vector tables for a layer from the vector API endpoint.
     * @param {string} layerId - The ID of the layer to fetch files for.
     * @returns {Promise} A promise that resolves to the JSON response from the raster API endpoint.
     */
    const fetchVectorTables = (layerId) => {
        const vectorsUrl = `${window.geomanager_opts.dataVectorApiBaseUrl}?layer=${layerId}`
        return fetch(vectorsUrl).then(res => res.json())
    }

    // layer selection and change event
    const $layerSelect = $('#layer_select')
    $layerSelect.on("change", (e) => {
        const selectedLayerId = e.target.value;
        setVectorTables(selectedLayerId);
    })

    // vector data selection and change event
    const $vectorTableSelect = $('#vector_table_select')
    $vectorTableSelect.on("change", (e) => {
        const selectedTable = e.target.value;
        onVectorTableChange(selectedTable, map, mapVectorLayerId);
    })

    const updateTileUrl = (tileUrl, params) => {
        // construct new url with new query params
        const url = new URL(tileUrl)
        const qs = new URLSearchParams(url.search);
        Object.keys(params).forEach(key => {
            qs.set(key, params[key])
        })
        url.search = decodeURIComponent(qs);
        return decodeURIComponent(url.href)
    }


    /**
     * Updates the source tiles of a map to show data for a specific table.
     * @param {string} selectedTable - The table to show data for
     * @param {object} map - The Mapbox GL JS map object to update.
     * @param {string} sourceId - The ID of the map source to update.
     */
    const onVectorTableChange = (selectedTable, map, sourceId) => {
        if (selectedTable && map && sourceId) {
            const selectedLayer = $layerSelect.val();
            setLayer(selectedLayer)
        }
    };

    const setLayer = async (layerId) => {
        const selectedVectorTable = $vectorTableSelect.val()
        const vectorTable = vectorTables.find(v => v.table_name === selectedVectorTable) || {}
        let {geometry_type, bounds} = vectorTable


        if (layerId) {


            const selectedLayer = window.geomanager_opts.datasetLayers.find(l => l.id === layerId)


            if (selectedLayer) {
                const {id, layerConfig: {source: {tiles}, render}} = selectedLayer

                if (render && render.layers && !!render.layers.length) {

                    render.layers.forEach((layer, index) => {

                        const layerId = `${id}-${layer.type}-${index}`

                        // Check if the layer exists and remove it if it does
                        if (map.getLayer(layerId)) {
                            map.removeLayer(layerId);
                        }

                        // Check if the source exists and remove it if it does
                        if (map.getSource(layerId)) {
                            map.removeSource(layerId);
                        }
                        const url_params = {
                            layer: layerId,
                            table_name: selectedVectorTable,
                        }

                        const tileUrl = updateTileUrl(window.geomanager_opts.vectorTilesUrl, url_params)

                        map.addSource(layerId, {
                            type: "vector",
                            tiles: [tileUrl],
                        });

                        map.addLayer({
                            id: layerId,
                            source: layerId,
                            "source-layer": "default",
                            ...layer
                        });

                        if (geometry_type && selectedVectorTable) {
                            if (bounds) {
                                map.fitBounds(bounds, {padding: 20})
                            }
                        }
                    })
                }
            }
        }
    }

    const setVectorTables = async (layerId) => {
        $vectorTableSelect.empty();

        vectorTables = await fetchVectorTables(layerId)
        $.each(vectorTables, function (index, rasterFile) {
            const optionEl = new Option(rasterFile.table_name, rasterFile.table_name)
            $vectorTableSelect.append(optionEl);
        });


        await setLayer(layerId)
    }

    const selectedLayer = $layerSelect.val();
    await setVectorTables(selectedLayer)
}));