from django.urls import include, path
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView, )

from geomanager.views import (
    RasterTileView,
    VectorTileView,
    map_view,
    RegisterView,
    ResetPasswordView,
    tile_gl,
    tile_json_gl,
    style_json_gl,
    get_mapviewer_config,
    GeoJSONPgTableView
)
from geomanager.views.auth import (
    EmailTokenObtainPairView,
    UserTokenVerifyView
)
from geomanager.views.profile import (
    get_geomanager_user_profile,
    create_or_update_geomanager_user_profile
)
from geomanager.views.raster import (
    RasterDataPixelView,
    RasterDataPixelTimeseriesView,
    RasterDataGeostoreView,
    RasterDataGeostoreTimeseriesView
)
from geomanager.views.stations import StationsTileView
from geomanager.viewsets import (
    FileImageLayerRasterFileDetailViewSet,
    VectorTableFileDetailViewSet,
    DatasetListViewSet,
    GeostoreViewSet,
    AdminBoundaryViewSet,
    MetadataViewSet
)
from geomanager.viewsets.aoi import AoiViewSet

router = SimpleRouter(trailing_slash=False)

router.register(r'api/datasets', DatasetListViewSet)
router.register(r'api/metadata', MetadataViewSet)

router.register(r'api/file-raster', FileImageLayerRasterFileDetailViewSet)
router.register(r'api/vector-data', VectorTableFileDetailViewSet)

router.register(r'api/aoi', AoiViewSet)

urlpatterns = [
                  # MapViewer
                  path(r'mapviewer/', map_view, name="mapview"),
                  path(r'mapviewer/<str:location_type>/', map_view, name="mapview"),
                  path(r'mapviewer/<str:location_type>/<str:adm0>/', map_view, name="mapview"),
                  path(r'mapviewer/<str:location_type>/<str:adm0>/<str:adm1>/', map_view, name="mapview"),
                  path(r'mapviewer/<str:location_type>/<str:adm0>/<str:adm1>/', map_view, name="mapview"),
                  path(r'mapviewer/<str:location_type>/<str:adm0>/<str:adm1>/<str:adm2>/', map_view, name="mapview"),

                  # MapViewer configuration
                  path(r'api/mapviewer-config', get_mapviewer_config, name="mapview_config"),

                  # Authentication
                  path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
                  path('api/auth/reset-password/', ResetPasswordView.as_view(), name='auth_password_reset'),
                  path('api/auth/token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
                  path('api/auth/token/verify/', UserTokenVerifyView.as_view(), name='token_verify'),
                  path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

                  # User Profile
                  path('api/geomanager-profile/<int:user_id>', get_geomanager_user_profile,
                       name='get_geomanager_user_profile'),
                  path('api/geomanager-profile/update/<str:user_id>', create_or_update_geomanager_user_profile,
                       name='update_geomanager_user_profile'),

                  # # User Areas of Interest
                  # path('api/aoi/<int:user_id>', get_user_aoi_list, name='get_user_aoi_list'),
                  # path('api/aoi/', create_aoi, name='create_user_aoi'),
                  # path('api/aoi/', create_aoi, name='create_user_aoi'),

                  # Country
                  path(r'api/country', AdminBoundaryViewSet.as_view({"get": "get"}), name="country_list"),
                  path(r'api/country/<str:gid_0>', AdminBoundaryViewSet.as_view({"get": "get_regions"}),
                       name="country_regions"),
                  path(r'api/country/<str:gid_0>/<str:gid_1>',
                       AdminBoundaryViewSet.as_view({"get": "get_sub_regions"}),
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
                  path(r'api/vector-tiles/<int:z>/<int:x>/<int:y>', VectorTileView.as_view(), name="vector_tiles"),
                  path(r'api/station-tiles/<int:z>/<int:x>/<int:y>', StationsTileView.as_view(), name="station_tiles"),

                  # Data
                  path(r'api/raster-data/pixel', RasterDataPixelView.as_view(), name="raster_data_pixel"),
                  path(r'api/raster-data/pixel/timeseries', RasterDataPixelTimeseriesView.as_view(),
                       name="raster_data_pixel_timeseries"),

                  path(r'api/raster-data/geostore', RasterDataGeostoreView.as_view(), name="raster_data_geostore"),
                  path(r'api/raster-data/geostore/timeseries', RasterDataGeostoreTimeseriesView.as_view(),
                       name="raster_data_geostore_timeseries"),

                  # FeatureServ
                  path(r'api/feature-serv/<str:table_name>.geojson', GeoJSONPgTableView.as_view(),
                       name="feature_serv"),

                  # Tiles GL
                  path(r'api/tile-gl/tile/<str:source_slug>/<int:z>/<int:x>/<int:y>.pbf', tile_gl, name="tile_gl"),
                  path(r'api/tile-gl/tile-json/<str:source_slug>.json', tile_json_gl, name="tile_json_gl"),
                  path(r'api/tile-gl/style/<str:source_slug>.json', style_json_gl, name="style_json_gl"),

                  # Additional, standalone URLs from django-large-image
                  path('', include('django_large_image.urls')),
                  path('', include('adminboundarymanager.urls')),
              ] + router.urls
