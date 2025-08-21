from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CityViewSet, DataCenterViewSet, HostViewSet,
    HostStatisticsViewSet, RequestLogViewSet
)

router = DefaultRouter()
router.register(r'cities', CityViewSet)
router.register(r'datacenters', DataCenterViewSet)
router.register(r'hosts', HostViewSet)
router.register(r'statistics', HostStatisticsViewSet)
router.register(r'logs', RequestLogViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
] 