import dash.constants


class ContentAdSourceMixin:
    def get_submission_status(self):
        if (
            self.submission_status != dash.constants.ContentAdSubmissionStatus.APPROVED
            and self.submission_status != dash.constants.ContentAdSubmissionStatus.REJECTED
        ):
            return dash.constants.ContentAdSubmissionStatus.PENDING
        return self.submission_status

    def get_source_id(self):
        if self.source.source_type and self.source.source_type.type in [
            dash.constants.SourceType.B1,
            dash.constants.SourceType.GRAVITY,
        ]:
            return self.content_ad_id
        else:
            return self.source_content_ad_id

    def __str__(self):
        return "{}(id={}, content_ad={}, source={}, state={}, source_state={}, submission_status={}, source_content_ad_id={})".format(
            self.__class__.__name__,
            self.id,
            self.content_ad,
            self.source,
            self.state,
            self.source_state,
            self.submission_status,
            self.source_content_ad_id,
        )
