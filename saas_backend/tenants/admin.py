from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Company, Domain


@admin.register(Company)
class CompanyAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'schema_name', 'subscription_plan', 'is_active', 'created_at']
    list_filter = ['subscription_plan', 'is_active', 'created_at']
    search_fields = ['name', 'schema_name', 'contact_email']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'schema_name', 'is_active')
        }),
        ('Subscription', {
            'fields': ('subscription_plan', 'subscription_start_date', 'subscription_end_date')
        }),
        ('Limits', {
            'fields': ('max_users', 'max_projects')
        }),
        ('Contact', {
            'fields': ('contact_email', 'contact_phone')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['domain', 'tenant__name']