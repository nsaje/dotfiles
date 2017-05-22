from django.db import models

import constants


class BlueKaiCategory(models.Model):
    id = models.AutoField(primary_key=True)
    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')

    category_id = models.PositiveIntegerField(unique=True)
    parent_category_id = models.PositiveIntegerField()
    description = models.TextField()
    reach = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    navigation_only = models.BooleanField()
    status = models.PositiveSmallIntegerField(
        default=constants.BlueKaiCategoryStatus.INACTIVE,
        choices=constants.BlueKaiCategoryStatus.get_choices())
