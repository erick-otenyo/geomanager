$(document).ready(function () {
    const $autoIngestCheck = $('#id_auto_ingest_from_directory')
    const $panelDataVariable = $('#panel-auto_ingest_nc_data_variable-section')

    const $useCustomLegendCheck = $('#id_use_custom_legend')
    const $panelCustomLegend = $('#panel-legend-section')

    if ($autoIngestCheck.is(':checked')) {
        $panelDataVariable.show()
    } else {
        $panelDataVariable.hide()
    }


    $autoIngestCheck.change(function () {
        if ($(this).is(':checked')) {
            $panelDataVariable.show()
        } else {
            $panelDataVariable.hide()
        }
    });


    if ($useCustomLegendCheck.is(':checked')) {
        $panelCustomLegend.show()
    } else {
        $panelCustomLegend.hide()
    }


    $useCustomLegendCheck.change(function () {
        if ($(this).is(':checked')) {
            $panelCustomLegend.show()
        } else {
            $panelCustomLegend.hide()
        }
    });

});