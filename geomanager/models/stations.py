from django.contrib.gis.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.html import format_html
from django_tables2 import tables, LazyPaginator, TemplateColumn
from wagtail.contrib.routable_page.models import RoutablePageMixin, path
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.models import Page

from geomanager.fields import ListField
from geomanager.utils.vector_utils import get_model_field


class StationSettings(BaseSiteSetting):
    stations_table_name = "geomanager_station"
    db_schema = "public"

    columns = models.JSONField(blank=True, null=True)
    geom_type = models.CharField(max_length=100, blank=True, null=True)
    bounds = ListField(max_length=256, blank=True, null=True)
    name_column = models.CharField(max_length=100, blank=True, null=True)

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
            "__module__": "geomanager.station"
        }

        station_model = type("Station", (models.Model,), attrs)

        return station_model

    def station_fields_factory(self):
        fields = {
            "geom": get_model_field(self.geom_type)()
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


class AbstractStationsPage(RoutablePageMixin, Page):
    class Meta:
        abstract = True

    @path('')
    def all_stations(self, request, *args, **kwargs):
        context = {}
        station_settings = StationSettings.for_request(request)

        stations_vector_tiles_url = request.scheme + '://' + request.get_host() + station_settings.stations_vector_tiles_url

        context.update({
            "mapConfig": {
                "stationBounds": station_settings.bounds,
                "stationsVectorTilesUrl": stations_vector_tiles_url,
            },
        })

        # get stations model
        station_model = station_settings.get_station_model()

        # get all columns
        station_table_columns_list = station_settings.station_table_columns_list

        table_fields = [field.get("name") for field in station_table_columns_list]

        page_url = request.build_absolute_uri(self.url)

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
        stations_table.paginate(page=request.GET.get("page", 1), per_page=50, paginator_class=LazyPaginator)

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
