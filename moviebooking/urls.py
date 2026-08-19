from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("booking.urls")),  # Connects the landing page at root http://127.0.0.1:8000/
    path("api-auth/", include("rest_framework.urls")),
]