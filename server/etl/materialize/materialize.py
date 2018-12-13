from etl import helpers


class Materialize(object):

    TABLE_NAME = "missing"
    SOURCE_VIEW = None
    IS_TEMPORARY_TABLE = False
    IS_DERIVED_VIEW = False

    def __init__(self, job_id, date_from, date_to, account_id, spark_session=None):
        self.job_id = job_id
        self.date_from = date_from
        self.date_to = date_to
        self.account_id = account_id
        self.spark_session = spark_session

    def generate(self, **kwargs):
        raise NotImplementedError()

    def _add_account_id_param(self, params):
        if self.account_id:
            params["account_id"] = self.account_id

        return params

    def _add_ad_group_id_param(self, params):
        if self.account_id:
            params["ad_group_id"] = helpers.get_ad_group_ids_or_none(self.account_id)

        return params
