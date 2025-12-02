from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import viewsets

router = DefaultRouter()
router.register("users", viewsets.UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
]
