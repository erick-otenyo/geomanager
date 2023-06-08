$(document).ready(function () {

    const $jsonStylePanel = $("#panel-open_map_style_json-section")
    const $useDefaultStyle = $("form input[name='use_default_style']")

    if ($useDefaultStyle.is(':checked')) {
        $jsonStylePanel.hide()
    } else {
        $jsonStylePanel.show()
    }

    $useDefaultStyle.on("change", function () {
        const checked = $(this).is(':checked')
        if (checked) {
            $jsonStylePanel.hide()
        } else {
            $jsonStylePanel.show()
        }
    })
})

