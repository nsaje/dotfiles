import serviceapi.salesforce.outbrain.urls
import serviceapi.salesforce.zemanta.urls
import serviceapi.seat_info.urls
import serviceapi.video_upload_callback.urls

urlpatterns = []
urlpatterns += serviceapi.salesforce.zemanta.urls.urlpatterns
urlpatterns += serviceapi.salesforce.outbrain.urls.urlpatterns
urlpatterns += serviceapi.video_upload_callback.urls.urlpatterns
urlpatterns += serviceapi.seat_info.urls.urlpatterns
