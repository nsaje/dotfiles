from django.apps import apps
from django.db import models

from . import constants


class BlueKaiCategoryManager(models.Manager):
    def create(self, category_id, parent_category_id, name, description, reach, price, navigation_only):
        bluekai_category = apps.get_model("dash", "BlueKaiCategory")(
            category_id=category_id,
            parent_category_id=parent_category_id,
            name=name,
            description=description,
            reach=reach,
            price=price,
            navigation_only=navigation_only,
            status=constants.BlueKaiCategoryStatus.ACTIVE,
        )
        bluekai_category.save()
        return bluekai_category


class BlueKaiCategoryMixin(object):
    def mark_active(self):
        self.status = constants.BlueKaiCategoryStatus.ACTIVE
        self.save()

    def mark_inactive(self):
        self.status = constants.BlueKaiCategoryStatus.INACTIVE
        self.save()

    def update(self, name, description, reach, price, navigation_only):
        self.name = name
        self.description = description
        self.reach = reach
        self.price = price
        self.navigation_only = navigation_only
        self.save()
