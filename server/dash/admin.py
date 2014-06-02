from django.contrib import admin

import models


class AccountAdmin(admin.ModelAdmin):
    pass


class CampaignAdmin(admin.ModelAdmin):
    pass


class AdGroupAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.Account, AccountAdmin)
admin.site.register(models.Campaign, CampaignAdmin)
admin.site.register(models.AdGroup, AdGroupAdmin)
