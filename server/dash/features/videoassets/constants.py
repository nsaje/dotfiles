from utils import constant_base


class VideoAssetStatus(constant_base.ConstantBase):
    NOT_UPLOADED = 0
    PROCESSING = 1
    READY_FOR_USE = 2
    PROCESSING_ERROR = 3

    _VALUES = {
        NOT_UPLOADED: "Video is not uploaded yet",
        PROCESSING: "Video is processing",
        READY_FOR_USE: "Video is ready for use in creating ads",
        PROCESSING_ERROR: "An error has occurred while processing the video",
    }


class VideoAssetType(constant_base.ConstantBase):
    DIRECT_UPLOAD = 1
    VAST_UPLOAD = 2
    VAST_URL = 3

    _VALUES = {
        DIRECT_UPLOAD: 'DIRECT_UPLOAD',
        VAST_UPLOAD: 'VAST_UPLOAD',
        VAST_URL: 'VAST_URL',
    }
