class Error(Exception):

    def __init__(self, message):
        self.message = message

    @property
    def serialize(self):
        return {
            'message': self.message
        }


class InvalidFile(Error):
    pass


class RasterConvertError(Error):
    pass


class UnsupportedRasterFormat(Error):
    pass


class NoShpFound(Error):
    pass


class NoShxFound(Error):
    pass


class NoDbfFound(Error):
    pass


# Tile GL

class MissingTileError(Error):
    pass


class MBTilesNotFoundError(Error):
    pass


class MBTilesInvalid(Error):
    pass


class MissingBoundaryField(Error):
    pass


class NoMatchingBoundaryLayer(Error):
    pass


class NoMatchingBoundaryData(Error):
    pass


class InvalidBoundaryGeomType(Error):
    pass


class RasterFileNotFound(Error):
    pass


class GeostoreNotFound(Error):
    pass


class QueryParamRequired(Error):
    pass


class InvalidGeomType(Error):
    pass


class GeomValidationNotImplemented(Error):
    pass
