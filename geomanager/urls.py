from django.urls import include, path
from django.views.decorators.cache import cache_page
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from geomanager.views import (
    RasterTileView,
    VectorTileView,
    map_view,
    RegisterView,
    ResetPasswordView,
    BoundaryVectorTileView, tile_gl, tile_json_gl, style_json_gl, get_mapviewer_config, GeoJSONPgTableView
)
from geomanager.views.raster import RasterDataPixelView, RasterDataPixelTimeseriesView
from geomanager.viewsets import (
    FileImageLayerRasterFileDetailViewSet,
    VectorTableFileDetailViewSet,
    DatasetListViewSet,
    GeostoreViewSet,
    CountryBoundaryViewSet,
    MetadataViewSet
)

router = SimpleRouter(trailing_slash=False)

router.register(r'api/datasets', DatasetListViewSet)
router.register(r'api/metadata', MetadataViewSet)

router.register(r'api/file-raster', FileImageLayerRasterFileDetailViewSet)
router.register(r'api/vector-data', VectorTableFileDetailViewSet)

urlpatterns = [
                  # MapViewer
                  path(r'mapviewer/', map_view, name="mapview"),
                  path(r'mapviewer/<str:location_type>/', map_view, name="mapview"),
                  path(r'mapviewer/<str:location_type>/<str:adm0>/', map_view, name="mapview"),
                  path(r'mapviewer/<str:location_type>/<str:adm0>/<str:adm1>/', map_view, name="mapview"),
                  path(r'mapviewer/<str:location_type>/<str:adm0>/<str:adm1>/<str:adm2>/', map_view, name="mapview"),

                  # MapViewer configuration
                  path(r'api/mapviewer-config', get_mapviewer_config, name="mapview_config"),

                  # Authentication
                  path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
                  path('api/auth/password-reset/', ResetPasswordView.as_view(), name='auth_password_reset'),
                  path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
                  path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

                  # Country
                  path(r'api/country', CountryBoundaryViewSet.as_view({"get": "get"}), name="country_list"),
                  path(r'api/country/<str:gid_0>', CountryBoundaryViewSet.as_view({"get": "get_regions"}),
                       name="country_regions"),
                  path(r'api/country/<str:gid_0>/<str:gid_1>',
                       CountryBoundaryViewSet.as_view({"get": "get_sub_regions"}),
                       name="country_sub_regions"),

                  # Geostore
                  path(r'api/geostore/', GeostoreViewSet.as_view({"post": "post"}), name="geostore"),
                  path(r'api/geostore/<uuid:geostore_id>', GeostoreViewSet.as_view({"get": "get"}),
                       name="get_by_geostore"),
                  path(r'api/geostore/admin/<str:gid_0>', GeostoreViewSet.as_view({"get": "get_by_admin"}),
                       name="get_by_gid0"),
                  path(r'api/geostore/admin/<str:gid_0>/<str:gid_1>', GeostoreViewSet.as_view({"get": "get_by_admin"}),
                       name="get_by_gid1"),
                  path(r'api/geostore/admin/<str:gid_0>/<str:gid_1>/<str:gid_2>',
                       GeostoreViewSet.as_view({"get": "get_by_admin"}),
                       name="get_by_gid2"),

                  # Tiles
                  path(r'api/raster-tiles/<int:z>/<int:x>/<int:y>', RasterTileView.as_view(), name="raster_tiles"),
                  path(r'api/vector-tiles/<int:z>/<int:x>/<int:y>', cache_page(3600)(VectorTileView.as_view()),
                       name="vector_tiles"),
                  path(r'api/boundary-tiles/<int:z>/<int:x>/<int:y>',
                       BoundaryVectorTileView.as_view(),
                       name="boundary_tiles"),

                  # Data
                  path(r'api/raster-data/pixel', RasterDataPixelView.as_view(), name="raster_data_pixel"),
                  path(r'api/raster-data/pixel/timeseries', RasterDataPixelTimeseriesView.as_view(),
                       name="raster_data_pixel_timeseries"),

                  # FeatureServ
                  path(r'api/feature-serv/<str:table_name>.geojson', cache_page(3600)(GeoJSONPgTableView.as_view()),
                       name="feature_serv"),

                  # Tiles GL
                  path(r'api/tile-gl/tile/<str:source>/<int:z>/<int:x>/<int:y>.pbf', tile_gl, name="tile_gl"),
                  path(r'api/tile-gl/tile-json/<str:source>.json', tile_json_gl, name="tile_json_gl"),
                  path(r'api/tile-gl/style/<str:style_name>.json', style_json_gl, name="style_json_gl"),

                  # Additional, standalone URLs from django-large-image
                  path('', include('django_large_image.urls')),
              ] + router.urls
