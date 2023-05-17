from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.cache import cache_control

from geomanager.errors import MissingTileError
from geomanager.models import MBTSource, TileGlStyle
from geomanager.utils.tile_gl import center_from_bounds, open_mbtiles

DEFAULT_ZOOM = 13
DEFAULT_MINZOOM = 7
DEFAULT_MAXZOOM = 15
WORLD_BOUNDS = [-180, -85.05112877980659, 180, 85.0511287798066]

MONTH_SECONDS = 60 * 60 * 24 * 30


@cache_control(max_age=MONTH_SECONDS)
def tile_gl(request, source, z, x, y):
    source = MBTSource.objects.get(slug=source)
    with (open_mbtiles(source.file.path)) as mbtiles:
        try:
            data = mbtiles.tile(z, x, y)
            response = HttpResponse(
                content=data,
                status=200,
            )
            response["Content-Type"] = "application/x-protobuf"
            response["Content-Encoding"] = "gzip"

            return response

        except MissingTileError:
            return HttpResponse(
                status=204,
            )


def tile_json_gl(request, source):
    source = MBTSource.objects.get(slug=source)
    with open_mbtiles(source.file.path) as mbtiles:
        metadata = mbtiles.metadata()

        # Load valid tilejson keys from the mbtiles metadata
        valid_tilejson_keys = (
            # MUST
            "name",
            "format",
            # SHOULD
            "bounds",
            "center",
            "minzoom",
            "maxzoom",
            # MAY
            "attribution",
            "description",
            "type",
            "version",
            # UNSPECIFIED
            "scheme",
        )
        spec = {key: metadata[key] for key in valid_tilejson_keys if key in metadata}

        if spec["format"] == "pbf":
            spec["vector_layers"] = metadata["json"]["vector_layers"]
        else:
            raise NotImplementedError(
                f"Only mbtiles in pbf format are supported. Found {spec['format']}"
            )

        # Optional fields
        spec["scheme"] = spec.get("scheme", "xyz")
        spec["bounds"] = spec.get("bounds", WORLD_BOUNDS)
        spec["minzoom"] = spec.get("minzoom", DEFAULT_MINZOOM)
        spec["maxzoom"] = spec.get("maxzoom", DEFAULT_MINZOOM)
        spec["center"] = spec.get(
            "center", center_from_bounds(spec["bounds"], DEFAULT_ZOOM)
        )

        # Tile defintions
        tile_url = request.build_absolute_uri(reverse("tile_gl", args=(source.slug, 0, 0, 0)))
        tile_url = tile_url.replace("/0/0/0.pbf", r"/{z}/{x}/{y}.pbf")
        spec["tiles"] = [tile_url]

        # Version defintion
        spec["tilejson"] = "3.0.0"

        return JsonResponse(spec)


def style_json_gl(request, style_name):
    style = TileGlStyle.objects.get(slug=style_name)
    tilejson_url = request.build_absolute_uri(reverse("tile_json_gl", args=[style.data_source.slug]))

    style_config = style.json
    style_config["id"] = style.pk
    style_config["name"] = style.name
    style_config["glyphs"] = "https://fonts.openmaptiles.org/{fontstack}/{range}.pbf"
    style_config["sources"] = {
        "openmaptiles": {
            "type": "vector", "url": tilejson_url
        }
    }

    return JsonResponse(style_config)
