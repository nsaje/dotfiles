import serviceapi.salesforce.urls
import serviceapi.video_upload_callback.urls

urlpatterns = []
urlpatterns += serviceapi.salesforce.urls.urlpatterns
urlpatterns += serviceapi.video_upload_callback.urls.urlpatterns
