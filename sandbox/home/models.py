from django.contrib.gis.db import models
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_tables2 import tables, LazyPaginator, TemplateColumn
from wagtail.admin.panels import FieldPanel
from wagtail.api.v2.utils import get_full_url
from wagtail.contrib.routable_page.models import path, RoutablePageMixin
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import register_setting
from wagtail.models import Page
from wagtailcache.cache import cache_page

from geomanager.fields import ListField
from geomanager.models import SubCategory, Metadata
from geomanager.utils.vector_utils import get_model_field


@method_decorator(cache_page, name="serve")
class HomePage(Page):
    pass


@register_setting
class StationSettings(BaseSiteSetting):
    stations_table_name = "home_station"
    db_schema = "public"

    columns = models.JSONField(blank=True, null=True)
    geom_type = models.CharField(max_length=100, blank=True, null=True)
    bounds = ListField(max_length=256, blank=True, null=True)
    name_column = models.CharField(max_length=100, blank=True, null=True)

    show_on_mapviewer = models.BooleanField(default=False, verbose_name=_("Show on Mapviewer"),
                                            help_text=_("Check to show stations data on Mapviewer"))
    layer_title = models.CharField(max_length=100, blank=True, null=True, default="Stations",
                                   verbose_name=_("Stations Layer Title"))
    geomanager_subcategory = models.ForeignKey(SubCategory, null=True, blank=True,
                                               verbose_name=_("Stations Layer SubCategory"),
                                               on_delete=models.SET_NULL)
    geomanager_layer_metadata = models.ForeignKey(Metadata, on_delete=models.SET_NULL, blank=True, null=True,
                                                  verbose_name=_("Stations Layer Metadata"))

    panels = [
        FieldPanel("show_on_mapviewer"),
        FieldPanel("layer_title"),
        FieldPanel("geomanager_subcategory"),
        FieldPanel("geomanager_layer_metadata"),
    ]

    @cached_property
    def full_table_name(self):
        return f"{self.db_schema}.{self.stations_table_name}"

    @cached_property
    def stations_vector_tiles_url(self):
        base_url = reverse("station_tiles", args=(0, 0, 0)).replace("/0/0/0", r"/{z}/{x}/{y}")
        return base_url

    def get_station_model(self):
        fields = self.station_fields_factory()

        attrs = {
            **fields,
            "managed": False,
            "__module__": "home"
        }

        station_model = type("Station", (models.Model,), attrs)

        return station_model

    def station_fields_factory(self):
        geom_type = self.geom_type or "Point"
        fields = {
            "geom": get_model_field(geom_type)()
        }

        if isinstance(self.columns, list):
            for column in self.columns:
                data_type = column.get("data_type")
                name = column.get("name")
                label = column.get("label") or name
                if data_type:
                    model_field = get_model_field(column.get("data_type"))

                    if model_field:
                        field_kwargs = {"verbose_name": label}
                        if name == "gid":
                            field_kwargs.update({"primary_key": True})
                        fields.update({name: model_field(**field_kwargs)})

        return fields

    @cached_property
    def station_columns_list(self):
        station_columns = []
        if self.columns and isinstance(self.columns, list):
            for column in self.columns:
                name = column.get("name")
                if name:
                    station_columns.append(name)
        return station_columns

    @cached_property
    def station_table_columns_list(self):
        table_columns = []
        if self.columns and isinstance(self.columns, list):
            for column in self.columns:
                name = column.get("name")
                label = column.get("label")
                table = column.get("table")
                if name and table:
                    table_columns.append({"name": name, "label": label})
        return table_columns

    @cached_property
    def station_popup_columns_list(self):
        popup_columns = []
        if self.columns and isinstance(self.columns, list):
            for column in self.columns:
                name = column.get("name")
                label = column.get("label")
                popup = column.get("popup")
                if name and popup:
                    popup_columns.append({"name": name, "label": label})
        return popup_columns


class StationsPage(RoutablePageMixin, Page):
    template = "stations/stations_list_page.html"
    parent_page_types = ["home.HomePage"]
    subpage_types = []
    max_count = 1

    content_panels = Page.content_panels

    @path('')
    def all_stations(self, request, *args, **kwargs):
        context = {}
        station_settings = StationSettings.for_request(request)

        stations_vector_tiles_url = get_full_url(request, station_settings.stations_vector_tiles_url)

        context.update({
            "mapConfig": {
                "stationBounds": station_settings.bounds or [],
                "stationsVectorTilesUrl": stations_vector_tiles_url,
            },
        })

        # get stations model
        station_model = station_settings.get_station_model()

        # get all columns
        station_table_columns_list = station_settings.station_table_columns_list

        table_fields = [field.get("name") for field in station_table_columns_list]

        page_url = get_full_url(request, self.url)

        class StationTable(tables.Table):
            detail_url = TemplateColumn('<a href="" target="_blank"></a>')

            class Meta:
                model = station_model
                fields = table_fields

            def render_detail_url(self, value, record):
                record_pk_suffix = str(record.gid)
                if page_url and not page_url.endswith("/"):
                    record_pk_suffix = f"/{record_pk_suffix}"
                url = page_url + record_pk_suffix
                return format_html(
                    "<a href='{}'>View detail</a>",
                    url
                )

        stations_table = StationTable(station_model.objects.all())

        try:
            stations_table.paginate(page=request.GET.get("page", 1), per_page=50, paginator_class=LazyPaginator)
        except Exception as e:
            stations_table = None

        context.update({
            "stations_table": stations_table,
            "popup_fields": station_settings.station_popup_columns_list
        })

        return self.render(request, context_overrides={**context})

    @path('<int:station_pk>/')
    def station_detail(self, request, station_pk):
        station_settings = StationSettings.for_request(request)

        # get stations model
        station_model = station_settings.get_station_model()

        station = station_model.objects.filter(pk=station_pk)

        if station.exists:
            station = station.first()
        else:
            station = None

        context = {
            "station": station,
            "columns": station_settings.columns,
            "bounds": station_settings.bounds,
            "station_name_column": station_settings.name_column
        }

        return self.render(request, template="stations/station_detail_page.html", context_overrides=context)
