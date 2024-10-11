from django.contrib import admin
from django.urls import include, path

from api.views import redirect_to_recipe


urlpatterns = [
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls),
    path('s/<short_link>', redirect_to_recipe, name='redirect_full_url')
]
