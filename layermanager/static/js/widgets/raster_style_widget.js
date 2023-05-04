$(document).ready(function () {

    const parseIntPrecision = (d) => {
        if (d === undefined) {
            return (n) => n
        }
        const m = Math.pow(10, d)
        return (n) => Math.round(n * m) / m
    }

    const createLegend = ({min, max, palette}) => {
        const colors = palette.split(',')
        const step = (max - min) / (colors.length - (min > 0 ? 2 : 1))
        const precision = d3.precisionRound(step, max)
        const valueFormat = parseIntPrecision(precision)

        let from = min
        let to = valueFormat(min + step)

        return colors.map((color, index) => {
            const item = {color}

            if (index === 0 && min > 0) {
                // Less than min
                item.from = 0
                item.to = min
                item.name = '< ' + min
                to = min
            } else if (from < max) {
                item.from = from
                item.to = to
                item.name = from + ' - ' + to
            } else {
                // Higher than max
                item.from = from
                item.name = '> ' + from
            }

            from = to
            to = valueFormat(min + step * (index + (min > 0 ? 1 : 2)))

            return item
        })
    }

    const $styleButton = $("#style-button")
    const $colorOptions = $("#color-options")

    // form Data
    const $maxEl = $("form input[name='max']")
    const $minEl = $("form input[name='min']")
    const $paletteEl = $("input[name='palette']")
    const $stepsEl = $("form input[name='steps']")

    const colorDialog = document.getElementById("dialog-raster-style")
    let colorscaleName = 'YlOrBr'
    let colorSteps = parseInt($stepsEl.val())

    const updateLegendPreview = () => {
        const min = parseInt($minEl.val())
        const max = parseInt($maxEl.val())
        const steps = parseInt($stepsEl.val())
        let palette = $paletteEl.val()

        if (!palette) {
            palette = colorbrewer[colorscaleName][steps].join(",")
            $paletteEl.val(palette)
        }

        const legendPreviewContent = $("#legend-content")
        const legend = createLegend({min, max, palette})

        const table = $('<table>');
        const tbody = $('<tbody>').appendTo(table);

        legend.forEach((item) => {
            const legendItem = $('<tr>').appendTo(tbody);
            const th = $('<th>').appendTo(legendItem)
            $('<span>').css("background-color", item.color).appendTo(th)
            $('<td>').addClass("segment-label").text(item.name).appendTo(legendItem)
        })

        legendPreviewContent.html(table)
    }

    const createColorOptions = (bins, width, onSelectColor) => {
        const $container = $("<div>")
        colorScales.map((scale) => {
            createColorScale(scale, bins, width, onSelectColor).appendTo($container)
        })

        $colorOptions.html($container)
    }

    const createColorScale = (scale, bins, width, onSelectColor) => {
        const colors = colorbrewer[scale][bins]
        const itemWidth = width ? width / bins : 36


        const $ul = $("<ul>")
            .addClass("colorscale")

        if (onSelectColor) {
            $ul.on("click", () => onSelectColor(scale))
        }

        if (width) {
            $ul.css("width", width)
        }


        colors.forEach((color) => {
            $("<li>").addClass("colorscale-item")
                .css("background-color", color).css("width", itemWidth)
                .appendTo($ul);
        });

        return $ul;
    }

    const handleOnSelectColor = (scale) => {
        colorscaleName = scale
        const colorSteps = parseInt($stepsEl.val())
        const colors = colorbrewer[scale][colorSteps]
        $paletteEl.val(colors.join(","))

        const $styleColor = createColorScale(scale, colorSteps)
        $styleButton.html($styleColor)

        // hide color dialog
        colorDialog.dispatchEvent(new CustomEvent("wagtail:hide"))

        updateLegendPreview()
    }

    // ***** initialize ****
    if (instanceColorPalette) {
        colorSteps = instanceColorPalette.split(',').length
        colorscaleName = getColorScale(instanceColorPalette)
    }

    const $styleColor = createColorScale(colorscaleName, colorSteps)

    createColorOptions(colorSteps, 400, handleOnSelectColor)
    $styleButton.html($styleColor)

    updateLegendPreview()


    //****  changes *****
    // validate min value
    $minEl.on("input", function () {
        const val = $(this).val()
        let $errorEl = $(this).parent().siblings().filter(".w-field__errors")[0]
        if ($errorEl) {
            $errorEl = $($errorEl)
        }

        if (!val) {
            const message = $("<p class='error-message'>Min value is required </p>");
            $errorEl.html(message)
        } else {
            updateLegendPreview()
            if ($errorEl.html()) {
                $errorEl.empty()
            }
        }
    });

    // validate max value
    $maxEl.on("input", function () {
        const val = $(this).val()
        let $errorEl = $(this).parent().siblings().filter(".w-field__errors")[0]
        if ($errorEl) {
            $errorEl = $($errorEl)
        }

        const minValue = parseInt($minEl.val())

        if (!val) {
            const message = $("<p class='error-message'>Max value is required </p>");
            $errorEl.html(message)
        } else if (minValue >= parseInt(val)) {
            const message = $("<p class='error-message'>Max should be greater that min </p>");
            $errorEl.html(message)
        } else {
            updateLegendPreview()

            if ($errorEl.html()) {
                $errorEl.empty()
            }
        }
    });

    $stepsEl.on("input", function () {
        const val = $(this).val()
        let $errorEl = $(this).parent().siblings().filter(".w-field__errors")[0]
        if ($errorEl) {
            $errorEl = $($errorEl)
        }

        if (!val) {
            const message = $("<p class='error-message'>Valid Steps are 3 to 9</p>");
            $errorEl.html(message)
        } else {
            const steps = parseInt(val)
            const $styleColor = createColorScale(colorscaleName, steps)
            $styleButton.html($styleColor)
            createColorOptions(steps, 400, handleOnSelectColor)

            const colors = colorbrewer[colorscaleName][steps]
            $paletteEl.val(colors.join(","))

            updateLegendPreview()

            if ($errorEl.html()) {
                $errorEl.empty()
            }
        }
    });

});