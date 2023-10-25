$((function () {
    $(document).on("drop dragover", (function (e) {
        e.preventDefault()
    }));

    $("#fileupload").fileupload({
        dataType: "html",
        sequentialUploads: !0,
        dropZone: $(".drop-zone"),
        acceptFileTypes: window.fileupload_opts.accepted_file_types,
        maxFileSize: window.fileupload_opts.max_file_size,
        previewMinWidth: 150,
        previewMaxWidth: 150,
        previewMinHeight: 150,
        previewMaxHeight: 150,
        messages: {
            acceptFileTypes: window.fileupload_opts.errormessages.accepted_file_types,
            maxFileSize: window.fileupload_opts.errormessages.max_file_size
        },
        add: function (e, a) {
            const t = $(this)
            const s = t.data("blueimp-fileupload") || t.data("fileupload")
            const o = $($("#upload-list-item").html()).addClass("upload-uploading")
            const i = s.options;

            $("#upload-list").append(o);
            a.context = o;

            a.process((function () {
                return t.fileupload("process", a)
            })).always((function () {
                a.context.removeClass("processing");
                a.context.find(".left").each((function (e, t) {
                    $(t).append(escapeHtml(a.files[e].name))
                }));
            })).done((function () {
                a.context.find(".start").prop("disabled", !1);
                !1 !== s._trigger("added", e, a) && (i.autoUpload || a.autoUpload) && !1 !== a.autoUpload && a.submit()
            })).fail((function () {
                a.files.error && a.context.each((function (e) {
                    const t = a.files[e].error;
                    t && $(this).find(".error_messages").html(t)
                }))
            }))
        },
        processfail: function (e, a) {
            $(a.context).removeClass("upload-uploading").addClass("upload-failure")
        },
        progress: function (e, a) {
            if (e.isDefaultPrevented()) return !1;
            const t = Math.floor(a.loaded / a.total * 100);
            a.context.each((function () {
                $(this).find(".progress").addClass("active").attr("aria-valuenow", t).find(".bar").css("width", t + "%").html(t + "%")
            }))
        },
        progressall: function (e, a) {
            const t = parseInt(a.loaded / a.total * 100, 10);
            $("#overall-progress").addClass("active").attr("aria-valuenow", t).find(".bar").css("width", t + "%").html(t + "%");
            t >= 100 && $("#overall-progress").removeClass("active").find(".bar").css("width", "0%")
        },
        formData: function (e) {
            const a = this.files[0].name, t = {title: a.replace(/\.[^.]+$/, "")};
            const s = window.fileupload_opts.max_title_length;
            return e.get(0).dispatchEvent(new CustomEvent("wagtail:images-upload", {
                bubbles: !0,
                cancelable: !0,
                detail: {data: t, filename: a, maxTitleLength: s}
            })) ? e.serializeArray().concat({name: "title", value: t.title}) : e.serializeArray()
        },
        done: function (e, a) {
            const t = $(a.context);
            const s = JSON.parse(a.result);
            if (s.success) {
                if (s.forms) {
                    // clear
                    $("#upload-list").empty()
                    s.forms.forEach(form => {
                        const o = $($("#upload-list-item").html()).addClass("upload-success")
                        $(".right", o).append(form)
                        $("#upload-list").append(o);
                    })
                } else {
                    t.addClass("upload-success");
                    $(".right", t).append(s.form)
                }

            } else {
                t.addClass("upload-failure");
                $(".right .error_messages", t).append(s.error_message)
            }

        },
        fail: function (e, a) {
            const t = $(a.context)
            const s = $(".server-error", t);

            $(".error-text", s).text(a.errorThrown);
            $(".error-code", s).text(a.jqXHR.status);

            t.addClass("upload-server-error")
        },
        always: function (e, a) {
            $(a.context).removeClass("upload-uploading").addClass("upload-complete")
        }
    });

    $("#upload-list").on("submit", "form", (function (e) {
        const a = $(this);
        const t = new FormData(this);
        const s = a.closest("#upload-list > li");
        e.preventDefault();

        $.ajax({
            contentType: !1,
            data: t,
            processData: !1,
            type: "POST",
            url: this.action
        }).done((function (e) {
            if (e.success) {
                const t = $(".status-msg.update-success").text();
                document.dispatchEvent(new CustomEvent("w-messages:add", {
                    detail: {
                        clear: !0,
                        text: t,
                        type: "success"
                    }
                }));
                s.slideUp((function () {
                    $(this).remove()
                }))
            } else {
                a.replaceWith(e.form);
            }

        }))
    }));

    $("#upload-list").on("click", ".delete", (function (e) {
        const a = $(this).closest("form");
        const t = a.closest("#upload-list > li");
        e.preventDefault();

        const s = $('input[name="csrfmiddlewaretoken"]', a).val();

        $.post(this.href, {csrfmiddlewaretoken: s}, (function (e) {
            e.success && t.slideUp((function () {
                $(this).remove()
            }))
        }))
    }))

}));