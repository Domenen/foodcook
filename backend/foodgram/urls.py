from django.contrib import admin
from django.urls import include, path

from api.views import ShortLinkViewSet

urlpatterns = [
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls),
]
