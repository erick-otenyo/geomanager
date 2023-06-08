$(document).ready(function () {

    const $iconSelected = $("#selected-icon")
    const $iconOptions = $("#icon-options")

    // form Data
    const $iconEl = $("input[name='icon']")

    const iconDialog = document.getElementById("dialog-icon")

    const createIconOptions = (onSelect) => {
        const $svgDefs = $('div[data-sprite] svg defs symbol')

        $svgDefs.each(function () {
            const iconId = $(this).attr("id")
            createIconOption(iconId, onSelect).appendTo($iconOptions)
        })
    }

    const createIconOption = (iconId, onSelect) => {
        const $container = $("<div class='svg-container'>")
        $container.on("click", () => onSelect(iconId))
        $(`<svg class="icon icon-option" aria-hidden="true">
            <use href="#${iconId}"></use>
        </svg>`).appendTo($container)

        $(`<div class="icon-lable">${iconId}</div>`).appendTo($container)

        return $container
    }

    const handleOnSelectColor = (iconId) => {

        const svg = $(`<svg class="icon selected-icon" aria-hidden="true">
            <use href="#${iconId}"></use>
        </svg>`)

        $iconSelected.html(svg)

        $iconEl.val(iconId)

        // hide color dialog
        iconDialog.dispatchEvent(new CustomEvent("wagtail:hide"))
    }

    createIconOptions(handleOnSelectColor)


    $("#id_icon_filter").on("keyup", function () {
        const value = $(this).val().toLowerCase();
        $("#icon-options div").filter(function () {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });
});