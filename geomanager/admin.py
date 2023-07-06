from django.contrib import admin

from geomanager.models import LayerRasterFile, Geostore


@admin.register(LayerRasterFile)
class LayerRasterFileAdmin(admin.ModelAdmin):
    list_display = ('pk', "time")


@admin.register(Geostore)
class GeostoreAdmin(admin.ModelAdmin):
    list_display = ('pk',)
