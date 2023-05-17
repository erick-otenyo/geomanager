from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from django_json_widget.widgets import JSONEditorWidget
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.models import Orderable


class MBTSource(TimeStampedModel, ClusterableModel):
    name = models.CharField(max_length=255, verbose_name=_("name"), help_text=_("Style Name"))
    slug = models.CharField(max_length=255, unique=True, editable=False)
    file = models.FileField(upload_to="mbtiles", verbose_name=_("file"))
    default = models.BooleanField(default=False, verbose_name=_("default"), help_text=_("Is Default data source"))

    panels = [
        FieldPanel('name'),
        FieldPanel('file'),
        FieldPanel('default'),
        InlinePanel('gl_styles', heading="GL Styles", label=_("Gl Style"))
    ]

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)

        super(MBTSource, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Basemap Source")

    def __str__(self):
        return self.name


class TileGlStyle(TimeStampedModel, Orderable):
    data_source = ParentalKey(MBTSource, on_delete=models.CASCADE, related_name="gl_styles",
                              verbose_name=_("data source"))
    name = models.CharField(max_length=255, verbose_name=_("name"), help_text=_("Style Name"))
    slug = models.SlugField(max_length=255, unique=True, editable=False)
    json = models.JSONField(verbose_name=_("JSON style"))

    class Meta:
        verbose_name = _("Basemap Style")

    panels = [
        FieldPanel("name"),
        FieldPanel("json", widget=JSONEditorWidget(width="100%")),
    ]

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(TileGlStyle, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def map_style_url(self):
        return reverse("style_json_gl", args=[self.slug])
