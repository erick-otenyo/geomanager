$(document).ready(function () {

    const $palettePanel = $("#panel-palette-section")
    const $colorValuesPanel = $("#panel-custom_color_values-section")
    const $useCustomColors = $("form input[name='use_custom_colors']")

    if ($useCustomColors.is(':checked')) {
        $palettePanel.hide()
        $colorValuesPanel.show()
    } else {
        $palettePanel.show()
        $colorValuesPanel.hide()
    }

    $useCustomColors.on("change", function () {
        const checked = $(this).is(':checked')
        if (checked) {
            $palettePanel.hide()
            $colorValuesPanel.show()
        } else {
            $palettePanel.show()
            $colorValuesPanel.hide()
        }
    })
})

