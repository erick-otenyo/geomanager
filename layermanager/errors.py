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

class MissingTileError(Exception):
    pass


class MBTilesNotFoundError(Exception):
    pass


class MBTilesInvalid(Exception):
    pass


class MissingBoundaryField(Exception):
    pass


class NoMatchingBoundaryData(Exception):
    pass


class InvalidBoundaryGeomType(Exception):
    pass
