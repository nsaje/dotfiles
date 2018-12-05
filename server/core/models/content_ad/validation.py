import dash.constants

from . import exceptions


class ContentAdValidatorMixin(object):
    def clean(self):
        self._validate_ad_type()

    def _validate_ad_type(self):
        if (
            self.ad_group.campaign.type
            in [
                dash.constants.CampaignType.CONTENT,
                dash.constants.CampaignType.CONVERSION,
                dash.constants.CampaignType.MOBILE,
            ]
            and self.type != dash.constants.AdType.CONTENT
            or self.ad_group.campaign.type == dash.constants.CampaignType.VIDEO
            and self.type != dash.constants.AdType.VIDEO
            or self.ad_group.campaign.type == dash.constants.CampaignType.DISPLAY
            and self.type not in [dash.constants.AdType.IMAGE, dash.constants.AdType.AD_TAG]
        ):
            raise exceptions.CampaignAdTypeMismatch("Creative type does not match the campaign type.")
