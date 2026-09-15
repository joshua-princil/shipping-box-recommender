from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    # Send the bare site root to the browsable API root, so
    # http://127.0.0.1:8000/ lands somewhere useful instead of 404ing.
    path("", RedirectView.as_view(url="api/", permanent=False)),
    path("admin/", admin.site.urls),
    path("api/", include("boxes.urls")),
]
