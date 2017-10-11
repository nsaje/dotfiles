from django.db import models


class GALinkedAccounts(models.Model):
    customer_ga_account_id = models.CharField(max_length=25, primary_key=True)
    zem_ga_account_email = models.CharField(max_length=254)
    has_read_and_analyze = models.BooleanField()
