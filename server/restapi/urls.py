import core.features.videoassets.urls
import dash.features.bluekai.urls
import restapi.account.urls
import restapi.accountcredit.urls
import restapi.accountcreditrefund.urls
import restapi.adgroup.urls
import restapi.adgroupsource.urls
import restapi.adgroupsourcesrtb.urls
import restapi.adgroupsourcestats.urls
import restapi.adgroupstats.urls
import restapi.bcm.urls
import restapi.campaign.urls
import restapi.campaignbudget.urls
import restapi.campaigngoal.urls
import restapi.campaignlauncher.urls
import restapi.campaignstats.urls
import restapi.contentad.urls
import restapi.geolocation.urls
import restapi.inventory_planning.urls
import restapi.publisherbidmodifiers.urls
import restapi.publishergroup.urls
import restapi.publishergroupentry.urls
import restapi.publishers.urls
import restapi.report.urls
from dash.features import cloneadgroup
from dash.features.bulkactions import clonecontent

urlpatterns = []
urlpatterns += restapi.bcm.urls.urlpatterns
urlpatterns += restapi.account.urls.urlpatterns
urlpatterns += restapi.accountcredit.urls.urlpatterns
urlpatterns += restapi.accountcreditrefund.urls.urlpatterns
urlpatterns += restapi.campaign.urls.urlpatterns
urlpatterns += restapi.campaignstats.urls.urlpatterns
urlpatterns += restapi.campaignlauncher.urls.urlpatterns
urlpatterns += restapi.campaigngoal.urls.urlpatterns
urlpatterns += restapi.campaignbudget.urls.urlpatterns
urlpatterns += restapi.adgroup.urls.urlpatterns
urlpatterns += restapi.adgroupstats.urls.urlpatterns
urlpatterns += restapi.adgroupsource.urls.urlpatterns
urlpatterns += restapi.adgroupsourcestats.urls.urlpatterns
urlpatterns += restapi.adgroupsourcesrtb.urls.urlpatterns
urlpatterns += restapi.contentad.urls.urlpatterns
urlpatterns += restapi.report.urls.urlpatterns
urlpatterns += restapi.geolocation.urls.urlpatterns
urlpatterns += restapi.publishers.urls.urlpatterns
urlpatterns += restapi.publishergroup.urls.urlpatterns
urlpatterns += restapi.publishergroupentry.urls.urlpatterns
urlpatterns += restapi.publisherbidmodifiers.urls.urlpatterns
urlpatterns += restapi.inventory_planning.urls.urlpatterns
urlpatterns += cloneadgroup.urls.urlpatterns
urlpatterns += clonecontent.urls.urlpatterns
urlpatterns += dash.features.bluekai.urls.urlpatterns
urlpatterns += core.features.videoassets.urls.urlpatterns
