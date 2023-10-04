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

    // map layer id. Also used as source id
    const mapRasterLayerId = "vectorTileLayer"

    // wait for map to load
    await new Promise((resolve) => map.on("load", resolve));

    // layer selection and change event
    const $layerSelect = $('#layer_select')
    $layerSelect.on("change", (e) => {
        const selectedLayerId = e.target.value;
    })

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

    // timestamp selection and change event
    const $timestampsWrapper = $('#timestamps_wrapper')
    const $timestampsSelect = $('#timestamps_select')
    $timestampsSelect.on("change", (e) => {
        const selectedTime = e.target.value;
        const selectedLayerId = $layerSelect.val();
        onTimeChange(selectedTime, map, selectedLayerId);
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

    const fetchTimestamps = (tileJsonUrl, timestampResponseObjectKey = "timestamps") => {
        return fetch(tileJsonUrl).then(res => res.json()).then(res => res[timestampResponseObjectKey])
    }

    const setLayer = (selectedLayer) => {
        const {id: layerId, layerConfig: {source: {tiles}}} = selectedLayer

        // Check if the layer exists and remove it if it does
        if (map.getLayer(layerId)) {
            map.removeLayer(layerId);
        }

        // Check if the source exists and remove it if it does
        if (map.getSource(layerId)) {
            map.removeSource(layerId);
        }

        const selectedTimestamp = $timestampsSelect.val()

        const params = {}

        if (selectedTimestamp) {
            params["time"] = selectedTimestamp
        }

        const tilesUrl = updateTileUrl(tiles[0], params)

        map.addSource(layerId, {
            type: "raster",
            tiles: [tilesUrl],
        });

        map.addLayer({
            id: layerId,
            "type": "raster",
            source: layerId,
        });
    }

    const selectedLayerId = $layerSelect.val();

    if (selectedLayerId) {
        const selectedLayer = window.geomanager_opts.dataLayers.find(l => l.id === selectedLayerId)


        const {tileJsonUrl, timestampsResponseObjectKey} = selectedLayer

        if (tileJsonUrl) {
            const timestamps = await fetchTimestamps(tileJsonUrl, timestampsResponseObjectKey)
            $.each(timestamps, function (index, t) {
                const optionEl = new Option(t, t)
                $timestampsSelect.append(optionEl);
            });
            $timestampsWrapper.show()
        }

        if (selectedLayer) {
            setLayer(selectedLayer)
        }
    }


}));

