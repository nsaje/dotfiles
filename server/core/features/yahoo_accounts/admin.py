from django.contrib import admin

from . import models


class YahooMigrationAdGroupHistoryAdmin(admin.ModelAdmin):
    model = models.YahooMigrationAdGroupHistory
    list_display = ('ad_group_id', 'source_campaign_key')
    search_fields = ('ad_group__id', )
    readonly_fields = ('ad_group', 'source_campaign_key')


class YahooMigrationContentAdHistoryAdmin(admin.ModelAdmin):
    model = models.YahooMigrationContentAdHistory
    list_display = ('content_ad_id', 'source_content_ad_id')
    search_fields = ('content_ad__id', )
    readonly_fields = ('content_ad', 'source_content_ad_id')


admin.site.register(models.YahooMigrationAdGroupHistory, YahooMigrationAdGroupHistoryAdmin)
admin.site.register(models.YahooMigrationContentAdHistory, YahooMigrationContentAdHistoryAdmin)
