import dash.constants


class ConstantsConverter:
    _to_ad_type_map = {
        dash.constants.CreativeBatchType.NATIVE: dash.constants.AdType.CONTENT,
        dash.constants.CreativeBatchType.VIDEO: dash.constants.AdType.VIDEO,
        dash.constants.CreativeBatchType.DISPLAY: dash.constants.AdType.IMAGE,
    }

    _to_batch_type_map = {
        dash.constants.AdType.CONTENT: dash.constants.CreativeBatchType.NATIVE,
        dash.constants.AdType.VIDEO: dash.constants.CreativeBatchType.VIDEO,
        dash.constants.AdType.IMAGE: dash.constants.CreativeBatchType.DISPLAY,
        dash.constants.AdType.AD_TAG: dash.constants.CreativeBatchType.DISPLAY,
    }

    @classmethod
    def to_ad_type(cls, batch_type: dash.constants.CreativeBatchType) -> dash.constants.AdType:
        return cls._to_ad_type_map.get(batch_type, dash.constants.AdType.CONTENT)

    @classmethod
    def to_batch_type(cls, ad_type: dash.constants.AdType) -> dash.constants.CreativeBatchType:
        return cls._to_batch_type_map.get(ad_type, dash.constants.CreativeBatchType.NATIVE)
