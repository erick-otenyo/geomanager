$(document).ready(function () {

    const $getTimeFromTileJSonInput = $("#id_get_time_from_tile_json")
    const $dependentElements = $(".show_if_get_time_checked")

    if ($getTimeFromTileJSonInput.is(':checked')) {
        $dependentElements.show()
    } else {
        $dependentElements.hide()
    }

    $getTimeFromTileJSonInput.on("change", function () {
        const checked = $(this).is(':checked')
        if (checked) {
            $dependentElements.show()
        } else {
            $dependentElements.hide()
        }
    })
})