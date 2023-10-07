from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from django_json_widget.widgets import JSONEditorWidget
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel

from geomanager.constants import DEFAULT_OPEN_MAP_TILES_STYLE


class MBTSource(TimeStampedModel, ClusterableModel):
    name = models.CharField(max_length=255, verbose_name=_("name"), help_text=_("Style Name"))
    slug = models.CharField(max_length=255, unique=True, editable=False)
    file = models.FileField(upload_to="mbtiles", verbose_name=_("file"))
    use_default_style = models.BooleanField(default=True, verbose_name=_("Use default style"))
    open_map_style_json = models.JSONField(blank=True, null=True, verbose_name=_("OpenMapTiles style"),
                                           help_text=mark_safe(
                                               "OpenMapTiles JSON Style. See schema here: "
                                               "<a href='https://openmaptiles.org/schema' target='_blank' rel='noopener noreferrer'>"
                                               "https://openmaptiles.org/schema</a>"))

    panels = [
        FieldPanel('name'),
        FieldPanel('file'),
        FieldPanel('use_default_style'),
        FieldPanel('open_map_style_json', widget=JSONEditorWidget(width="100%")),
    ]

    class Meta:
        verbose_name = _("Basemap Source")
        verbose_name_plural = _("Basemap Sources")

    def __str__(self):
        return self.name

    @cached_property
    def json_style(self):
        if self.use_default_style:
            return DEFAULT_OPEN_MAP_TILES_STYLE
        if self.open_map_style_json:
            return self.open_map_style_json
        return {}

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)

        super(MBTSource, self).save(*args, **kwargs)

    @property
    def map_style_url(self):
        return reverse("style_json_gl", args=[self.slug])
