from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Company(TenantMixin):
    """
    Organization/Company model for multi-tenancy.
    Each company gets its own schema in the database.
    """
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Subscription fields
    SUBSCRIPTION_PLANS = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]

    subscription_plan = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_PLANS,
        default='free'
    )
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Contact information
    contact_email = models.EmailField(null=True, blank=True)
    contact_phone = models.CharField(max_length=20, null=True, blank=True)

    # Usage limits based on subscription
    max_users = models.IntegerField(default=5)
    max_projects = models.IntegerField(default=3)

    auto_create_schema = True
    auto_drop_schema = False

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name


class Domain(DomainMixin):
    """
    Domain model to map domains/subdomains to tenants.
    Example: company1.yoursaas.com -> Company(schema_name='company1')
    """
    pass