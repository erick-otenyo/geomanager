$(document).ready(function () {
    const $palettePanel = $("#panel-palette-section")
    const $colorValuesPanel = $("#panel-custom_color_values-section")
    const $stepsPanel = $("#panel-steps-section")
    const $useCustomColors = $("form input[name='use_custom_colors']")

    if ($useCustomColors.is(':checked')) {
        $palettePanel.hide()
        $colorValuesPanel.show()
        $stepsPanel.hide()
    } else {
        $palettePanel.show()
        $colorValuesPanel.hide()
        $stepsPanel.show()
    }

    $useCustomColors.on("change", function () {
        const checked = $(this).is(':checked')
        if (checked) {
            $palettePanel.hide()
            $colorValuesPanel.show()
            $stepsPanel.hide()
        } else {
            $palettePanel.show()
            $colorValuesPanel.hide()
            $stepsPanel.show()
        }
    })
})

