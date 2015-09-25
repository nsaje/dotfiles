import unittest
from zemauth.models import User
from utils.migrationtest import MigrationTest
from utils.test_decorators import skipIfNoMigrations

# based on https://github.com/plumdog/django_migration_testcase

#we will skip this migration test as it is long gone-by
#@skipIfNoMigrations
@unittest.skip
class ContentAdBatchMigrationTest(MigrationTest):

    # At present, we can only run migrations for one app at a time.
    app_name = 'dash'
    before = '0065_auto_20150828_1151'
    after = '0066_add_batch_fields_to_contentad'
 
    def test_migration(self):
        # Load some data. Don't directly import models. At this point,
        # the database is at self.before, and the models have fields
        # set accordingly. Can get models from other apps with
        # self.get_model_before('otherapp.OtherModel')

        AdGroup = self.get_model_before('AdGroup')
        Campaign = self.get_model_before('Campaign')
        Account = self.get_model_before('Account')
        ContentAd = self.get_model_before('ContentAd')
        UploadBatch = self.get_model_before('UploadBatch')

        user = User.objects.create_user('test@example.com')
        account = Account.objects.create(modified_by_id = user.id)
        campaign = Campaign.objects.create(modified_by_id = user.id, account_id = account.id)
        ad_group = AdGroup.objects.create(modified_by_id = user.id, campaign_id = campaign.id)
        batch = UploadBatch.objects.create(name='test', 
                                           display_url="abc.com",
                                           brand_name="Brand inc.",
                                           description="This desc!", 
                                           call_to_action="Act!",)
        content_ad1 = ContentAd.objects.create(
            url='test.com',
            title='test',
            ad_group_id=ad_group.id,
            batch_id=batch.id,

        )
        # Trigger the migration
        self.run_migration()

        # Now run some assertions based on what the data should now
        # look like. The database will now be at self.after. To run
        # queries via the models, reload the model.

        ContentAd = self.get_model_after('ContentAd')

        ca = ContentAd.objects.get(url='test.com')
        self.assertEqual(ca.display_url, "abc.com")
        self.assertEqual(ca.brand_name, "Brand inc.")
        self.assertEqual(ca.description ,"This desc!")
        self.assertEqual(ca.call_to_action, "Act!")
