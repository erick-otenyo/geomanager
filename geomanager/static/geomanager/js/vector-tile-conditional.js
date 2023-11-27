$(document).ready(function () {
    const $useRenderLayersJsonCheck = $('#id_use_render_layers_json')
    const $panelRenderLayersJson = $('#panel-render_layers_json-section')
    const $panelRenderLayersBlocks = $('#panel-render_layers-section')

    if ($useRenderLayersJsonCheck.is(':checked')) {
        $panelRenderLayersJson.show()
        $panelRenderLayersBlocks.hide()
    } else {
        $panelRenderLayersJson.hide()
        $panelRenderLayersBlocks.show()
    }


    $useRenderLayersJsonCheck.change(function () {
        if ($(this).is(':checked')) {
            $panelRenderLayersJson.show()
            $panelRenderLayersBlocks.hide()
        } else {
            $panelRenderLayersJson.hide()
            $panelRenderLayersBlocks.show()
        }
    });

});