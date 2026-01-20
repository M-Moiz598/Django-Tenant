from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from .models import Company, Domain
from .serializers import (
    CompanySerializer, DomainSerializer, CompanyRegistrationSerializer
)


class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing companies (public schema only).
    Only superusers can access this.
    """
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        """Filter companies based on permissions"""
        if self.request.user.is_superuser:
            return Company.objects.all()
        return Company.objects.none()


class DomainViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing domains (public schema only).
    Only superusers can access this.
    """
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    permission_classes = [IsAdminUser]


@api_view(['POST'])
@permission_classes([AllowAny])
def register_company(request):
    """
    Public endpoint to register a new company.
    Creates company, domain, and admin user.
    """
    serializer = CompanyRegistrationSerializer(data=request.data)

    if serializer.is_valid():
        result = serializer.save()

        return Response({
            'message': 'Company registered successfully',
            'company': {
                'name': result['company'].name,
                'schema_name': result['company'].schema_name,
            },
            'domain': result['domain'].domain,
            'admin_username': result['admin_user'].username,
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Simple health check endpoint"""
    return Response({
        'status': 'healthy',
        'service': 'Multi-Tenant SaaS Backend'
    })