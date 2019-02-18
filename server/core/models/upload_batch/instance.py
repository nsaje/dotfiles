import dash.constants
import utils.dates_helper
import utils.exc

from .. import content_ad_candidate


class UploadBatchInstanceMixin:
    def get_approved_content_ads(self):
        return self.contentad_set.all().order_by("pk")

    def save(self, *args, **kwargs):
        if self.pk is None:
            user = kwargs.pop("user", None)
            self.created_by = user
        super().save(*args, **kwargs)

    @classmethod
    def generate_cloned_name(cls, source_ad_group):
        return "Cloned from {} on {}".format(
            source_ad_group.get_name_with_id(), utils.dates_helper.format_date_mmddyyyy(utils.dates_helper.local_now())
        )

    def mark_save_done(self):
        self.status = dash.constants.UploadBatchStatus.DONE
        self.save()

    def set_ad_group(self, ad_group):
        if self.status == dash.constants.UploadBatchStatus.DONE:
            raise utils.exc.ForbiddenError("Cannot set an ad group on an already persisted batch")
        self.ad_group = ad_group
        candidates = content_ad_candidate.ContentAdCandidate.objects.filter(batch=self)
        candidates.update(ad_group=ad_group)
        self.save()
