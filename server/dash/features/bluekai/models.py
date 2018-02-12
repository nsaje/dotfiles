from django.db import models

from . import constants
from . import managers


class BlueKaiCategoryQuerySet(models.QuerySet):

    def active(self):
        return self.filter(status=constants.BlueKaiCategoryStatus.ACTIVE)


class BlueKaiCategory(models.Model, managers.BlueKaiCategoryMixin):
    id = models.AutoField(primary_key=True)
    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')

    category_id = models.PositiveIntegerField(unique=True)
    parent_category_id = models.PositiveIntegerField()
    name = models.TextField()
    description = models.TextField()
    reach = models.BigIntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    navigation_only = models.BooleanField()
    status = models.PositiveSmallIntegerField(
        default=constants.BlueKaiCategoryStatus.INACTIVE,
        choices=constants.BlueKaiCategoryStatus.get_choices())

    objects = managers.BlueKaiCategoryManager.from_queryset(BlueKaiCategoryQuerySet)()
