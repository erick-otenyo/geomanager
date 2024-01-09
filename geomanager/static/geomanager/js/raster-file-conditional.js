$(document).ready(function () {
    const $autoIngestCheck = $('#id_auto_ingest_from_directory')
    const $autoIngestWrapper = $('#panel-auto_ingest_settings-section')

    const $useCustomAutoIngestDirNameCheck = $('#id_auto_ingest_use_custom_directory_name')
    const $autoIngestCustomDirNameElements = $('.show-if-custom-dir-name')

    const $useCustomLegendCheck = $('#id_use_custom_legend')
    const $panelCustomLegend = $('#panel-legend-section')


    // auto ingest check
    if ($autoIngestCheck.is(':checked')) {
        $autoIngestWrapper.show()
    } else {
        $autoIngestWrapper.hide()
    }

    $autoIngestCheck.change(function () {
        if ($(this).is(':checked')) {
            $autoIngestWrapper.show()
        } else {
            $autoIngestWrapper.hide()
        }
    });


    // use custom auto ingest dir name check
    if ($useCustomAutoIngestDirNameCheck.is(':checked')) {
        $autoIngestCustomDirNameElements.show()
    } else {
        $autoIngestCustomDirNameElements.hide()
    }

    $useCustomAutoIngestDirNameCheck.change(function () {
        if ($(this).is(':checked')) {
            $autoIngestCustomDirNameElements.show()
        } else {
            $autoIngestCustomDirNameElements.hide()
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