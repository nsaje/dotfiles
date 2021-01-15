import restapi.account.urls
import restapi.adgroup.urls
import restapi.adgroupsource.urls
import restapi.adgroupsourcesrtb.urls
import restapi.adgroupsourcestats.urls
import restapi.adgroupstats.urls
import restapi.agency.urls
import restapi.audience.urls
import restapi.availablesources.urls
import restapi.bidmodifiers.internal.urls
import restapi.bidmodifiers.urls
import restapi.bluekai.urls
import restapi.booksclosed.urls
import restapi.bulkupload.urls
import restapi.campaign.urls
import restapi.campaignbudget.urls
import restapi.campaigngoal.urls
import restapi.campaignstats.urls
import restapi.contentad.urls
import restapi.conversion_pixel.urls
import restapi.creative_tags.urls
import restapi.creatives.urls
import restapi.credit.urls
import restapi.creditrefund.urls
import restapi.directdeal.urls
import restapi.geolocation.urls
import restapi.inventory_planning.urls
import restapi.publishergroup.urls
import restapi.publishergroupentry.urls
import restapi.publishers.urls
import restapi.realtimestats.urls
import restapi.report.urls
import restapi.rules.urls
import restapi.source.urls
import restapi.user.urls
import restapi.videoassets.urls

urlpatterns = []
urlpatterns += restapi.account.urls.urlpatterns
urlpatterns += restapi.credit.urls.urlpatterns
urlpatterns += restapi.creditrefund.urls.urlpatterns
urlpatterns += restapi.adgroup.urls.urlpatterns
urlpatterns += restapi.adgroupstats.urls.urlpatterns
urlpatterns += restapi.adgroupsource.urls.urlpatterns
urlpatterns += restapi.adgroupsourcestats.urls.urlpatterns
urlpatterns += restapi.adgroupsourcesrtb.urls.urlpatterns
urlpatterns += restapi.agency.urls.urlpatterns
urlpatterns += restapi.audience.urls.urlpatterns
urlpatterns += restapi.campaign.urls.urlpatterns
urlpatterns += restapi.campaignstats.urls.urlpatterns
urlpatterns += restapi.campaigngoal.urls.urlpatterns
urlpatterns += restapi.campaignbudget.urls.urlpatterns
urlpatterns += restapi.bidmodifiers.urls.urlpatterns
urlpatterns += restapi.bidmodifiers.internal.urls.urlpatterns
urlpatterns += restapi.contentad.urls.urlpatterns
urlpatterns += restapi.conversion_pixel.urls.urlpatterns
urlpatterns += restapi.directdeal.urls.urlpatterns
urlpatterns += restapi.inventory_planning.urls.urlpatterns
urlpatterns += restapi.geolocation.urls.urlpatterns
urlpatterns += restapi.report.urls.urlpatterns
urlpatterns += restapi.publishers.urls.urlpatterns
urlpatterns += restapi.publishergroup.urls.urlpatterns
urlpatterns += restapi.publishergroupentry.urls.urlpatterns
urlpatterns += restapi.rules.urls.urlpatterns
urlpatterns += restapi.source.urls.urlpatterns
urlpatterns += restapi.availablesources.urls.urlpatterns
urlpatterns += restapi.videoassets.urls.urlpatterns
urlpatterns += restapi.user.urls.urlpatterns
urlpatterns += restapi.bluekai.urls.urlpatterns
urlpatterns += restapi.booksclosed.urls.urlpatterns
urlpatterns += restapi.bulkupload.urls.urlpatterns
urlpatterns += restapi.realtimestats.urls.urlpatterns
urlpatterns += restapi.creatives.urls.urlpatterns
urlpatterns += restapi.creative_tags.urls.urlpatterns
