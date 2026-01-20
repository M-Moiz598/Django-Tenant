from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'companies', views.CompanyViewSet, basename='company')
router.register(r'domains', views.DomainViewSet, basename='domain')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', views.register_company, name='register-company'),
    path('health/', views.health_check, name='health-check'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]