from django.contrib import admin
from django.urls import include, path
from django.conf import settings

urlpatterns = [
    path(r"api/", include("api.urls")),
]

if settings.ADMIN_ENABLED:
    urlpatterns += [path(r"admin/", admin.site.urls), ]
