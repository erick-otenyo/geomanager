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

    // add scale control
    map.addControl(new maplibregl.ScaleControl({position: 'bottom-right'}));


    // map layer id. Also used as source id
    const mapRasterLayerId = "rasterLayer"

    // wait for map to load
    await new Promise((resolve) => map.on("load", resolve));


    /**
     * Fetches the raster files for a layer from the raster API endpoint.
     * @param {string} layerId - The ID of the layer to fetch files for.
     * @returns {Promise} A promise that resolves to the JSON response from the raster API endpoint.
     */
    const fetchLayerFiles = (layerId) => {
        const rasterListUrl = `${window.geomanager_opts.fileRasterListUrl}?layer=${layerId}`
        return fetch(rasterListUrl).then(res => res.json())
    }

    /**
     * Fetches the bounds of a raster file from the raster API endpoint.
     * @param {string} rasterId - The ID of the raster file to fetch bounds for.
     * @returns {Promise} A promise that resolves to a two-dimensional array representing the raster's bounds.
     */
    const fetchRasterBounds = (rasterId) => {
        const metadataUrl = `${window.geomanager_opts.fileRasterMetadataUrl}`.replace("/0/", `/${rasterId}/`)
        return fetch(metadataUrl).then(res => res.json()).then(metadata => {
            return [
                [metadata.bounds.ll.x, metadata.bounds.ll.y],
                [metadata.bounds.ur.x, metadata.bounds.ur.y]
            ]
        })
    }

    /**
     * Fetches the colormaps from the layer-image API endpoint.
     * @returns {Promise} A promise that resolves to an array of color maps.
     */
    const fetchColorMaps = () => {
        const largeImageApiBaseUrl = `${window.geomanager_opts.layerImageColorMapsUrl}`
        return fetch(largeImageApiBaseUrl).then(res => res.json()).then(colormaps => colormaps.matplotlib)
    }

    // layer selection and change event
    const $layerSelect = $('#layer_select')
    $layerSelect.on("change", (e) => {
        const selectedLayerId = e.target.value;
        setTimestamps(selectedLayerId);
    })

    // timestamp selection and change event
    const $timestampsSelect = $('#timestamps_select')
    $timestampsSelect.on("change", (e) => {
        const selectedTime = e.target.value;
        onTimeChange(selectedTime, map, mapRasterLayerId);
    })

    // colorscale selection and change event
    const $colorScaleSelect = $('#colorscale_select')
    $colorScaleSelect.on("change", (e) => {
        const selectedColorScale = e.target.value;
        onColorScaleChange(selectedColorScale, map, mapRasterLayerId);
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

    const updateSourceTileUrl = (map, sourceId, params) => {

        // Get the source object from the map using the specified source ID.
        const source = map.getSource(sourceId);
        const sourceTileUrl = source.tiles[0]
        const newTileUrl = updateTileUrl(sourceTileUrl, params)

        // Replace the source's tile URL with the updated URL.
        map.getSource(sourceId).tiles = [newTileUrl];

        // Remove the tiles for the updated source from the map cache.
        map.style.sourceCaches[sourceId].clearTiles();

        // Load the new tiles for the updated source within the current viewport.
        map.style.sourceCaches[sourceId].update(map.transform);

        // Trigger a repaint of the map to display the updated tiles.
        map.triggerRepaint();
    }

    /**
     * Updates the source tiles of a map to show data for a specific time.
     * @param {string} selectedTime - The time to show data for, formatted as an ISO 8601 string.
     * @param {object} map - The Mapbox GL JS map object to update.
     * @param {string} sourceId - The ID of the map source to update.
     */
    const onTimeChange = (selectedTime, map, sourceId) => {
        if (selectedTime && map && sourceId) {
            const params = {time: selectedTime}
            updateSourceTileUrl(map, sourceId, params)
        }
    };

    /**
     * Updates the source tiles of a map to use a new color scale.
     * @param {string} selectedColorScale - The name of the color scale to use.
     * @param {object} map - The Mapbox GL JS map object to update.
     * @param {string} sourceId - The ID of the map source to update.
     */
    const onColorScaleChange = (selectedColorScale, map, sourceId) => {
        if (selectedColorScale && map && sourceId) {
            let style
            if (selectedColorScale === "layer-style") {
                style = "layer-style"
            } else {
                style = {"bands": [{"band": 1, "palette": selectedColorScale}]}
                style = JSON.stringify(style)
            }
            const params = {style: style}
            updateSourceTileUrl(map, sourceId, params)
        }
    };

    const setColorMaps = async () => {
        const colorMaps = await fetchColorMaps()
        $colorScaleSelect.empty();

        const {hasstyle} = $('#layer_select option:selected').data()

        if (hasstyle) {
            const optionEl = new Option("Layer Defined Style", "layer-style")
            $colorScaleSelect.append(optionEl);
        }

        $.each(colorMaps, function (index, colorMap) {
            const optionEl = new Option(colorMap, colorMap)
            $colorScaleSelect.append(optionEl);
        });
    }

    const setLayer = async (layerId) => {

        const selectedLayer = window.geomanager_opts.dataLayers.find(l => l.id === layerId)

        const {id, layerConfig: {source: {tiles}, render}} = selectedLayer


        const selectedColorMap = $colorScaleSelect.val()
        let style
        if (selectedColorMap === "layer-style") {
            style = "layer-style"
        } else {
            style = {"bands": [{"band": 1, "palette": selectedColorMap}]}
            style = JSON.stringify(style)
        }

        // Check if the layer exists and remove it if it does
        if (map.getLayer(mapRasterLayerId)) {
            map.removeLayer(mapRasterLayerId);
        }

        // Check if the source exists and remove it if it does
        if (map.getSource(mapRasterLayerId)) {
            map.removeSource(mapRasterLayerId);
        }


        const selectedTimestamp = $timestampsSelect.val()
        const selectedTimestampData = $('#timestamps_select option:selected').data();

        const {rasterid} = selectedTimestampData

        const rasterBounds = await fetchRasterBounds(rasterid)

        map.fitBounds(rasterBounds, {padding: 20})

        const params = {
            layer: layerId,
            time: selectedTimestamp,
            style: style
        }

        const tilesUrl = updateTileUrl(tiles[0], params)

        map.addSource(mapRasterLayerId, {
            type: "raster",
            tiles: [tilesUrl],
        });

        map.addLayer({
            id: mapRasterLayerId,
            type: "raster",
            source: mapRasterLayerId,
        });
    }

    const setTimestamps = async (layerId) => {
        $timestampsSelect.empty();

        const layerFiles = await fetchLayerFiles(layerId)
        $.each(layerFiles, function (index, rasterFile) {
            const optionEl = new Option(rasterFile.time, rasterFile.time)
            optionEl.dataset.rasterid = rasterFile.id
            $timestampsSelect.append(optionEl);
        });

        await setLayer(layerId)
    }

    const selectedLayerId = $layerSelect.val()

    await setColorMaps()
    await setTimestamps(selectedLayerId)
}));