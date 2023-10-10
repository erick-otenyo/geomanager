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
    const mapRasterLayerId = "wmsLayer"

    // wait for map to load
    await new Promise((resolve) => map.on("load", resolve));

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

    function getValidTimestamps(rangeString) {
        const parts = rangeString.split("/");
        const start_time = new Date(parts[0]);
        const end_time = new Date(parts[1]);
        const duration = parseISO8601Duration(parts[2]);

        let current_time = start_time.getTime();
        const valid_timestamps = [];

        while (current_time < end_time.getTime()) {
            valid_timestamps.push(new Date(current_time).toISOString());
            current_time += duration;
        }

        return valid_timestamps;
    }

    function parseISO8601Duration(durationString) {
        const regex = /P(?:([0-9]+)Y)?(?:([0-9]+)M)?(?:([0-9]+)D)?(?:T(?:([0-9]+)H)?(?:([0-9]+)M)?(?:([0-9]+(?:\.[0-9]+)?)S)?)?/;
        const matches = regex.exec(durationString);

        const years = matches[1] || 0;
        const months = matches[2] || 0;
        const days = matches[3] || 0;
        const hours = matches[4] || 0;
        const minutes = matches[5] || 0;
        const seconds = parseFloat(matches[6]) || 0;

        const duration = (((((years * 365 + months * 30 + days) * 24 + hours) * 60) + minutes) * 60) + seconds;
        return duration * 1000; // convert to milliseconds
    }

    const getTimeStamps = async (wmsGetCapabilitiesUrl, layerName) => {
        return fetch(wmsGetCapabilitiesUrl).then(res => res.text()).then(xml => {
            const parser = new ol.format.WMSCapabilities();
            const result = parser.read(xml);
            const layers = result?.Capability?.Layer?.Layer

            if (layers) {
                const layer = layers.find(l => l.Name === layerName)

                if (layer) {
                    const dims = layer?.Dimension || []
                    const timDimension = dims.find(d => d.name === "time")
                    const timeValue = timDimension.values
                    let dateRange = timeValue.split("/")


                    if (!!dateRange.length && dateRange.length > 1) {
                        return getValidTimestamps(timeValue)
                    }
                    return timeValue.split(",")
                }
            }
            return []
        })
    }

    const setLayer = async (selectedLayer) => {
        const {layerConfig: {source: {tiles}}} = selectedLayer

        // Check if the layer exists and remove it if it does
        if (map.getLayer(mapRasterLayerId)) {
            map.removeLayer(mapRasterLayerId);
        }

        // Check if the source exists and remove it if it does
        if (map.getSource(mapRasterLayerId)) {
            map.removeSource(mapRasterLayerId);
        }

        const selectedTimestamp = $timestampsSelect.val()

        const params = {
            time: selectedTimestamp,
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
        const selectedLayer = window.geomanager_opts.dataLayers.find(l => l.id === layerId)
        const {getCapabilitiesUrl, layerName, getCapabilitiesLayerName} = selectedLayer

        $timestampsSelect.empty();
        const timestamps = await getTimeStamps(getCapabilitiesUrl, getCapabilitiesLayerName || layerName) || []

        $.each(timestamps.reverse().slice(0, 10), function (index, timestamp) {
            const optionEl = new Option(timestamp, timestamp)
            $timestampsSelect.append(optionEl);
        });

        await setLayer(selectedLayer)
    }

    const selectedLayerId = $layerSelect.val();


    await setTimestamps(selectedLayerId)
}));

