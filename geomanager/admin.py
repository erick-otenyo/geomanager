from django.contrib import admin

from geomanager.models import LayerRasterFile, CountryBoundary, Geostore


@admin.register(LayerRasterFile)
class LayerRasterFileAdmin(admin.ModelAdmin):
    list_display = ('pk', "time")


@admin.register(CountryBoundary)
class CountryBoundaryAdmin(admin.ModelAdmin):
    list_display = ('pk',)


@admin.register(Geostore)
class GeostoreAdmin(admin.ModelAdmin):
    list_display = ('pk',)
