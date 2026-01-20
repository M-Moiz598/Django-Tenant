from rest_framework import serializers
from .models import Company, Domain
from django.contrib.auth.models import User


class CompanySerializer(serializers.ModelSerializer):
    """Serializer for Company/Tenant"""

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'schema_name', 'subscription_plan',
            'subscription_start_date', 'subscription_end_date',
            'is_active', 'max_users', 'max_projects',
            'contact_email', 'contact_phone', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'schema_name']


class DomainSerializer(serializers.ModelSerializer):
    """Serializer for Domain"""

    class Meta:
        model = Domain
        fields = ['id', 'domain', 'is_primary', 'tenant']
        read_only_fields = ['id']


class CompanyRegistrationSerializer(serializers.Serializer):
    """Serializer for registering a new company with admin user"""

    company_name = serializers.CharField(max_length=255)
    schema_name = serializers.CharField(max_length=63)
    domain_url = serializers.CharField(max_length=255)

    admin_username = serializers.CharField(max_length=150)
    admin_email = serializers.EmailField()
    admin_password = serializers.CharField(write_only=True, min_length=8)

    subscription_plan = serializers.ChoiceField(
        choices=Company.SUBSCRIPTION_PLANS,
        default='free'
    )

    def validate_schema_name(self, value):
        """Ensure schema name is valid and unique"""
        if Company.objects.filter(schema_name=value).exists():
            raise serializers.ValidationError("This schema name is already taken.")

        # Schema name must be valid PostgreSQL identifier
        if not value.replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Schema name must contain only alphanumeric characters and underscores."
            )

        return value.lower()

    def validate_domain_url(self, value):
        """Ensure domain is unique"""
        if Domain.objects.filter(domain=value).exists():
            raise serializers.ValidationError("This domain is already registered.")
        return value.lower()

    def create(self, validated_data):
        """Create company, domain, and admin user"""
        from django.db import transaction
        from django.contrib.auth.models import User

        with transaction.atomic():
            # Create the company/tenant
            company = Company.objects.create(
                name=validated_data['company_name'],
                schema_name=validated_data['schema_name'],
                subscription_plan=validated_data['subscription_plan']
            )

            # Create the domain
            domain = Domain.objects.create(
                domain=validated_data['domain_url'],
                tenant=company,
                is_primary=True
            )

            # Switch to tenant schema to create admin user
            from django.db import connection
            connection.set_tenant(company)

            # Create admin user in tenant schema
            admin_user = User.objects.create_user(
                username=validated_data['admin_username'],
                email=validated_data['admin_email'],
                password=validated_data['admin_password'],
                is_staff=True,
                is_superuser=True
            )

            return {
                'company': company,
                'domain': domain,
                'admin_user': admin_user
            }