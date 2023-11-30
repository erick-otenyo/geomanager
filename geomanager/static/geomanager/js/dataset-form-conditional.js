$(document).ready(function () {
    const $isMultiLayerCheck = $('#id_multi_layer')
    const $panelEnableAllMultiLayer = $('#panel-enable_all_multi_layers_on_add-section')

    if ($isMultiLayerCheck.is(':checked')) {
        $panelEnableAllMultiLayer.show()
    } else {
        $panelEnableAllMultiLayer.hide()
    }


    $isMultiLayerCheck.change(function () {
        if ($(this).is(':checked')) {
            $panelEnableAllMultiLayer.show()
        } else {
            $panelEnableAllMultiLayer.hide()
        }
    });

});