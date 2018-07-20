class ProdopsMixin(object):
    def get_prodops_dict(self):
        d = {
            "source_id": self.source_id,
            "source__name": self.source.name,
            "submission_status": self.get_submission_status(),
            "source_ad_id": self.get_source_id(),
        }
        for k, v in list(self.content_ad.get_prodops_dict().items()):
            d["content_ad__" + k] = v
        return d
